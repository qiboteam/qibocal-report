import io
import json
import queue
import shlex
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import MagicMock, patch
from urllib.parse import urlsplit

import click
import pytest
from click.testing import CliRunner
from rich.console import Console

from qibocal_report.cli import main
from qibocal_report.notebook import (
    READY_PREFIX,
    NotebookOptions,
    NotebookOutput,
    _read_stderr,
    _read_worker,
    _wait_ready,
    _wait_tunnel,
    connection_file,
    launch,
    load_options,
    ssh_arguments,
    stop_process,
)
from qibocal_report.notebook_worker import EVENT_PREFIX


@pytest.mark.parametrize("color", [False, True])
def test_rich_node_output(color):
    stream = io.StringIO()
    output = NotebookOutput()
    output.console = Console(file=stream, force_terminal=color, width=120)
    output.line(
        EVENT_PREFIX
        + json.dumps(
            {
                "kind": "node",
                "role": "compute",
                "identity": {
                    "hostname": "compute-1",
                    "cwd": "/work/[red]literal[/red]",
                    "slurm": {"SLURM_JOB_ID": "123", "SLURM_JOB_PARTITION": "chip"},
                },
            }
        )
    )
    text = stream.getvalue()
    assert "Compute node" in text
    assert "Hostname" in text and "compute-1" in text
    assert "/work/[red]literal[/red]" in text
    assert "SLURM_JOB_ID" in text and "123" in text
    assert "SLURM_JOB_PARTITION" in text
    assert EVENT_PREFIX not in text
    assert ("\x1b[" in text) is color


@pytest.mark.parametrize(
    "data",
    [
        "{",
        "[]",
        '{"kind":"unknown"}',
        '{"kind":"node","role":"compute","identity":{"slurm":[]}}',
    ],
)
def test_invalid_diagnostic_visible(data):
    stream = io.StringIO()
    output = NotebookOutput()
    output.console = Console(file=stream, width=160)
    output.line(EVENT_PREFIX + data)
    assert "Invalid notebook diagnostic received" in stream.getvalue()
    assert data in stream.getvalue()


def test_worker_streams_keep_readiness_separate():
    process = worker_process()
    process.stderr = io.StringIO(
        EVENT_PREFIX
        + json.dumps({"kind": "status", "message": "Waiting for allocation"})
        + "\nraw scheduler log\n"
    )
    output = NotebookOutput()
    stream = io.StringIO()
    output.console = Console(file=stream)
    messages = queue.Queue()
    _read_stderr(process, output)
    _read_worker(process, messages, output)
    assert json.loads(messages.get())["port"] == 8123
    assert messages.get() is None
    assert "Waiting for allocation" in stream.getvalue()
    assert "raw scheduler log" in stream.getvalue()
    assert READY_PREFIX not in stream.getvalue()


def test_notebook_help():
    result = CliRunner().invoke(main, ["notebook", "--help"])
    assert result.exit_code == 0
    for option in (
        "--ssh",
        "--queue",
        "--marimo",
        "--workdir",
        "--slurm",
        "--venv",
        "-n",
    ):
        assert option in result.output


def test_connection_file_xdg(tmp_path, monkeypatch):
    monkeypatch.delenv("QIBOCAL_REPORT_CONFIG_DIR")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert connection_file() == tmp_path / "qibocal-report" / "notebooks.json"
    assert not connection_file().parent.exists()


def test_connection_file_home(tmp_path, monkeypatch):
    monkeypatch.delenv("QIBOCAL_REPORT_CONFIG_DIR")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert (
        connection_file() == tmp_path / ".config" / "qibocal-report" / "notebooks.json"
    )


def test_cli_defaults():
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(main, ["notebook"])
    assert result.exit_code == 0
    assert mock.call_args.args == (NotebookOptions(),)
    assert not connection_file().exists()


def test_named_connection_cli_overrides():
    connection_file().write_text(
        json.dumps(
            {
                "chip": {
                    "ssh": "user@login",
                    "queue": "old",
                    "marimo": True,
                    "no_interactive": True,
                    "timeout": 900,
                }
            }
        ),
        encoding="utf-8",
    )
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(
            main,
            [
                "notebook",
                "chip",
                "-q",
                "new",
                "--jupyter",
                "--interactive",
                "-w",
                "/data",
                "--timeout",
                "120",
            ],
        )
    assert result.exit_code == 0, result.output
    options = mock.call_args.args[0]
    assert options.ssh == "user@login"
    assert options.queue == "new"
    assert options.workdir == "/data"
    assert options.marimo is False
    assert options.no_interactive is False
    assert options.timeout == 120


def test_cli_short_options():
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(
            main,
            [
                "notebook",
                "-q",
                "chip",
                "-w",
                "~/runs",
                "-n",
                "--marimo",
                "--venv",
                "./env",
                "--slurm",
                "--time=01:00:00",
            ],
        )
    assert result.exit_code == 0, result.output
    options = mock.call_args.args[0]
    assert options.queue == "chip"
    assert options.workdir == "~/runs"
    assert options.no_interactive
    assert options.marimo
    assert options.venv == "./env"
    assert options.slurm == "--time=01:00:00"


