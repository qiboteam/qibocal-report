"""Self-contained notebook worker, also executed on remote hosts with ``python -c``."""

import getpass
import json
import math
import os
import platform
import queue
import secrets
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, build_opener

READY_PREFIX = "QIBOCAL_NOTEBOOK_READY "
EVENT_PREFIX = "QIBOCAL_NOTEBOOK_EVENT "


def event(kind, **details):
    sys.stderr.write(EVENT_PREFIX + json.dumps({"kind": kind, **details}) + "\n")
    sys.stderr.flush()


def log_node(role):
    identity = {
        "hostname": socket.gethostname(),
        "fqdn": socket.getfqdn(),
        "user": getpass.getuser(),
        "system": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "python": sys.executable,
        "python_version": platform.python_version(),
        "pid": os.getpid(),
        "cwd": str(Path.cwd()),
    }
    slurm = {
        name: os.environ[name]
        for name in (
            "SLURM_CLUSTER_NAME",
            "SLURM_JOB_ID",
            "SLURM_JOB_NAME",
            "SLURM_JOB_PARTITION",
            "SLURM_JOB_NODELIST",
            "SLURM_STEP_ID",
            "SLURM_STEP_NODELIST",
            "SLURM_NODEID",
            "SLURM_PROCID",
            "SLURM_CPUS_ON_NODE",
            "SLURM_CPUS_PER_TASK",
            "SLURM_MEM_PER_NODE",
            "SLURM_MEM_PER_CPU",
            "SLURM_JOB_GPUS",
            "SLURM_STEP_GPUS",
            "CUDA_VISIBLE_DEVICES",
        )
        if name in os.environ
    }
    if slurm:
        identity["slurm"] = slurm
    event("node", role=role, identity=identity)


class WorkerError(RuntimeError):
    """An actionable startup or child-process failure."""


class Stopped(Exception):
    """The controlling process requested shutdown."""


def slurm_arguments(value):
    """Accept scheduler options, never an alternate executable or IO redirection."""
    arguments = shlex.split(value or "")
    forbidden = {
        "--input",
        "--output",
        "--error",
        "--unbuffered",
        "--pty",
        "--label",
        "--multi-prog",
        "--wrap",
        "--prolog",
        "--epilog",
        "--task-prolog",
        "--task-epilog",
        "--chdir",
        "--help",
        "--version",
    }
    valued = {
        "--partition",
        "--account",
        "--time",
        "--mem",
        "--mem-per-cpu",
        "--cpus-per-task",
        "--nodes",
        "--ntasks",
        "--ntasks-per-node",
        "--nodelist",
        "--exclude",
        "--constraint",
        "--gres",
        "--gpus",
        "--gpus-per-node",
        "--gpus-per-task",
        "--qos",
        "--reservation",
        "--job-name",
        "--export",
        "--hint",
        "--distribution",
        "--cpu-bind",
        "--dependency",
        "--licenses",
        "--nice",
        "--begin",
        "-p",
        "-A",
        "-t",
        "-c",
        "-N",
        "-n",
        "-w",
        "-x",
        "-C",
        "-J",
    }
    flags = {"--exclusive", "--overcommit", "--oversubscribe", "--verbose", "-v"}
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        name, separator, option_value = argument.partition("=")
        if name in forbidden or argument.startswith(("-i", "-o", "-e", "-u", "-l")):
            raise WorkerError(
                f"SLURM option {argument!r} can override worker launch or IO"
            )
        if name in valued:
            if not separator:
                index += 1
                if index >= len(arguments) or arguments[index].startswith("-"):
                    raise WorkerError(f"SLURM option {name!r} requires a value")
                option_value = arguments[index]
            if name in {"--nodes", "-N"} and option_value != "1":
                raise WorkerError("Notebook SLURM jobs must use exactly one node")
            if name in {"--ntasks", "--ntasks-per-node", "-n"} and option_value != "1":
                raise WorkerError("Notebook SLURM jobs must run exactly one task")
        elif argument not in flags:
            raise WorkerError(f"Unsupported SLURM option or command: {argument!r}")
        index += 1
    return arguments


def environment_path(value):
    expanded = Path(value).expanduser()
    if value.startswith(("/", "./", "../", "~")):
        return expanded.resolve()
    if not value or "/" in value or value in {".", ".."}:
        raise WorkerError(
            "Use a simple environment name or an explicit environment path"
        )
    return cache_home() / "qibocal" / "envs" / value


