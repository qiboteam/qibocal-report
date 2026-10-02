"""Self-contained notebook worker, also executed on remote hosts with ``python -c``."""

import getpass
import ipaddress
import json
import math
import os
import platform
import queue
import secrets
import select
import shlex
import signal
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from importlib import util
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


def free_port(host="127.0.0.1"):
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    with socket.socket(family) as listener:
        listener.bind((host, 0))
        return listener.getsockname()[1]


def usable_address(value):
    address = ipaddress.ip_address(value)
    return not (
        address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
    )


def node_addresses(runtime):
    result = runtime.command(["hostname", "-I"], capture=True)
    addresses = []
    for value in result.split():
        try:
            address = ipaddress.ip_address(value)
        except ValueError as error:
            raise WorkerError(
                f"hostname -I returned an invalid IP: {value!r}"
            ) from error
        if usable_address(address):
            addresses.append(str(address))
    if not addresses:
        raise WorkerError("hostname -I reported no usable node IP addresses")
    return list(dict.fromkeys(addresses))


def compute_address(access_addresses, compute_addresses):
    best = None
    longest = -1
    for local in map(ipaddress.ip_address, access_addresses):
        for remote in map(ipaddress.ip_address, compute_addresses):
            if local.version != remote.version:
                continue
            prefix = local.max_prefixlen - (int(local) ^ int(remote)).bit_length()
            if prefix > longest:
                best, longest = str(remote), prefix
    if best is None:
        raise WorkerError("Access and compute nodes have no common IP address family")
    return best


class Forwarder:
    """Relay access-node loopback to the selected compute interface."""

    def __init__(self, host, port):
        self.stop = threading.Event()
        stop = self.stop

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                try:
                    with socket.create_connection((host, port), timeout=5) as remote:
                        self.request.settimeout(5)
                        peers = {self.request: remote, remote: self.request}
                        readers = list(peers)
                        while readers and not stop.is_set():
                            readable, _, _ = select.select(readers, [], [], 0.2)
                            for source in readable:
                                data = source.recv(65536)
                                if data:
                                    peers[source].sendall(data)
                                else:
                                    readers.remove(source)
                                    peers[source].shutdown(socket.SHUT_WR)
                except OSError as error:
                    if not stop.is_set():
                        event(
                            "status",
                            message=f"Notebook forwarding connection failed: {error}",
                        )

        self.server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.1},
            daemon=True,
        )
        self.thread.start()

    def close(self):
        self.stop.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


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


def environment_install_command(python, packages, seeded):
    if seeded:
        return [python, "-m", "pip", "install", *packages]
    if util.find_spec("pip") is not None:
        return [sys.executable, "-m", "pip", "--python", python, "install", *packages]
    raise WorkerError(
        "Target environment has no pip and no external package installer is "
        "available. Bootstrap pip in the target environment (install the "
        "computing node's python3-venv package if ensurepip is unavailable), "
        "or provide pip >= 22.3 for the worker's Python."
    )


def ensure_environment(runtime, path, server=False, packages=()):
    python = path / "bin" / "python"
    if not path.exists() and not path.is_symlink():
        if server:
            packages = ["jupyterlab", "ipykernel"]
        seeded = util.find_spec("ensurepip") is not None
        if not seeded:
            packages = ["pip", *packages]
        if packages:
            install = environment_install_command(str(python), packages, seeded)
        event("status", message=f"Creating environment: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-m", "venv"]
        if not seeded:
            command.append("--without-pip")
        runtime.command([*command, str(path)])
        if packages:
            event(
                "status",
                message=f"Installing {'notebook' if server else 'kernel'} "
                f"dependencies: {', '.join(packages)}",
            )
            runtime.command(install)
    if not python.is_file() or not os.access(python, os.X_OK):
        raise WorkerError(
            f"Environment {path} has no executable bin/python; repair it manually"
        )
    return str(python)


