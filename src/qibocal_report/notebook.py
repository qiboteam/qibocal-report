"""Notebook connection configuration and local session supervision."""

import ipaddress
import json
import os
import queue
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, build_opener

import click
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from qibocal_report import config
from qibocal_report.notebook_worker import EVENT_PREFIX

READY_PREFIX = "QIBOCAL_NOTEBOOK_READY "


class NotebookOutput:
    """Render locally so transported workers need only the standard library."""

    def __init__(self):
        self.console = Console(stderr=True)

    def status(self, message: str, style: str = "cyan") -> None:
        self.console.print(Text(message, style=style))

    def line(self, line: str) -> None:
        if not line.startswith(EVENT_PREFIX):
            self.console.print(
                Text.from_ansi(line.rstrip("\n")),
                style="bold red" if line.startswith("Notebook worker:") else "dim",
            )
            return
        try:
            data = json.loads(line[len(EVENT_PREFIX) :])
        except ValueError:
            data = None
        if isinstance(data, dict):
            if data.get("kind") == "status" and isinstance(data.get("message"), str):
                self.status(data["message"])
                return
            if (
                data.get("kind") == "node"
                and isinstance(data.get("role"), str)
                and isinstance(data.get("identity"), dict)
                and all(
                    isinstance(key, str) and isinstance(value, (str, int))
                    for key, value in data["identity"].items()
                    if key != "slurm"
                )
                and isinstance(data["identity"].get("slurm", {}), dict)
                and all(
                    isinstance(key, str) and isinstance(value, str)
                    for key, value in data["identity"].get("slurm", {}).items()
                )
            ):
                table = Table.grid(padding=(0, 2))
                table.add_column(style="bold", no_wrap=True)
                table.add_column(overflow="fold")
                labels = {
                    "fqdn": "FQDN",
                    "system": "OS",
                    "release": "OS release",
                    "python": "Python executable",
                    "python_version": "Python version",
                    "pid": "PID",
                    "cwd": "Arrival directory",
                }
                for key, value in data["identity"].items():
                    if key != "slurm":
                        table.add_row(
                            Text(labels.get(key, key.replace("_", " ").capitalize())),
                            Text(str(value)),
                        )
                for key, value in data["identity"].get("slurm", {}).items():
                    table.add_row(Text(key), Text(value))
                self.console.print(
                    Panel(
                        table,
                        title=Text(
                            f"{data['role'].capitalize()} node", style="bold cyan"
                        ),
                        border_style="cyan",
                        expand=False,
                    )
                )
                return
        self.status("Invalid notebook diagnostic received:", "bold red")
        self.console.print(Text(line.rstrip("\n")))


class NotebookOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ssh: str | None = Field(default=None, min_length=1)
    queue: str | None = Field(default=None, min_length=1)
    slurm: str | None = Field(default=None, min_length=1)
    workdir: str | None = Field(default=None, min_length=1)
    venv: str = Field(default="qibocal", min_length=1)
    marimo: bool = False
    no_interactive: bool = False
    timeout: float = Field(default=300.0, gt=0, allow_inf_nan=False)
    subnet: str | None = Field(default=None, min_length=1)

    @field_validator("subnet")
    @classmethod
    def validate_subnet(cls, value: str | None) -> str | None:
        if value is not None:
            ipaddress.ip_network(value)
        return value


def connection_file() -> Path:
    """Share the report configuration directory without creating it."""
    return config.get_config_dir(create=False) / "notebooks.json"


def load_connections(*, missing_ok: bool = False) -> dict:
    path = connection_file()
    try:
        connections = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        if missing_ok:
            return {}
        raise click.ClickException(f"Could not read '{path}': {exc}") from exc
    except (OSError, ValueError) as exc:
        raise click.ClickException(f"Could not read '{path}': {exc}") from exc
    if not isinstance(connections, dict):
        raise click.ClickException(f"'{path}' must contain a connection-name object.")
    for name, values in connections.items():
        if not isinstance(values, dict):
            raise click.ClickException(
                f"Notebook connection '{name}' must be an object."
            )
    return connections


def registered_connection(connections: dict, name: str) -> dict:
    if name not in connections:
        raise click.ClickException(
            f"Notebook connection '{name}' not found in '{connection_file()}'."
        )
    return connections[name]


def load_options(name: str | None, overrides: dict) -> NotebookOptions:
    values = {}
    if name is not None:
        values = registered_connection(load_connections(), name)
    values = {
        **values,
        **{key: value for key, value in overrides.items() if value is not None},
    }
    try:
        options = NotebookOptions.model_validate(values)
        if options.ssh:
            ssh_arguments(options.ssh)
        if options.slurm:
            shlex.split(options.slurm)
        return options
    except (ValidationError, ValueError) as exc:
        raise click.ClickException(f"Invalid notebook options: {exc}") from exc