def cache_home():
    return Path(os.environ.get("XDG_CACHE_HOME") or "~/.cache").expanduser().absolute()


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def stop_process(process):
    if process.stdin is not None:
        try:
            process.stdin.close()
        except OSError:
            pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    # The leader may exit while notebook kernels remain in its process group.
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.05)


class Runtime:
    def __init__(self, timeout):
        self.stop = threading.Event()
        self.deadline = time.monotonic() + timeout
        self.processes = []
        self.threads = []

    def check(self):
        if self.stop.is_set():
            raise Stopped()
        if time.monotonic() >= self.deadline:
            raise WorkerError("Timed out starting notebook")

    def spawn(self, command, capture=False, env=None):
        self.check()
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            start_new_session=True,
            env=env,
        )
        self.processes.append(process)
        messages = queue.Queue()

        def read(stream, collect):
            try:
                for line in stream:
                    if collect:
                        messages.put(line)
                    else:
                        print(line, end="", file=sys.stderr, flush=True)
            finally:
                stream.close()
                if collect:
                    messages.put(None)

        for stream, collect in ((process.stdout, capture), (process.stderr, False)):
            thread = threading.Thread(target=read, args=(stream, collect), daemon=True)
            self.threads.append(thread)
            thread.start()
        return process, messages

    def command(self, command, capture=False):
        process, messages = self.spawn(command, capture=capture)
        lines = []
        ended = not capture
        while process.poll() is None or not ended:
            self.check()
            if capture:
                try:
                    line = messages.get(timeout=0.1)
                except queue.Empty:
                    continue
                if line is None:
                    ended = True
                else:
                    lines.append(line)
            else:
                self.stop.wait(0.1)
        if process.returncode:
            raise WorkerError(
                f"Command failed ({process.returncode}): {shlex.join(command)}"
            )
        return "".join(lines)

    def close(self):
        for process in reversed(self.processes):
            stop_process(process)
        for thread in self.threads:
            thread.join(timeout=1)


def ensure_environment(runtime, path, server=False, marimo=False):
    python = path / "bin" / "python"
    if not path.exists() and not path.is_symlink():
        event("status", message=f"Creating environment: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-m", "venv"]
        if not server:
            command.append("--without-pip")
        runtime.command([*command, str(path)])
        if server:
            packages = ["marimo"] if marimo else ["jupyterlab", "ipykernel"]
            event(
                "status",
                message=f"Installing notebook dependencies: {', '.join(packages)}",
            )
            runtime.command([str(python), "-m", "pip", "install", *packages])
    if not python.is_file() or not os.access(python, os.X_OK):
        raise WorkerError(
            f"Environment {path} has no executable bin/python; repair it manually"
        )
    return str(python)


def server_sites(runtime, python, marimo):
    packages = ["marimo"] if marimo else ["jupyterlab", "ipykernel"]
    try:
        result = runtime.command(
            [
                python,
                "-c",
                "import json, sysconfig; "
                + "; ".join(f"import {name}" for name in packages)
                + "; print(json.dumps(list(dict.fromkeys("
                "[sysconfig.get_path('purelib'), sysconfig.get_path('platlib')]))))",
            ],
            capture=True,
        )
        sites = json.loads(result)
    except (WorkerError, json.JSONDecodeError) as error:
        runtime.check()
        raise WorkerError(
            f"Notebook dependencies unavailable. Repair the server environment with: "
            f"{shlex.join([python, '-m', 'pip', 'install', *packages])}"
        ) from error
    return sites


def bootstrap(sites, module):
    # Appending preserves the target environment's packages ahead of server fallback.
    return (
        f"import sys, runpy; "
        f"sys.path[:] = [p for p in sys.path if p not in {sites!r}]; "
        f"sys.path.extend({sites!r}); "
        f"runpy.run_module({module!r}, run_name='__main__')"
    )


def wait_http(runtime, port, token, path, marimo, processes):
    opener = build_opener(ProxyHandler({}))
    query = urlencode({"access_token" if marimo else "token": token})
    url = f"http://127.0.0.1:{port}{path}?{query}"
    while True:
        runtime.check()
        if any(process.poll() is not None for process in processes):
            raise WorkerError(
                "Notebook server or forwarding process exited during startup"
            )
        try:
            with opener.open(
                url, timeout=min(1, max(0.01, runtime.deadline - time.monotonic()))
            ) as response:
                if response.status == 200:
                    return
        except (URLError, OSError):
            pass
        runtime.stop.wait(0.1)


