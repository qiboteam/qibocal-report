"""Self-contained report worker, also executed on remote hosts with ``python -c``.

Creating an environment, installing into it and supervising child processes is
exactly what the notebook worker already does, so this one does not repeat it:
``notebook_worker.py`` is shipped alongside and executed as a module, and its
helpers are used from here. The two therefore put environments in the same
place, create them the same way, and report progress with the same events.
"""

import json
import math
import os
import shlex
import signal
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener

READY_PREFIX = "QIBOCAL_REPORT_READY "

# The launcher prepends `SHARED_SOURCE = <notebook_worker.py>`; running from an
# installed package instead, the sibling module is read from disk.
_source = globals().get("SHARED_SOURCE")
if _source is None:
    _source = Path(__file__).with_name("notebook_worker.py").read_text(encoding="utf-8")

# A name other than "__main__", or the notebook worker would start itself.
_shared = {"__name__": "qibocal_report.notebook_worker"}
exec(compile(_source, "notebook_worker.py", "exec"), _shared)  # noqa: S102

Runtime = _shared["Runtime"]
Stopped = _shared["Stopped"]
WorkerError = _shared["WorkerError"]
ensure_environment = _shared["ensure_environment"]
environment_install_command = _shared["environment_install_command"]
environment_path = _shared["environment_path"]
event = _shared["event"]
free_port = _shared["free_port"]
log_node = _shared["log_node"]
monitor_stdin = _shared["monitor_stdin"]


def announce(port):
    """Tell the launcher which port the report server listens on."""
    print(READY_PREFIX + json.dumps({"port": port}), flush=True)


def reports_path():
    """The shared reports directory of this host, as ``config.get_reports_dir`` names it.

    Spelled out again because the worker runs where the package is not
    installed yet; the two must agree, and a test holds them to it.
    """
    custom = os.environ.get("QIBOCAL_REPORT_DATA_DIR")
    if custom:
        return Path(custom) / "reports"
    root = os.environ.get("XDG_DATA_HOME")
    base = Path(root) if root else Path.home() / ".local" / "share"
    return base / "qibocal" / "reports"


def reports_directory(given):
    """The directory to serve: the one named, which must exist, or the shared one."""
    if given:
        directory = Path(given).expanduser()
        if not directory.is_dir():
            raise WorkerError(f"No report directory {directory} on this host")
        return directory
    directory = reports_path()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


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


def upgrade_commands(python, packages, seeded):
    """The two installs that bring a package up to date, whatever its version says.

    A branch or commit archive carries the same version number as the one
    installed, so pip would call it satisfied and change nothing: the package
    itself is put back by force, on its own, and the dependencies brought up
    to date after it — as the launcher updates its own installation.
    """
    base = environment_install_command(python, [], seeded)
    return [
        [*base, "--upgrade", "--force-reinstall", "--no-deps", *packages],
        [*base, "--upgrade", *packages],
    ]


def ensure_qibocal(runtime, path, packages, upgrade=False):
    """Return the environment's ``qibocal``, installing it when it is missing.

    ``ensure_environment`` only installs into an environment it creates, so an
    environment that exists but was never given the report package is filled in
    here — which is what happens the second time a different package is asked
    for in the same environment. With ``upgrade``, the packages are put back by
    force even when the environment has them.
    """
    python = ensure_environment(runtime, path, packages=packages)
    executable = path / "bin" / "qibocal"
    if not executable.is_file():
        event("status", message=f"Installing {', '.join(packages)} in: {path}")
        runtime.command(
            environment_install_command(python, packages, has_pip(runtime, python))
        )
    elif upgrade:
        event("status", message=f"Updating {', '.join(packages)} in: {path}")
        for command in upgrade_commands(python, packages, has_pip(runtime, python)):
            runtime.command(command)
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise WorkerError(
            f"Environment {path} has no executable bin/qibocal after installing "
            f"{', '.join(packages)}; check the package name with --install"
        )
    return executable


def wait_http(runtime, url, process):
    """Wait until the report server answers, or give up with its exit status."""
    opener = build_opener(ProxyHandler({}))
    while True:
        runtime.check()
        if process.poll() is not None:
            raise WorkerError(
                f"Report server exited before startup (status {process.returncode})"
            )
        try:
            with opener.open(url, timeout=1):
                return
        except HTTPError:
            # An error page is still an answer: the server is listening.
            return
        except (URLError, TimeoutError, ConnectionError, OSError):
            time.sleep(0.1)


def run(options):
    given = options.get("timeout")
    timeout = 300.0 if given is None else float(given)
    if not math.isfinite(timeout) or timeout <= 0:
        raise WorkerError("Report timeout must be finite and positive")
    runtime = Runtime(timeout)
    handlers = {}
    try:
        log_node("report")
        for sig in (signal.SIGTERM, signal.SIGINT):
            handlers[sig] = signal.signal(sig, lambda *_: runtime.stop.set())
        monitor_stdin(runtime.stop)
        # The server writes nothing where it starts, so without a working
        # directory a fresh temporary one keeps it out of the home folder.
        workdir = options.get("workdir")
        os.chdir(
            Path(workdir).expanduser()
            if workdir
            else tempfile.mkdtemp(prefix="qibocal-report-")
        )
        packages = shlex.split(options.get("install") or "qibocal-report")
        if not packages:
            raise WorkerError("--install must name at least one package")
        path = environment_path(options.get("venv") or "qibocal")

        if options.get("upgrade"):
            # An update, and nothing else: the packages put back, and done.
            ensure_qibocal(runtime, path, packages, upgrade=True)
            event("status", message=f"{', '.join(packages)} is up to date in {path}.")
            return

        directory = reports_directory(options.get("directory"))
        executable = ensure_qibocal(runtime, path, packages)
        port = free_port()
        command = [
            str(executable),
            "report",
            "server",
            str(directory.resolve()),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--auth" if options.get("auth") else "--no-auth",
        ]
        event("status", message=f"Starting the report server on port {port}.")
        process, _ = runtime.spawn(command)
        wait_http(runtime, f"http://127.0.0.1:{port}/", process)
        runtime.check()
        announce(port)
        while not runtime.stop.wait(0.1):
            if process.poll() is not None:
                raise WorkerError(f"Report server exited (status {process.returncode})")
    except Stopped:
        pass
    finally:
        runtime.close()
        for sig, handler in handlers.items():
            signal.signal(sig, handler)


def main():
    try:
        options = json.loads(sys.argv[1])
        if not isinstance(options, dict):
            raise WorkerError("Report options must be a JSON object")
        run(options)
    except (WorkerError, OSError, ValueError, IndexError) as error:
        print(f"Report worker: {error}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