@pytest.mark.parametrize(
    "contents, error",
    [
        ("{", "Could not read"),
        ("[]", "connection-name object"),
        ('{"chip": []}', "must be an object"),
        ('{"other": {}}', "not found"),
        ('{"chip": {"typo": true}}', "Invalid notebook options"),
        ('{"chip": {"marimo": "yes"}}', "Invalid notebook options"),
        ('{"chip": {"timeout": -1}}', "Invalid notebook options"),
    ],
)
def test_invalid_connection(contents, error):
    connection_file().write_text(contents, encoding="utf-8")
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(main, ["notebook", "chip"])
    assert result.exit_code == 1
    assert error in result.output
    mock.assert_not_called()


def test_missing_connection():
    result = CliRunner().invoke(main, ["notebook", "missing"])
    assert result.exit_code == 1
    assert "Could not read" in result.output


@pytest.mark.parametrize(
    "arguments",
    [
        ["--ssh", "'unterminated"],
        ["--ssh", "-p"],
        ["--slurm", "'unterminated"],
        ["--timeout", "0"],
        ["--timeout", "nan"],
    ],
)
def test_invalid_cli_options(arguments):
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(main, ["notebook", *arguments])
    assert result.exit_code != 0
    mock.assert_not_called()


def test_ssh_arguments():
    assert ssh_arguments('-p 2222 -i "my key" user@login') == (
        ["-p", "2222", "-i", "my key"],
        "user@login",
    )


def test_config_not_modified():
    path = connection_file()
    text = '{"chip": {"venv": "/custom/env"}}\n'
    path.write_text(text, encoding="utf-8")
    assert load_options("chip", {}).venv == "/custom/env"
    assert path.read_text(encoding="utf-8") == text


def worker_process():
    process = MagicMock()
    process.stdout = io.StringIO(
        READY_PREFIX
        + json.dumps(
            {"host": "compute", "port": 8123, "token": "secret", "path": "/lab"}
        )
        + "\n"
    )
    process.poll.return_value = None
    process.stderr = io.StringIO("")
    process.wait.return_value = 0
    return process


@pytest.mark.parametrize("ssh", [None, "-p 2222 user@login"])
@pytest.mark.parametrize("slurm", [False, True])
def test_launch_composes_layers(ssh, slurm, capsys):
    process = worker_process()
    tunnel = MagicMock()
    tunnel.poll.return_value = None
    tunnel.stdin = None
    options = NotebookOptions(
        ssh=ssh,
        queue="chip" if slurm else None,
        workdir="/data with space",
        no_interactive=True,
    )
    with (
        patch(
            "qibocal_report.notebook.subprocess.Popen", side_effect=[process, tunnel]
        ) as popen,
        patch("qibocal_report.notebook._wait_tunnel") as wait_tunnel,
        patch("qibocal_report.notebook.free_port", return_value=9000),
        patch("qibocal_report.notebook.webbrowser.open") as browser,
        patch("qibocal_report.notebook.time.sleep", side_effect=KeyboardInterrupt),
        patch("qibocal_report.notebook.stop_process") as stop,
    ):
        launch(options)
    command = popen.call_args_list[0].args[0]
    if ssh:
        assert command[:3] == ["ssh", "-p", "2222"]
        assert command[-2] == "user@login"
        worker_command = shlex.split(command[-1])
        assert worker_command[:3] == ["python3", "-u", "-c"]
        tunnel_command = popen.call_args_list[1].args[0]
        assert tunnel_command[-3:] == [
            "-L",
            "127.0.0.1:9000:127.0.0.1:8123",
            "user@login",
        ]
        assert stop.call_args_list[0].args[0] is tunnel
    else:
        worker_command = command
        assert popen.call_count == 1
    assert "WORKER_SOURCE = " in worker_command[3]
    remote_options = json.loads(worker_command[-1])
    assert remote_options["queue"] == ("chip" if slurm else None)
    assert remote_options["workdir"] == "/data with space"
    assert "ssh" not in remote_options
    assert (
        wait_tunnel.call_args.args[0]
        == f"http://127.0.0.1:{9000 if ssh else 8123}/lab?token=secret"
    )
    browser.assert_not_called()
    assert stop.call_args_list[-1].args[0] is process
    output = capsys.readouterr()
    assert output.out == (
        f"http://127.0.0.1:{9000 if ssh else 8123}/lab?token=secret\n"
    )
    assert "Notebook ready" in output.err
    assert "Press Ctrl+C" in output.err
    assert "\x1b" not in output.out + output.err