def announce(port, token, path):
    print(
        READY_PREFIX
        + json.dumps(
            {"host": socket.gethostname(), "port": port, "token": token, "path": path}
        ),
        flush=True,
    )


def wait_nested(runtime, process, messages):
    while True:
        runtime.check()
        try:
            line = messages.get(timeout=0.1)
        except queue.Empty:
            if process.poll() is not None:
                raise WorkerError("SLURM worker exited before readiness")
            continue
        if line is None:
            raise WorkerError("SLURM worker exited before readiness")
        if not line.startswith(READY_PREFIX):
            print(line, end="", file=sys.stderr, flush=True)
            continue
        try:
            data = json.loads(line[len(READY_PREFIX) :])
            valid = (
                isinstance(data, dict)
                and isinstance(data.get("host"), str)
                and bool(data["host"])
                and not data["host"].startswith("-")
                and all(
                    character.isalnum() or character in ".-_"
                    for character in data["host"]
                )
                and type(data.get("port")) is int
                and 0 < data["port"] < 65536
                and isinstance(data.get("token"), str)
                and bool(data["token"])
                and data.get("path") in {"/", "/lab"}
            )
        except (json.JSONDecodeError, TypeError):
            valid = False
        if not valid:
            raise WorkerError("Invalid nested notebook readiness response")
        return data


def monitor_stdin(stop):
    def read():
        try:
            # Avoid holding a buffered-stdin lock at interpreter shutdown on SIGTERM.
            while os.read(sys.stdin.fileno(), 1024):
                pass
        except (OSError, ValueError):
            pass
        stop.set()

    threading.Thread(target=read, daemon=True).start()