def prompt_options(
    parameters: list[click.Option], current: NotebookOptions | None = None
) -> dict:
    defaults = (current or NotebookOptions()).model_dump()
    console = Console()
    table = Table(
        title="Choose options to change"
        if current is not None
        else "Choose options to change from their defaults"
    )
    table.add_column("#", style="cyan")
    table.add_column("Option")
    table.add_column("Current" if current is not None else "Default")
    table.add_column("Description")
    for index, parameter in enumerate(parameters, 1):
        default = defaults[parameter.name]
        table.add_row(
            str(index),
            Text(parameter.opts[0]),
            Text("None" if default is None else str(default)),
            Text(parameter.help or ""),
        )
    console.print(table)

    def selection(value: str) -> list[click.Option]:
        tokens = value.replace(",", " ").split()
        selected = []
        for token in tokens:
            if (
                not token.isascii()
                or not token.isdigit()
                or not 1 <= int(token) <= len(parameters)
            ):
                raise click.BadParameter(
                    f"Choose numbers between 1 and {len(parameters)}."
                )
            parameter = parameters[int(token) - 1]
            if parameter not in selected:
                selected.append(parameter)
        return selected

    selected = click.prompt(
        "Options to change (comma-separated numbers; Enter keeps "
        + ("current values)" if current is not None else "defaults)"),
        default="",
        show_default=False,
        value_proc=selection,
    )
    values = {}
    for parameter in selected:
        default = defaults[parameter.name]
        label = parameter.opts[0]
        if parameter.is_bool_flag:
            values[parameter.name] = click.confirm(label, default=default)
        else:
            values[parameter.name] = click.prompt(
                label, default=default, type=parameter.type
            )
    return values


def add_connection(name: str, values: dict) -> None:
    if not name.strip():
        raise click.ClickException("Connection name must not be empty.")
    options = load_options(None, values)
    connections = load_connections(missing_ok=True)
    if name in connections:
        raise click.ClickException(f"Notebook connection '{name}' already exists.")
    connections[name] = options.model_dump(exclude_unset=True)
    write_connections(connections)
    click.echo(f"Added notebook connection '{name}'.")


def update_connection(name: str, values: dict) -> None:
    connections = load_connections()
    current = registered_connection(connections, name)
    options = load_options(
        None,
        {
            **current,
            **{key: value for key, value in values.items() if value is not None},
        },
    )
    connections[name] = options.model_dump(exclude_unset=True)
    write_connections(connections)
    click.echo(f"Updated notebook connection '{name}'.")


def remove_connection(name: str) -> None:
    connections = load_connections()
    registered_connection(connections, name)
    del connections[name]
    write_connections(connections)
    click.echo(f"Removed notebook connection '{name}'.")


