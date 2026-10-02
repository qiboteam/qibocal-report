"""Notebook connection configuration and local session supervision."""

import json
import os
import queue
import shlex
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, build_opener

import click
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from qibocal_report import config

READY_PREFIX = "QIBOCAL_NOTEBOOK_READY "


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


def connection_file() -> Path:
    """Share the report configuration directory without creating it."""
    return config.get_config_dir(create=False) / "notebooks.json"


def load_options(name: str | None, overrides: dict) -> NotebookOptions:
    values = {}
    if name is not None:
        path = connection_file()
        try:
            connections = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise click.ClickException(f"Could not read '{path}': {exc}") from exc
        if not isinstance(connections, dict):
            raise click.ClickException(
                f"'{path}' must contain a connection-name object."
            )
        if name not in connections:
            raise click.ClickException(
                f"Notebook connection '{name}' not found in '{path}'."
            )
        values = connections[name]
        if not isinstance(values, dict):
            raise click.ClickException(
                f"Notebook connection '{name}' must be an object."
            )
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


def _read_worker(process: subprocess.Popen, messages: queue.Queue) -> None:
    for line in process.stdout:
        if line.startswith(READY_PREFIX):
            messages.put(line[len(READY_PREFIX) :])
        else:
            click.echo(line, nl=False, err=True)
    messages.put(None)


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
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        processes.append(process)
        messages = queue.Queue()
        threading.Thread(
            target=_read_worker, args=(process, messages), daemon=True
        ).start()
        ready = _wait_ready(process, messages, deadline)
        port = ready["port"]
        if ssh_base is not None:
            port = free_port()
            tunnel = subprocess.Popen(
                [
                    *ssh_base,
                    "-N",
                    "-L",
                    f"127.0.0.1:{port}:127.0.0.1:{ready['port']}",
                    destination,
                ],
                start_new_session=True,
            )
            processes.append(tunnel)
        query = urlencode(
            {"access_token" if options.marimo else "token": ready["token"]}
        )
        url = f"http://127.0.0.1:{port}{ready['path']}?{query}"
        _wait_tunnel(url, processes, deadline)
        click.echo(url)
        if not options.no_interactive and not webbrowser.open(url):
            click.echo("Could not open a browser; use the URL above.", err=True)
        click.echo("Press Ctrl+C to stop the notebook and its tunnels.", err=True)
        while all(process.poll() is None for process in processes):
            time.sleep(0.2)
        failed = next(process for process in processes if process.poll() is not None)
        if failed is not processes[0] or failed.returncode:
            raise click.ClickException(
                f"Notebook session exited with status {failed.returncode}."
            )
    except KeyboardInterrupt:
        click.echo("Stopping notebook session.", err=True)
    except OSError as exc:
        raise click.ClickException(f"Could not launch notebook session: {exc}") from exc
    finally:
        try:
            for process in reversed(processes):
                stop_process(process)
        finally:
            signal.signal(signal.SIGTERM, previous_sigterm)