@pytest.mark.parametrize("marimo", [False, True])
def test_launch_opens_browser(marimo):
    process = worker_process()
    with (
        patch("qibocal_report.notebook.subprocess.Popen", return_value=process),
        patch("qibocal_report.notebook._wait_tunnel"),
        patch("qibocal_report.notebook.webbrowser.open", return_value=True) as browser,
        patch("qibocal_report.notebook.time.sleep", side_effect=KeyboardInterrupt),
        patch("qibocal_report.notebook.stop_process"),
    ):
        launch(NotebookOptions(marimo=marimo))
    query_key = "access_token" if marimo else "token"
    browser.assert_called_once_with(f"http://127.0.0.1:8123/lab?{query_key}=secret")


def test_launch_startup_failure_cleans_up():
    process = worker_process()
    process.stdout = io.StringIO("")
    with (
        patch("qibocal_report.notebook.subprocess.Popen", return_value=process),
        patch("qibocal_report.notebook.stop_process") as stop,
        pytest.raises(click.ClickException, match="exited before startup"),
    ):
        launch(NotebookOptions())
    stop.assert_called_once_with(process)


def test_stop_process_graceful():
    process = MagicMock()
    stop_process(process)
    process.stdin.close.assert_called_once()
    process.wait.assert_called_once_with(timeout=5)


def test_stop_process_escalates():
    process = MagicMock()
    process.wait.side_effect = [
        subprocess.TimeoutExpired("worker", 5),
        subprocess.TimeoutExpired("worker", 5),
        0,
    ]
    process.poll.return_value = None
    with patch("qibocal_report.notebook.os.killpg") as killpg:
        stop_process(process)
    assert killpg.call_count == 2


@pytest.mark.parametrize(
    "message",
    [
        "not-json",
        "[]",
        '{"port": 0, "token": "secret", "path": "/lab"}',
        '{"port": true, "token": "secret", "path": "/lab"}',
        '{"port": 8888, "token": "", "path": "/lab"}',
        '{"port": 8888, "token": "secret", "path": "//other-host"}',
    ],
)
def test_invalid_readiness(message):
    messages = queue.Queue()
    messages.put(message)
    with pytest.raises(click.ClickException, match="Invalid notebook startup response"):
        _wait_ready(MagicMock(), messages, time.monotonic() + 1)


def test_startup_timeout():
    with pytest.raises(click.ClickException, match="Timed out"):
        _wait_ready(MagicMock(), queue.Queue(), time.monotonic() - 1)


def test_tunnel_failure():
    process = MagicMock()
    process.poll.return_value = 255
    with pytest.raises(click.ClickException, match="exited during startup"):
        _wait_tunnel("http://127.0.0.1:1234", [process], time.monotonic() + 1)


def test_tunnel_wait_bypasses_proxies():
    process = MagicMock()
    process.poll.return_value = None
    with patch("qibocal_report.notebook.build_opener") as build_opener:
        _wait_tunnel("http://127.0.0.1:1234", [process], time.monotonic() + 1)
    assert build_opener.call_args.args[0].proxies == {}
    build_opener.return_value.open.assert_called_once()


def test_tunnel_wait_http_response(monkeypatch):
    requested = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requested.append(self.path)
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    process = MagicMock()
    process.poll.return_value = None
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:1")
    monkeypatch.setenv("no_proxy", "")
    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        _wait_tunnel(
            f"http://127.0.0.1:{server.server_port}/lab?token=secret",
            [process],
            time.monotonic() + 3,
        )
        thread.join(timeout=3)
        assert not thread.is_alive()
    assert requested == ["/lab?token=secret"]


def test_local_launcher_real_process_lifecycle(capsys):
    source = """
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, *args):
        pass

server = HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
print("QIBOCAL_NOTEBOOK_EVENT " + json.dumps({
    "kind": "node", "role": "access and compute",
    "identity": {"hostname": "local-test", "fqdn": "local-test.example"},
}), file=sys.stderr, flush=True)
print("QIBOCAL_NOTEBOOK_READY " + json.dumps({
    "host": "localhost", "port": server.server_port,
    "token": "test-token", "path": "/lab",
}), flush=True)
sys.stdin.read()
server.shutdown()
server.server_close()
"""
    opened = []

    def interrupt_after_ready(url):
        opened.append(url)
        raise KeyboardInterrupt

    with (
        patch("qibocal_report.notebook.Path.read_text", return_value=source),
        patch(
            "qibocal_report.notebook.webbrowser.open", side_effect=interrupt_after_ready
        ),
    ):
        launch(NotebookOptions(timeout=5))
    assert len(opened) == 1
    output = capsys.readouterr()
    assert output.out == opened[0] + "\n"
    assert "Access and compute node" in output.err
    assert "local-test" in output.err
    assert "FQDN" in output.err
    assert EVENT_PREFIX not in output.err
    assert READY_PREFIX not in output.err
    url = urlsplit(opened[0])
    assert url.query == "token=test-token"
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", url.port), timeout=1)