def server_sites(runtime, python):
    packages = ["jupyterlab", "ipykernel"]
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
        install = environment_install_command(
            python, packages, seeded=util.find_spec("ensurepip") is not None
        )
        raise WorkerError(
            f"Notebook dependencies unavailable. Repair the server environment with: "
            f"{shlex.join(install)}"
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


def wait_http(runtime, port, token, path, marimo, processes, host="127.0.0.1"):
    opener = build_opener(ProxyHandler({}))
    query = urlencode({"access_token" if marimo else "token": token})
    authority = f"[{host}]" if ":" in host else host
    url = f"http://{authority}:{port}{path}?{query}"
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


def announce(port, token, path, host=None):
    data = {
        "host": host or socket.gethostname(),
        "port": port,
        "token": token,
        "path": path,
    }
    print(
        READY_PREFIX + json.dumps(data),
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
                and usable_address(data["host"])
                and type(data.get("port")) is int
                and 0 < data["port"] < 65536
                and isinstance(data.get("token"), str)
                and bool(data["token"])
                and data.get("path") in {"/", "/lab"}
            )
        except (ValueError, TypeError):
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
    forwarder = None
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
        listen_host = "127.0.0.1"
        if scheduled:
            extra = slurm_arguments(options.get("slurm"))
            source = globals().get("WORKER_SOURCE")
            if not source:
                raise WorkerError("SLURM execution requires embedded WORKER_SOURCE")
            access_addresses = node_addresses(runtime)
            script = "WORKER_SOURCE = " + repr(source) + "\n" + source
            nested = dict(
                options,
                queue=None,
                slurm=None,
                workdir=str(Path.cwd()),
                _node_role="compute",
                _access_addresses=access_addresses,
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
            event(
                "status",
                message=f"Forwarding access-node loopback to {data['host']}.",
            )
            forwarder = Forwarder(data["host"], data["port"])
            port = forwarder.port
            token, path = data["token"], data["path"]
            processes = [worker]

            def drain():
                for line in iter(messages.get, None):
                    print(line, end="", file=sys.stderr, flush=True)

            thread = threading.Thread(target=drain, daemon=True)
            runtime.threads.append(thread)
            thread.start()
        else:
            if "_access_addresses" in options:
                listen_host = compute_address(
                    options["_access_addresses"], node_addresses(runtime)
                )
                event(
                    "status",
                    message=f"Selected compute interface: {listen_host}. "
                    "The notebook is token-protected on this interface.",
                )
            target_name = options.get("venv", "qibocal")
            target_path = environment_path(target_name)
            server_path = cache_home() / "qibocal" / "envs" / "jupyter"
            if not marimo:
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
                f"Kernel environment: {target_path}"
                + ("" if marimo else f"\nServer environment: {server_path}"),
            )
            target = ensure_environment(
                runtime,
                target_path,
                packages=("qibocal",) if target_name == "qibocal" else (),
            )
            if marimo:
                has_pip = json.loads(
                    runtime.command(
                        [
                            target,
                            "-c",
                            (
                                "import json, importlib.util; "
                                "print(json.dumps(importlib.util.find_spec('pip') "
                                "is not None))"
                            ),
                        ],
                        capture=True,
                    )
                )
                event("status", message=f"Installing marimo in: {target_path}")
                runtime.command(
                    environment_install_command(target, ["marimo"], seeded=has_pip)
                )
            else:
                server = ensure_environment(runtime, server_path, server=True)
                sites = server_sites(runtime, server)
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
            port, token = free_port(listen_host), secrets.token_urlsafe(32)
            env = os.environ.copy()
            if marimo:
                path = "/"
                command = [
                    target,
                    "-m",
                    "marimo",
                    "edit",
                    "--host",
                    listen_host,
                    "--port",
                    str(port),
                    "--headless",
                    "--token",
                    "--token-password",
                    token,
                ]
            else:
                target_pythonpath = os.pathsep.join(
                    [*target_sites, *filter(None, [env.get("PYTHONPATH")]), *sites]
                )
                path = "/lab"
                runtime_directory = os.environ.get("XDG_RUNTIME_DIR") or None
                if runtime_directory and not Path(runtime_directory).is_dir():
                    event(
                        "status",
                        message=f"Runtime directory {runtime_directory} is missing; "
                        "using the system temporary directory "
                        "for kernel specifications.",
                    )
                    runtime_directory = None
                kernel_directory = tempfile.TemporaryDirectory(
                    prefix="qibocal-kernels-",
                    dir=runtime_directory,
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
                    f"--ServerApp.ip={listen_host}",
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
        wait_http(runtime, port, token, path, marimo, processes, host=listen_host)
        runtime.check()
        if scheduled or listen_host == "127.0.0.1":
            announce(port, token, path)
        else:
            announce(port, token, path, listen_host)
        while not runtime.stop.wait(0.1):
            if any(process.poll() is not None for process in processes):
                raise WorkerError("Notebook server or forwarding process exited")
    except Stopped:
        pass
    finally:
        if forwarder is not None:
            forwarder.close()
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
