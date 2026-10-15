"""Starting a report server on another machine, over SSH.

The shape is the notebook's: ship a standard-library worker through ``ssh``,
wait for it to announce its port, tunnel that port back, and register the local
address so the dashboard finds it. Everything shared with the notebooks —
reading the worker, stopping processes, waiting for the tunnel — is imported
from :mod:`qibocal_report.notebook` rather than written twice.
"""

import json
import queue
import shlex
import signal
import subprocess
import threading
import time
from pathlib import Path

import click
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from qibocal_report import config
from qibocal_report.notebook import (
    NotebookOutput,
    _read_stderr,
    _read_worker,
    _wait_message,
    _wait_tunnel,
    free_port,
    ssh_arguments,
    stop_process,
)
from qibocal_report.report_worker import READY_PREFIX


class RemoteServerOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ssh: str = Field(min_length=1)
    # None is the shared reports directory of the remote host, which the
    # worker alone can locate.
    directory: str | None = Field(default=None, min_length=1)
    venv: str = Field(default="qibocal", min_length=1)
    workdir: str | None = Field(default=None, min_length=1)
    install: str = Field(default="qibocal-report", min_length=1)
    auth: bool = False
    timeout: float = Field(default=300.0, gt=0, allow_inf_nan=False)
    # How the tunnelled address is registered here; the worker never sees these.
    name: str | None = Field(default=None, min_length=1)
    registered: bool = True

    @property
    def served(self) -> str:
        """The directory, as spoken of in messages."""
        return self.directory or "the shared reports directory"


def load_options(values: dict) -> RemoteServerOptions:
    """Validate the flags, naming the mistake the way the notebooks do."""
    given = {key: value for key, value in values.items() if value is not None}
    try:
        options = RemoteServerOptions.model_validate(given)
        ssh_arguments(options.ssh)
        shlex.split(options.install)
        return options
    except (ValidationError, ValueError) as exc:
        raise click.ClickException(f"Invalid remote server options: {exc}") from exc


def worker_source() -> str:
    """The worker, with the notebook worker it borrows from carried along."""
    directory = Path(__file__).parent
    shared = (directory / "notebook_worker.py").read_text(encoding="utf-8")
    worker = (directory / "report_worker.py").read_text(encoding="utf-8")
    return f"SHARED_SOURCE = {shared!r}\n{worker}"


def worker_command(options: RemoteServerOptions) -> list[str]:
    """The whole remote invocation, destination included."""
    arguments, destination = ssh_arguments(options.ssh)
    remote = [
        "python3",
        "-u",
        "-c",
        worker_source(),
        json.dumps(options.model_dump(exclude={"ssh", "name", "registered"})),
    ]
    return [*ssh_base(arguments), destination, shlex.join(remote)]


def ssh_base(arguments: list[str]) -> list[str]:
    return [
        "ssh",
        *arguments,
        "-T",
        "-o",
        "ExitOnForwardFailure=yes",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "ServerAliveCountMax=3",
    ]


def register(url: str, options: RemoteServerOptions, destination: str) -> None:
    """Make the tunnelled server a dashboard entry, as a local one becomes."""
    if not options.registered:
        return
    if options.directory:
        directory = Path(options.directory).name or options.directory
    else:
        directory = "reports"
    try:
        config.add_server(
            url=url,
            name=options.name or f"{destination}-{directory}",
            description=f"Serving reports from {options.served} on {destination}",
            avatar="quantum-ring",
        )
    except OSError as exc:
        # A server that cannot be remembered is still a server that runs.
        raise click.ClickException(f"Could not register '{url}': {exc}") from exc


def launch(options: RemoteServerOptions) -> None:
    """Run the report server on the remote host and tunnel it back here."""
    output = NotebookOutput()
    arguments, destination = ssh_arguments(options.ssh)
    deadline = time.monotonic() + options.timeout
    processes: list[subprocess.Popen] = []
    readers: list[threading.Thread] = []
    previous_sigterm = signal.getsignal(signal.SIGTERM)

    def interrupt(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupt)
    try:
        output.status(f"Connecting to SSH destination {destination}.")
        process = subprocess.Popen(
            worker_command(options),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        processes.append(process)
        messages: queue.Queue = queue.Queue()
        readers = [
            threading.Thread(
                target=_read_worker,
                args=(process, messages, output, READY_PREFIX),
                daemon=True,
            ),
            threading.Thread(target=_read_stderr, args=(process, output), daemon=True),
        ]
        for reader in readers:
            reader.start()
        ready = _wait_message(process, messages, deadline, "report")
        if type(ready.get("port")) is not int or not 1 <= ready["port"] <= 65535:
            raise click.ClickException("Invalid report startup response.")

        output.status("Opening SSH tunnel to the remote report server.")
        port = free_port()
        tunnel = subprocess.Popen(
            [
                *ssh_base(arguments),
                "-N",
                "-L",
                f"127.0.0.1:{port}:127.0.0.1:{ready['port']}",
                destination,
            ],
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        processes.append(tunnel)
        reader = threading.Thread(
            target=_read_stderr, args=(tunnel, output), daemon=True
        )
        readers.append(reader)
        reader.start()

        url = f"http://localhost:{port}"
        _wait_tunnel(f"{url}/", processes, deadline, "report")
        register(url, options, destination)
        output.console.print(
            Panel(
                Text(
                    f"Reports from {options.served} on {destination} are ready.\n"
                    "Open the URL below, or pick the server in the dashboard.\n"
                    "Press Ctrl+C to stop the server and its tunnel."
                ),
                title="Report server ready",
                border_style="green",
                expand=False,
            )
        )
        # Printed plainly, because the launcher reads the address from here.
        Console().print(Text(url, style="bold cyan"), soft_wrap=True)
        while all(process.poll() is None for process in processes):
            time.sleep(0.2)
        failed = next(process for process in processes if process.poll() is not None)
        if failed is not processes[0] or failed.returncode:
            raise click.ClickException(
                f"Remote report server exited with status {failed.returncode}."
            )
    except KeyboardInterrupt:
        output.status("Stopping the remote report server.", "yellow")
    except OSError as exc:
        raise click.ClickException(f"Could not start the remote server: {exc}") from exc
    finally:
        try:
            for process in reversed(processes):
                stop_process(process)
            for reader in readers:
                reader.join(timeout=1)
        finally:
            signal.signal(signal.SIGTERM, previous_sigterm)
