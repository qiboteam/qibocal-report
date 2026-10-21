"""Self-contained notebook worker, also executed on remote hosts with ``python -c``."""

import getpass
import hashlib
import ipaddress
import json
import math
import os
import platform
import queue
import re
import secrets
import select
import shlex
import shutil
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


def route_source(destination):
    """The address this host would send from to reach `destination`, or None.

    Connecting a datagram socket sends nothing and asks the kernel's routing
    table which interface serves that destination: the one the access node
    can reach back, when any can.
    """
    try:
        target = ipaddress.ip_address(destination)
        family = socket.AF_INET6 if target.version == 6 else socket.AF_INET
        with socket.socket(family, socket.SOCK_DGRAM) as probe:
            probe.connect((destination, 9))
            return probe.getsockname()[0]
    except (OSError, ValueError):
        return None


def compute_address(
    access_addresses, compute_addresses, subnet=None, source_for=None
):
    """The compute-node address the access node forwards to.

    Within `subnet` when one is given. An address the two nodes share — a
    bridge every host has at the same address, a VPN's — is a per-host
    interface, not a network between them, and is left out while anything
    else remains. The interface this node routes through to reach the
    access node (`source_for`, `route_source` in practice) comes first; the
    longest common prefix decides otherwise.
    """
    if subnet is not None:
        network = ipaddress.ip_network(subnet)
        compute_addresses = [
            value
            for value in compute_addresses
            if ipaddress.ip_address(value) in network
        ]
        if not compute_addresses:
            raise WorkerError(
                f"No usable computing-node IP addresses match subnet {subnet}"
            )
    shared = set(access_addresses)
    distinct = [value for value in compute_addresses if value not in shared]
    if distinct:
        compute_addresses = distinct
    if source_for is not None:
        for destination in access_addresses:
            source = source_for(destination)
            if source in compute_addresses:
                return source
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


def probe_reachable(host, port, deadline, stop):
    """Whether something answers at host:port before `deadline`; the error otherwise.

    A refused connection a moment after the server reported ready may be
    the server still binding, so refusals are retried until the deadline.
    """
    error = None
    while time.monotonic() < deadline and not stop.is_set():
        try:
            with socket.create_connection((host, port), timeout=3):
                return None
        except OSError as failure:
            error = failure
        stop.wait(0.3)
    return error or OSError("timed out")


class Forwarder:
    """Relay access-node loopback to the selected compute interface."""

    def __init__(self, host, port):
        self.stop = threading.Event()
        stop = self.stop
        # One report per kind of failure: a browser retries, and every retry
        # would otherwise say the same thing again.
        reported = set()

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
                    if not stop.is_set() and str(error) not in reported:
                        reported.add(str(error))
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


# --- uv: environments made and filled far faster than with venv and pip -------
# uv is used wherever it can be: the one on the PATH, or one the worker
# installs once for itself, under the cache, with venv and pip. Without
# either — no index, no pip anywhere — the worker falls back on venv and
# pip, as before.
_UV = {}


def tools_path():
    return cache_home() / "qibocal" / "tools" / "uv"


def _bin(path, name):
    return path / ("Scripts" if os.name == "nt" else "bin") / (f"{name}.exe" if os.name == "nt" else name)


def find_uv(runtime):
    """The uv to use, installing it once when there is none; None to fall back on pip."""
    if "path" in _UV:
        return _UV["path"]
    if os.environ.get("QIBOCAL_NO_UV"):
        # Asked for venv and pip: nothing found, nothing installed.
        _UV["path"] = None
        return None
    found = shutil.which("uv")
    managed = _bin(tools_path(), "uv")
    if found is None and managed.is_file():
        found = str(managed)
    if found is None:
        try:
            event("status", message=f"Installing uv, once, in: {tools_path()}")
            seeded = util.find_spec("ensurepip") is not None
            tools_path().parent.mkdir(parents=True, exist_ok=True)
            runtime.command(
                [sys.executable, "-m", "venv", *([] if seeded else ["--without-pip"]), str(tools_path())]
            )
            runtime.command(environment_install_command(str(_bin(tools_path(), "python")), ["uv"], seeded))
            if managed.is_file():
                found = str(managed)
        except WorkerError as error:
            event("status", message=f"uv is unavailable ({error}); using venv and pip.")
    _UV["path"] = found
    return found