def write_connections(connections: dict) -> None:
    path = connection_file()
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(connections, stream, indent=2)
            stream.write("\n")
        temporary.replace(path)
    except OSError as exc:
        raise click.ClickException(f"Could not write '{path}': {exc}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def list_connections(*, raw: bool = False) -> None:
    if raw:
        path = connection_file()
        try:
            contents = path.read_bytes()
        except OSError as exc:
            raise click.ClickException(f"Could not read '{path}': {exc}") from exc
        click.echo(contents, nl=False)
        return
    connections = load_connections(missing_ok=True)
    console = Console()
    if not connections:
        console.print("No notebook connections registered.")
        return
    table = Table(title="Notebook connections")
    table.add_column("Connection", style="bold cyan")
    table.add_column("Configured options", overflow="fold")
    for name, values in connections.items():
        table.add_row(
            Text(name),
            Text(
                "\n".join(
                    f"{key}: {json.dumps(value, ensure_ascii=False)}"
                    for key, value in values.items()
                )
                or "(defaults)"
            ),
        )
    console.print(table)


def ssh_arguments(value: str) -> tuple[list[str], str]:
    """Treat the last SSH argument as its destination, never as a remote command."""
    arguments = shlex.split(value)
    if not arguments or arguments[-1].startswith("-"):
        raise ValueError("--ssh must end with a host or user@host destination")
    return arguments[:-1], arguments[-1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def stop_process(process: subprocess.Popen) -> None:
    if process.stdin:
        process.stdin.close()
        try:
            process.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            pass
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        process.wait()
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def _read_worker(
    process: subprocess.Popen, messages: queue.Queue, output: NotebookOutput
) -> None:
    for line in process.stdout:
        if line.startswith(READY_PREFIX):
            messages.put(line[len(READY_PREFIX) :])
        else:
            output.line(line)
    messages.put(None)


def _read_stderr(process: subprocess.Popen, output: NotebookOutput) -> None:
    for line in process.stderr:
        output.line(line)


def _wait_ready(
    process: subprocess.Popen, messages: queue.Queue, deadline: float
) -> dict:
    while time.monotonic() < deadline:
        try:
            message = messages.get(
                timeout=min(0.2, max(0.001, deadline - time.monotonic()))
            )
        except queue.Empty:
            continue
        if message is None:
            raise click.ClickException(
                f"Notebook launcher exited before startup (status {process.poll()})."
            )
        try:
            ready = json.loads(message)
        except ValueError as exc:
            raise click.ClickException("Invalid notebook startup response.") from exc
        if (
            not isinstance(ready, dict)
            or type(ready.get("port")) is not int
            or not 1 <= ready["port"] <= 65535
            or not isinstance(ready.get("token"), str)
            or not ready["token"]
            or ready.get("path") not in ("/", "/lab")
        ):
            raise click.ClickException("Invalid notebook startup response.")
        return ready
    raise click.ClickException(
        "Timed out waiting for notebook startup; increase --timeout."
    )


def _wait_tunnel(url: str, processes: list[subprocess.Popen], deadline: float) -> None:
    from urllib.error import URLError

    opener = build_opener(ProxyHandler({}))
    while time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            raise click.ClickException(
                "Notebook server or SSH tunnel exited during startup."
            )
        try:
            with opener.open(
                url, timeout=min(1, max(0.001, deadline - time.monotonic()))
            ):
                return
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise click.ClickException("Timed out waiting for the notebook SSH tunnel.")


def launch(options: NotebookOptions) -> None:
    output = NotebookOutput()
    worker = Path(__file__).with_name("notebook_worker.py").read_text(encoding="utf-8")
    source = f"WORKER_SOURCE = {worker!r}\n{worker}"
    worker_options = options.model_dump(exclude={"ssh", "no_interactive"})
    command = [
        "python3" if options.ssh else sys.executable,
        "-u",
        "-c",
        source,
        json.dumps(worker_options),
    ]
    ssh_base = None
    destination = None
    if options.ssh:
        arguments, destination = ssh_arguments(options.ssh)
        ssh_base = [
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
        command = [*ssh_base, destination, shlex.join(command)]
    deadline = time.monotonic() + options.timeout
    processes = []
    previous_sigterm = signal.getsignal(signal.SIGTERM)

    def interrupt(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupt)
    readers = []
    try:
        output.status(
            f"Connecting to SSH destination {destination}."
            if destination
            else "Starting local notebook launcher."
        )
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        processes.append(process)
        messages = queue.Queue()
        readers = [
            threading.Thread(
                target=_read_worker, args=(process, messages, output), daemon=True
            ),
            threading.Thread(target=_read_stderr, args=(process, output), daemon=True),
        ]
        for reader in readers:
            reader.start()
        ready = _wait_ready(process, messages, deadline)
        port = ready["port"]
        if ssh_base is not None:
            output.status("Opening SSH tunnel to the local notebook URL.")
            port = free_port()
            tunnel = subprocess.Popen(
                [
                    *ssh_base,
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
        query = urlencode(
            {"access_token" if options.marimo else "token": ready["token"]}
        )
        url = f"http://127.0.0.1:{port}{ready['path']}?{query}"
        _wait_tunnel(url, processes, deadline)
        output.console.print(
            Panel(
                Text(
                    f"{'Marimo' if options.marimo else 'JupyterLab'} is ready.\n"
                    "Open the URL below in your browser.\n"
                    "Press Ctrl+C to stop the notebook and its tunnels."
                ),
                title="Notebook ready",
                border_style="green",
                expand=False,
            )
        )
        Console().print(Text(url, style="bold cyan"), soft_wrap=True)
        if not options.no_interactive and not webbrowser.open(url):
            output.status("Could not open a browser; use the URL above.", "yellow")
        while all(process.poll() is None for process in processes):
            time.sleep(0.2)
        failed = next(process for process in processes if process.poll() is not None)
        if failed is not processes[0] or failed.returncode:
            raise click.ClickException(
                f"Notebook session exited with status {failed.returncode}."
            )
    except KeyboardInterrupt:
        output.status("Stopping notebook session.", "yellow")
    except OSError as exc:
        raise click.ClickException(f"Could not launch notebook session: {exc}") from exc
    finally:
        try:
            for process in reversed(processes):
                stop_process(process)
            for reader in readers:
                reader.join(timeout=1)
        finally:
            signal.signal(signal.SIGTERM, previous_sigterm)