def run(options):
    timeout = float(options.get("timeout", 300))
    if not math.isfinite(timeout) or timeout <= 0:
        raise WorkerError("Notebook timeout must be finite and positive")
    runtime = Runtime(timeout)
    old_handlers = {}
    kernel_directory = None
    try:
        scheduled = options.get("queue") is not None or options.get("slurm") is not None
        log_node(
            options.get("_node_role", "access" if scheduled else "access and compute")
        )
        for sig in (signal.SIGTERM, signal.SIGINT):
            old_handlers[sig] = signal.signal(sig, lambda *_: runtime.stop.set())
        monitor_stdin(runtime.stop)
        if options.get("workdir"):
            os.chdir(Path(options["workdir"]).expanduser())
        marimo = options.get("marimo", False)
        if scheduled:
            extra = slurm_arguments(options.get("slurm"))
            source = globals().get("WORKER_SOURCE")
            if not source:
                raise WorkerError("SLURM execution requires embedded WORKER_SOURCE")
            script = "WORKER_SOURCE = " + repr(source) + "\n" + source
            nested = dict(
                options,
                queue=None,
                slurm=None,
                workdir=str(Path.cwd()),
                _node_role="compute",
            )
            command = ["srun", "--unbuffered"]
            if options.get("queue"):
                command += ["--partition", options["queue"]]
            command += extra + [
                "--nodes=1",
                "--ntasks=1",
                "--ntasks-per-node=1",
                "python3",
                "-u",
                "-c",
                script,
                json.dumps(nested),
            ]
            event(
                "status",
                message="Submitting SLURM job"
                + (f" on partition {options['queue']}" if options.get("queue") else "")
                + (f" ({shlex.join(extra)})" if extra else "")
                + "; waiting for a compute node.",
            )
            worker, messages = runtime.spawn(command, capture=True)
            data = wait_nested(runtime, worker, messages)
            port = free_port()
            event("status", message=f"Opening compute-node tunnel to {data['host']}.")
            tunnel, _ = runtime.spawn(
                [
                    "ssh",
                    "-N",
                    "-T",
                    "-o",
                    "ExitOnForwardFailure=yes",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ServerAliveInterval=30",
                    "-o",
                    "ServerAliveCountMax=3",
                    "-L",
                    f"127.0.0.1:{port}:127.0.0.1:{data['port']}",
                    data["host"],
                ]
            )
            token, path = data["token"], data["path"]
            processes = [worker, tunnel]

            def drain():
                for line in iter(messages.get, None):
                    print(line, end="", file=sys.stderr, flush=True)

            thread = threading.Thread(target=drain, daemon=True)
            runtime.threads.append(thread)
            thread.start()
        else:
            target_path = environment_path(options.get("venv", "qibocal"))
            server_path = (
                cache_home()
                / "qibocal"
                / "envs"
                / ("notebook-marimo" if marimo else "notebook-jupyter")
            )
            resolved_server = server_path.resolve()
            resolved_target = target_path.resolve()
            if (
                resolved_server == resolved_target
                or resolved_server in resolved_target.parents
                or resolved_target in resolved_server.parents
            ):
                raise WorkerError(
                    "The target and notebook server environments must be separate"
                )
            event(
                "status",
                message=f"Preparing notebook in {Path.cwd()}\n"
                f"Kernel environment: {target_path}\n"
                f"Server environment: {server_path}",
            )
            target = ensure_environment(runtime, target_path)
            server = ensure_environment(
                runtime, server_path, server=True, marimo=marimo
            )
            sites = server_sites(runtime, server, marimo)
            target_sites = json.loads(
                runtime.command(
                    [
                        target,
                        "-c",
                        (
                            "import json, sysconfig; "
                            "print(json.dumps(list(dict.fromkeys("
                            "[sysconfig.get_path('purelib'), "
                            "sysconfig.get_path('platlib')]))))"
                        ),
                    ],
                    capture=True,
                )
            )
            port, token = free_port(), secrets.token_urlsafe(32)
            env = os.environ.copy()
            target_pythonpath = os.pathsep.join(
                [*target_sites, *filter(None, [env.get("PYTHONPATH")]), *sites]
            )
            if marimo:
                path = "/"
                env["PYTHONPATH"] = target_pythonpath
                command = [
                    target,
                    "-c",
                    bootstrap(sites, "marimo"),
                    "edit",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--headless",
                    "--token",
                    "--token-password",
                    token,
                ]
            else:
                path = "/lab"
                kernel_directory = tempfile.TemporaryDirectory(
                    prefix="qibocal-kernels-",
                    dir=os.environ.get("XDG_RUNTIME_DIR") or None,
                )
                kernel_root = Path(kernel_directory.name)
                kernel = kernel_root / "kernels" / "qibocal"
                kernel.mkdir(parents=True)
                (kernel / "kernel.json").write_text(
                    json.dumps(
                        {
                            "argv": [
                                target,
                                "-c",
                                bootstrap(sites, "ipykernel_launcher"),
                                "-f",
                                "{connection_file}",
                            ],
                            "display_name": "Qibocal",
                            "language": "python",
                            "env": {"PYTHONPATH": target_pythonpath},
                        }
                    ),
                    encoding="utf-8",
                )
                env["JUPYTER_PATH"] = os.pathsep.join(
                    filter(None, [str(kernel_root), env.get("JUPYTER_PATH")])
                )
                command = [
                    server,
                    "-m",
                    "jupyterlab",
                    "--no-browser",
                    "--ServerApp.ip=127.0.0.1",
                    f"--ServerApp.port={port}",
                    "--ServerApp.port_retries=0",
                    f"--IdentityProvider.token={token}",
                    "--MappingKernelManager.default_kernel_name=qibocal",
                ]
            event(
                "status",
                message=(
                    f"Starting {'Marimo' if marimo else 'JupyterLab'} on port {port}."
                ),
            )
            process, _ = runtime.spawn(command, env=env)
            processes = [process]
        wait_http(runtime, port, token, path, marimo, processes)
        runtime.check()
        announce(port, token, path)
        while not runtime.stop.wait(0.1):
            if any(process.poll() is not None for process in processes):
                raise WorkerError("Notebook server or forwarding process exited")
    except Stopped:
        pass
    finally:
        runtime.close()
        if kernel_directory is not None:
            kernel_directory.cleanup()
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)


def main():
    try:
        options = json.loads(sys.argv[1])
        if not isinstance(options, dict):
            raise WorkerError("Notebook options must be a JSON object")
        run(options)
    except (WorkerError, OSError, ValueError, IndexError) as error:
        print(f"Notebook worker: {error}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