def install_command(runtime, python, packages, *, upgrade=False, reinstall=False, no_deps=False):
    """Install `packages` — names, specifications, `-r FILE` — into the environment of `python`.

    With uv when there is one, else with pip, in or for the environment.
    """
    flags = (["--upgrade"] if upgrade else []) + (["--no-deps"] if no_deps else [])
    uv = find_uv(runtime)
    if uv:
        return [uv, "pip", "install", "--python", str(python), *flags,
                *(["--reinstall"] if reinstall else []), *packages]
    return environment_install_command(
        str(python),
        [*flags, *(["--force-reinstall"] if reinstall else []), *packages],
        seeded=has_pip(runtime, python),
    )


def create_environment(runtime, path, packages=()):
    """Make an environment, with pip in it, and install `packages` in one go."""
    python = path / "bin" / "python"
    event("status", message=f"Creating environment: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    uv = find_uv(runtime)
    if uv:
        # Seeded: whoever uses the environment can still pip install in it.
        runtime.command([uv, "venv", "--seed", "--python", sys.executable, str(path)])
        if packages:
            runtime.command([uv, "pip", "install", "--python", str(python), *packages])
        return python
    seeded = util.find_spec("ensurepip") is not None
    if not seeded:
        packages = ["pip", *packages]
    if packages:
        install = environment_install_command(str(python), list(packages), seeded)
    command = [sys.executable, "-m", "venv"]
    if not seeded:
        command.append("--without-pip")
    runtime.command([*command, str(path)])
    if packages:
        runtime.command(install)
    return python


def ensure_environment(runtime, path, server=False, packages=()):
    python = path / "bin" / "python"
    if not path.exists() and not path.is_symlink():
        if server:
            packages = ["jupyterlab", "ipykernel"]
        if packages:
            event(
                "status",
                message=f"Installing {'notebook' if server else 'kernel'} "
                f"dependencies: {', '.join(packages)}",
            )
        create_environment(runtime, path, list(packages))
    if not python.is_file() or not os.access(python, os.X_OK):
        raise WorkerError(
            f"Environment {path} has no executable bin/python; repair it manually"
        )
    return str(python)


# The folder a session keeps its reports in, as the notebook and its kernels see it.
REPORTS_VARIABLE = "QIBOCAL_REPORTS_DIR"
# The remote execution connection qibocal-widgets' Remote plugin selects, by name.
REMOTE_VARIABLE = "QIBOCAL_WIDGETS_CONNECTION"


def remotes_file():
    """remotes.json where the plugin reads it: next to qibocal-report's files, on this host."""
    custom = os.environ.get("QIBOCAL_REPORT_CONFIG_DIR")
    if custom:
        return Path(custom) / "remotes.json"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return (Path(xdg) if xdg else Path.home() / ".config") / "qibocal" / "remotes.json"


def install_remote_connection(connections):
    """Make the session's remote execution connection readable on this host.

    The entry is merged into remotes.json here — versioned as the launcher
    writes it, every other connection left as it is — and written only when
    it differs, so the launcher's own file, on its own machine, is untouched.
    Answers the name to export.
    """
    (name, entry), = connections.items()
    path = remotes_file()
    try:
        document = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except ValueError as error:
        raise WorkerError(f"{path} is not valid JSON ({error}); the remote connection cannot be added")
    if not isinstance(document, dict):
        raise WorkerError(f"{path} does not hold a JSON object")
    if document.get("version", 1) != 1:
        raise WorkerError(f"{path} is of another format (version {document.get('version')}); left as it is")
    present = document.get("connections") if isinstance(document.get("connections"), dict) else {}
    if present.get(name) != entry:
        present[name] = entry
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps({"version": 1, "connections": present}, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    return name

# The requirements last installed in an environment, kept inside it: a session
# whose connection asks for others installs them on top, and only then.
REQUIREMENTS_MARKER = "qibocal-requirements.txt"


def normalize_requirements(text):
    """The requirements as compared: one per line, blank lines and comments dropped."""
    lines = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return "\n".join(lines) + "\n" if lines else ""


def has_pip(runtime, python):
    """Whether the environment can install on its own, or needs an external pip."""
    return json.loads(
        runtime.command(
            [
                python,
                "-c",
                "import json, importlib.util; "
                "print(json.dumps(importlib.util.find_spec('pip') is not None))",
            ],
            capture=True,
        )
    )


def requirement_name(line):
    """The distribution a requirements.txt line names, normalised; None for an option line.

    `name[extra]>=1`, `name @ url` and a bare URL with `#egg=name` all name one.
    """
    line = line.strip()
    if not line or line.startswith(("#", "-")):
        return None
    egg = re.search(r"#egg=([A-Za-z0-9][A-Za-z0-9._-]*)", line)
    found = egg or re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)", line)
    if not found or (not egg and "://" in line.split("@")[0]):
        return None
    return re.sub(r"[-_.]+", "-", found.group(1)).lower()


def requirement_arguments(runtime, directory, stem, wanted, defaults=()):
    """What installs `defaults` with the requirements `wanted`, the requirements winning.

    A default the requirements name is left out — theirs is the one asked
    for. With uv, the requirements are also overrides: what they say of a
    package holds for every package that depends on it, so `qibocal @ git+ssh…`
    is not contradicted by a dependency declaring `qibocal @ git+https…`.
    Answers the arguments and the files written for them, to remove after.
    """
    named = {requirement_name(line) for line in wanted.splitlines()} - {None}
    arguments = [package for package in defaults if requirement_name(package) not in named]
    files = []
    if wanted:
        listing = directory / f".{stem}.{REQUIREMENTS_MARKER}.pending"
        listing.write_text(wanted, encoding="utf-8")
        files.append(listing)
        arguments += ["-r", str(listing)]
        overrides = [line for line in wanted.splitlines() if requirement_name(line)]
        if overrides and find_uv(runtime):
            override = directory / f".{stem}.qibocal-overrides.txt.pending"
            override.write_text("\n".join(overrides) + "\n", encoding="utf-8")
            files.append(override)
            arguments += ["--override", str(override)]
    return arguments, files


def apply_requirements(runtime, path, python, text):
    """Make the environment hold what the connection asks for.

    The requirements installed last are recorded in the environment; when
    the connection asks for the same, nothing happens, and when it asks for
    others they are installed on top with pip — nothing is removed, and the
    environment is never rebuilt. A failure stops the session: the kernel
    would otherwise lack what it was promised.
    """
    wanted = normalize_requirements(text)
    marker = path / REQUIREMENTS_MARKER
    try:
        applied = marker.read_text(encoding="utf-8")
    except OSError:
        applied = ""
    if wanted == applied:
        return
    if not wanted:
        # Nothing asked for any more: nothing to install, and nothing removed.
        marker.unlink(missing_ok=True)
        return
    event(
        "status",
        message=f"Installing the connection's requirements in: {path}\n{wanted.rstrip()}",
    )
    arguments, files = requirement_arguments(runtime, path, "requirements", wanted)
    try:
        runtime.command(install_command(runtime, python, arguments))
    finally:
        for file in files:
            file.unlink(missing_ok=True)
    marker.write_text(wanted, encoding="utf-8")


def create_kernel_environment(runtime, path, requirements):
    """A new kernel environment: qibocal and the requirements, in a single install."""
    wanted = normalize_requirements(requirements)
    path.parent.mkdir(parents=True, exist_ok=True)
    arguments, files = requirement_arguments(runtime, path.parent, path.name, wanted, defaults=("qibocal",))
    kept = [argument for argument in arguments if argument == "qibocal"]
    event(
        "status",
        message="Installing kernel dependencies: "
        + " and ".join(kept + (["the requirements"] if wanted else []))
        + (f"\n{wanted.rstrip()}" if wanted else ""),
    )
    try:
        python = create_environment(runtime, path, arguments)
    finally:
        for file in files:
            file.unlink(missing_ok=True)
    if wanted:
        (path / REQUIREMENTS_MARKER).write_text(wanted, encoding="utf-8")
    return python


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


def prepare_kernels(runtime, root, target_path, target, sites, env):
    """Expose managed and previously selected environments without modifying them."""
    cache = cache_home() / "qibocal"
    registry = cache / "kernels"
    selected = target_path.resolve()
    managed_path = (cache / "envs").resolve()
    server_path = (cache / "envs" / "jupyter").resolve()
    default_path = (cache / "envs" / "qibocal").resolve()
    environments = {selected}
    if (cache / "envs").is_dir():
        environments.update(path.resolve() for path in (cache / "envs").iterdir())
    if registry.is_dir():
        for registration in sorted(registry.glob("*.json")):
            value = json.loads(registration.read_text(encoding="utf-8"))
            if not isinstance(value, str):
                raise WorkerError(f"Invalid kernel registration: {registration}")
            environments.add(Path(value).resolve())
    default_name = None
    for environment in sorted(environments):
        if environment == server_path:
            continue
        python = str(environment / "bin" / "python")
        if environment == selected:
            python = target
        elif not Path(python).is_file() or not os.access(python, os.X_OK):
            event(
                "status",
                message=f"Skipping unavailable kernel environment: {environment}",
            )
            continue
        name = (
            "qibocal"
            if environment == default_path
            else "qibocal-" + hashlib.sha256(os.fsencode(environment)).hexdigest()
        )
        target_sites = json.loads(
            runtime.command(
                [
                    python,
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
        kernel = root / "kernels" / name
        kernel.mkdir(parents=True)
        display_name = "Qibocal"
        if environment != default_path:
            display_name = f"Qibocal ({environment.name})"
            if environment.parent != managed_path:
                home = Path.home().resolve()
                display_path = (
                    Path("~") / environment.relative_to(home)
                    if environment.is_relative_to(home)
                    else environment
                )
                display_name += f" - {display_path}"
        (kernel / "kernel.json").write_text(
            json.dumps(
                {
                    "argv": [
                        python,
                        "-c",
                        bootstrap(sites, "ipykernel_launcher"),
                        "-f",
                        "{connection_file}",
                    ],
                    "display_name": display_name,
                    "language": "python",
                    "env": {
                        "PYTHONPATH": os.pathsep.join(
                            [
                                *target_sites,
                                *filter(None, [env.get("PYTHONPATH")]),
                                *sites,
                            ]
                        )
                    },
                }
            ),
            encoding="utf-8",
        )
        if environment == selected:
            default_name = name
    registry.mkdir(parents=True, exist_ok=True)
    (registry / f"{default_name}.json").write_text(
        json.dumps(str(selected)), encoding="utf-8"
    )
    return default_name


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


def srun_command(options, nested):
    """The srun call that runs this worker again on a computing node, with `nested` options.

    Answers the command and the job name given to it, when it is ours.
    """
    extra = slurm_arguments(options.get("slurm"))
    source = globals().get("WORKER_SOURCE")
    if not source:
        raise WorkerError("SLURM execution requires embedded WORKER_SOURCE")
    script = "WORKER_SOURCE = " + repr(source) + "\n" + source
    command = ["srun", "--unbuffered"]
    if options.get("queue"):
        command += ["--partition", options["queue"]]
    # A name of ours, unless the caller chose one: the launcher finds
    # the job in the queue by it the moment it is submitted, long
    # before the compute node reports the job id.
    if not any(
        item == "-J" or item.startswith(("--job-name", "-J"))
        for item in extra
    ):
        job_name = f"qibocal-nb-{secrets.token_hex(3)}"
        extra = [*extra, "--job-name", job_name]
    else:
        job_name = None
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
    description = (
        (f" {job_name}" if job_name else "")
        + (f" on partition {options['queue']}" if options.get("queue") else "")
        + (f" ({shlex.join(extra)})" if extra else "")
    )
    return command, description


def kernel_paths(options):
    """The kernel environment of these options, and the notebook server's, which must stay apart."""
    target_path = environment_path(options.get("venv", "qibocal"))
    server_path = cache_home() / "qibocal" / "envs" / "jupyter"
    resolved_server = server_path.resolve()
    resolved_target = target_path.resolve()
    if (
        resolved_server == resolved_target
        or resolved_server in resolved_target.parents
        or resolved_target in resolved_server.parents
    ):
        raise WorkerError("The target and notebook server environments must be separate")
    return target_path, server_path


def rebuild_environment(runtime, options):
    """Destroy the kernel environment and make it again, from qibocal and the requirements.

    Only a Python virtual environment is removed — a folder without
    `pyvenv.cfg` is refused, so a mistyped path costs nothing — and the
    notebook server's environment is never touched.
    """
    target_path, _ = kernel_paths(options)
    if target_path.exists() or target_path.is_symlink():
        if target_path.is_symlink() or not (target_path / "pyvenv.cfg").is_file():
            raise WorkerError(
                f"{target_path} is not a Python virtual environment; it is left as it is"
            )
        event("status", message=f"Removing the kernel environment: {target_path}")
        shutil.rmtree(target_path)
    create_kernel_environment(runtime, target_path, options.get("requirements"))
    event("status", message=f"Kernel environment regenerated: {target_path}")


def run_rebuild(runtime, options, scheduled):
    """Regenerate on the access node — the environments live in a home the nodes
    share — or on a computing node through srun, when the connection asks for it."""
    if not scheduled or not options.get("rebuild_on_compute"):
        rebuild_environment(runtime, options)
        return
    nested = dict(options, queue=None, slurm=None, workdir=str(Path.cwd()), _node_role="compute")
    command, description = srun_command(options, nested)
    event("status", message=f"Submitting SLURM job{description}; waiting for a compute node.")
    process, messages = runtime.spawn(command, capture=True)
    # The computing node's own events and lines, passed on as they come.
    for line in iter(messages.get, None):
        print(line, end="", flush=True)
    process.wait()
    if process.returncode:
        raise WorkerError(f"The regeneration on the computing node failed ({process.returncode})")


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
        if options.get("_rebuild"):
            run_rebuild(runtime, options, scheduled)
            return
        marimo = options.get("marimo", False)
        listen_host = "127.0.0.1"
        if scheduled:
            access_addresses = node_addresses(runtime)
            nested = dict(
                options,
                queue=None,
                slurm=None,
                workdir=str(Path.cwd()),
                _node_role="compute",
                _access_addresses=access_addresses,
            )
            command, description = srun_command(options, nested)
            event(
                "status",
                message=f"Submitting SLURM job{description}; waiting for a compute node.",
            )
            worker, messages = runtime.spawn(command, capture=True)
            data = wait_nested(runtime, worker, messages)
            event(
                "status",
                message=f"Forwarding access-node loopback to {data['host']}.",
            )
            # Said to be ready on that interface: make sure it is reachable
            # from here before a browser is pointed at it, and say exactly
            # what is wrong when it is not.
            failure = probe_reachable(
                data["host"],
                data["port"],
                min(runtime.deadline, time.monotonic() + 20),
                runtime.stop,
            )
            if failure is not None and not runtime.stop.is_set():
                raise WorkerError(
                    f"The notebook reported ready on {data['host']}:{data['port']}, "
                    f"but the access node cannot reach it: {failure}. The computing "
                    "node chose an interface the access node has no route to; pass "
                    "--subnet with the network the two nodes share."
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
                    options["_access_addresses"],
                    node_addresses(runtime),
                    options.get("subnet"),
                    source_for=route_source,
                )
                event(
                    "status",
                    message=f"Selected compute interface: {listen_host}. "
                    "The notebook is token-protected on this interface.",
                )
            if marimo:
                target_path = environment_path(options.get("venv", "qibocal"))
                server_path = cache_home() / "qibocal" / "envs" / "jupyter"
            else:
                target_path, server_path = kernel_paths(options)
            event(
                "status",
                message=f"Preparing notebook in {Path.cwd()}\n"
                f"Kernel environment: {target_path}"
                + ("" if marimo else f"\nServer environment: {server_path}"),
            )
            target = ensure_environment(
                runtime,
                target_path,
                packages=("qibocal",),
            )
            apply_requirements(runtime, target_path, target, options.get("requirements"))
            if marimo:
                event("status", message=f"Installing marimo in: {target_path}")
                runtime.command(install_command(runtime, target, ["marimo"]))
            else:
                server = ensure_environment(runtime, server_path, server=True)
                sites = server_sites(runtime, server)
            port, token = free_port(listen_host), secrets.token_urlsafe(32)
            env = os.environ.copy()
            if options.get("reports"):
                # The reports folder, for the code in the notebook to write to.
                reports = Path(options["reports"]).expanduser()
                reports = reports if reports.is_absolute() else Path.cwd() / reports
                reports.mkdir(parents=True, exist_ok=True)
                env[REPORTS_VARIABLE] = str(reports)
                event("status", message=f"Reports folder: {reports} (as {REPORTS_VARIABLE})")
            if options.get("_remote_connection"):
                name = install_remote_connection(options["_remote_connection"])
                env[REMOTE_VARIABLE] = name
                event("status", message=f"Remote execution: {name} (as {REMOTE_VARIABLE})")
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
                default_kernel = prepare_kernels(
                    runtime, kernel_root, target_path, target, sites, env
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
                    f"--MappingKernelManager.default_kernel_name={default_kernel}",
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
