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
    for command in ("connect", "add", "list", "update", "remove"):
        assert command in result.output
    result = CliRunner().invoke(main, ["notebook", "connect", "--help"])
    assert result.exit_code == 0
    for option in (
        "--ssh",
        "--queue",
        "--marimo",
        "--workdir",
        "--slurm",
        "--venv",
        "--subnet",
        "-n",
    ):
        assert option in result.output


def test_connection_file_xdg(tmp_path, monkeypatch):
    monkeypatch.delenv("QIBOCAL_REPORT_CONFIG_DIR")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert connection_file() == tmp_path / "qibocal" / "notebooks.json"
    assert not connection_file().parent.exists()


def test_connection_file_home(tmp_path, monkeypatch):
    monkeypatch.delenv("QIBOCAL_REPORT_CONFIG_DIR")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert connection_file() == tmp_path / ".config" / "qibocal" / "notebooks.json"


def test_cli_defaults():
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(main, ["notebook", "connect"])
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
                    "subnet": "192.0.2.0/24",
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
                "connect",
                "chip",
                "-q",
                "new",
                "--jupyter",
                "--interactive",
                "-w",
                "/data",
                "--timeout",
                "120",
                "--subnet",
                "192.168.0.0/24",
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
    assert options.subnet == "192.168.0.0/24"


def test_cli_short_options():
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(
            main,
            [
                "notebook",
                "connect",
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
        ('{"chip": {"subnet": "invalid"}}', "Invalid notebook options"),
        ('{"chip": {"subnet": 24}}', "Invalid notebook options"),
    ],
)
def test_invalid_connection(contents, error):
    connection_file().write_text(contents, encoding="utf-8")
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(main, ["notebook", "connect", "chip"])
    assert result.exit_code == 1
    assert error in result.output
    mock.assert_not_called()


def test_missing_connection():
    result = CliRunner().invoke(main, ["notebook", "connect", "missing"])
    assert result.exit_code == 1
    assert "Could not read" in result.output


@pytest.mark.parametrize("command", ["connect", "add"])
@pytest.mark.parametrize(
    "arguments",
    [
        ["--ssh", "'unterminated"],
        ["--ssh", "-p"],
        ["--slurm", "'unterminated"],
        ["--timeout", "0"],
        ["--timeout", "nan"],
        ["--subnet", "invalid"],
        ["--subnet", "192.168.0.0/33"],
        ["--subnet", "192.168.0.1/24"],
        ["--subnet", "2001:db8::/129"],
    ],
)
def test_invalid_cli_options(arguments, command):
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(
            main,
            ["notebook", command, *(["chip"] if command == "add" else []), *arguments],
        )
    assert result.exit_code != 0
    mock.assert_not_called()
    assert not connection_file().exists()


def test_add_help_references_connect():
    result = CliRunner().invoke(main, ["notebook", "add", "--help"])
    assert result.exit_code == 0
    assert "qibocal notebook connect --help" in result.output
    assert "--ssh" not in result.output
    assert "--timeout" not in result.output


def test_add_options_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path / "new-config"))
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(
            main,
            [
                "notebook",
                "add",
                "chip",
                "--ssh",
                "-p 2222 user@login",
                "-q",
                "chip",
                "--slurm",
                "--time=01:00:00",
                "-w",
                "~/runs",
                "--venv",
                "./env",
                "--marimo",
                "-n",
                "--timeout",
                "900",
                "--subnet",
                "2001:db8::/64",
            ],
        )
    assert result.exit_code == 0, result.output
    mock.assert_not_called()
    values = {
        "ssh": "-p 2222 user@login",
        "queue": "chip",
        "slurm": "--time=01:00:00",
        "workdir": "~/runs",
        "venv": "./env",
        "marimo": True,
        "no_interactive": True,
        "timeout": 900.0,
        "subnet": "2001:db8::/64",
    }
    assert json.loads(connection_file().read_text()) == {"chip": values}
    with patch("qibocal_report.notebook.launch") as mock:
        result = CliRunner().invoke(main, ["notebook", "connect", "chip"])
    assert result.exit_code == 0, result.output
    assert mock.call_args.args == (NotebookOptions(**values),)


def test_add_preserves_connections_and_explicit_defaults():
    connection_file().write_text('{"old": {"marimo": true}}\n', encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["notebook", "add", "new", "--jupyter", "--interactive", "--venv", "qibocal"],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(connection_file().read_text()) == {
        "old": {"marimo": True},
        "new": {"marimo": False, "no_interactive": False, "venv": "qibocal"},
    }


def test_add_interactive_defaults():
    result = CliRunner().invoke(main, ["notebook", "add"], input="local\n\n")
    assert result.exit_code == 0, result.output
    assert result.output.index("Connection name") < result.output.index(
        "Options to change"
    )
    assert "Default" in result.output
    assert json.loads(connection_file().read_text()) == {"local": {}}


def test_add_interactive_selected_options():
    result = CliRunner().invoke(
        main,
        ["notebook", "add"],
        input="chip\n1,2,3,4,5,6,7,8,9\nuser@login\nchip\n"
        "--time=01:00:00\n/data\n./env\ny\ny\n900\n192.168.0.0/24\n",
    )
    assert result.exit_code == 0, result.output
    assert load_options("chip", {}) == NotebookOptions(
        ssh="user@login",
        queue="chip",
        slurm="--time=01:00:00",
        workdir="/data",
        venv="./env",
        marimo=True,
        no_interactive=True,
        timeout=900,
        subnet="192.168.0.0/24",
    )


def test_add_interactive_invalid_selection_reprompts():
    result = CliRunner().invoke(
        main, ["notebook", "add"], input="chip\n0,10\nbad\n2,2\nchip\n"
    )
    assert result.exit_code == 0, result.output
    assert "Choose numbers between 1 and 9" in result.output
    assert json.loads(connection_file().read_text()) == {"chip": {"queue": "chip"}}


def test_add_options_without_name_prompts_only_for_name():
    result = CliRunner().invoke(main, ["notebook", "add", "--marimo"], input="chip\n")
    assert result.exit_code == 0, result.output
    assert "Options to change" not in result.output
    assert json.loads(connection_file().read_text()) == {"chip": {"marimo": True}}


def test_add_name_only_prompts_for_options():
    result = CliRunner().invoke(main, ["notebook", "add", "local"], input="\n")
    assert result.exit_code == 0, result.output
    assert "Connection name" not in result.output
    assert "Options to change" in result.output
    assert json.loads(connection_file().read_text()) == {"local": {}}


def test_add_duplicate_does_not_overwrite():
    text = '{"chip": {"queue": "old"}}\n'
    connection_file().write_text(text, encoding="utf-8")
    result = CliRunner().invoke(main, ["notebook", "add", "chip", "-q", "new"])
    assert result.exit_code == 1
    assert "already exists" in result.output
    assert connection_file().read_text() == text


@pytest.mark.parametrize("contents", ["{", "[]", '{"chip": []}'])
@pytest.mark.parametrize("command", ["add", "list"])
def test_invalid_registry_is_not_overwritten(contents, command):
    connection_file().write_text(contents, encoding="utf-8")
    result = CliRunner().invoke(
        main, ["notebook", command, *(["new", "--marimo"] if command == "add" else [])]
    )
    assert result.exit_code == 1
    assert connection_file().read_text() == contents


def test_add_write_failure_preserves_registry():
    text = '{"old": {}}\n'
    path = connection_file()
    path.write_text(text, encoding="utf-8")
    with patch("qibocal_report.notebook.Path.replace", side_effect=OSError("denied")):
        result = CliRunner().invoke(main, ["notebook", "add", "new", "--marimo"])
    assert result.exit_code == 1
    assert "Could not write" in result.output
    assert path.read_text() == text
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize("input", ["", "chip\n", "chip\n1\n"])
def test_add_aborted_prompt_does_not_write(input):
    result = CliRunner().invoke(main, ["notebook", "add"], input=input)
    assert result.exit_code != 0
    assert not connection_file().exists()


def test_add_empty_name():
    result = CliRunner().invoke(main, ["notebook", "add", " ", "--marimo"])
    assert result.exit_code == 1
    assert "must not be empty" in result.output
    assert not connection_file().exists()


def test_update_preserves_unspecified_settings():
    values = {
        "ssh": "user@login",
        "queue": "old",
        "marimo": True,
        "no_interactive": True,
        "subnet": "192.0.2.0/24",
    }
    connection_file().write_text(
        json.dumps({"chip": values, "other": {"venv": "custom"}}),
        encoding="utf-8",
    )
    with patch("qibocal_report.notebook.launch") as launch:
        result = CliRunner().invoke(
            main,
            [
                "notebook",
                "update",
                "chip",
                "-q",
                "new",
                "--jupyter",
                "--interactive",
                "--subnet",
                "192.168.0.0/24",
            ],
        )
    assert result.exit_code == 0, result.output
    assert "Updated notebook connection 'chip'" in result.output
    launch.assert_not_called()
    values.update(
        queue="new", marimo=False, no_interactive=False, subnet="192.168.0.0/24"
    )
    assert json.loads(connection_file().read_text()) == {
        "chip": values,
        "other": {"venv": "custom"},
    }
    assert load_options("chip", {}) == NotebookOptions(**values)


@pytest.mark.parametrize("named", [False, True])
def test_update_interactive_current_values(named):
    connection_file().write_text(
        '{"chip": {"queue": "old", "marimo": true, "timeout": 900}}',
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        main,
        ["notebook", "update", *(["chip"] if named else [])],
        input=("" if named else "chip\n") + "2,6,8\nnew\nn\n\n",
    )
    assert result.exit_code == 0, result.output
    assert "Current" in result.output
    assert "old" in result.output
    assert "Enter keeps current values" in result.output
    assert json.loads(connection_file().read_text()) == {
        "chip": {"queue": "new", "marimo": False, "timeout": 900.0}
    }


def test_update_options_without_name():
    connection_file().write_text('{"chip": {"queue": "old"}}', encoding="utf-8")
    result = CliRunner().invoke(
        main, ["notebook", "update", "--marimo"], input="chip\n"
    )
    assert result.exit_code == 0, result.output
    assert "Options to change" not in result.output
    assert json.loads(connection_file().read_text()) == {
        "chip": {"queue": "old", "marimo": True}
    }


@pytest.mark.parametrize("input", ["", "2\n"])
def test_update_aborted_prompt_preserves_registry(input):
    text = '{"chip": {"queue": "old"}}\n'
    connection_file().write_text(text, encoding="utf-8")
    result = CliRunner().invoke(main, ["notebook", "update", "chip"], input=input)
    assert result.exit_code != 0
    assert connection_file().read_text() == text


def test_update_interactive_no_changes():
    connection_file().write_text('{"chip": {"queue": "old"}}', encoding="utf-8")
    result = CliRunner().invoke(main, ["notebook", "update", "chip"], input="\n")
    assert result.exit_code == 0, result.output
    assert json.loads(connection_file().read_text()) == {"chip": {"queue": "old"}}


@pytest.mark.parametrize(
    "arguments",
    [
        ["--ssh", "'unterminated"],
        ["--ssh", "-p"],
        ["--slurm", "'unterminated"],
        ["--timeout", "0"],
        ["--subnet", "invalid"],
    ],
)
def test_update_invalid_options_preserves_registry(arguments):
    text = '{"chip": {"queue": "old"}}\n'
    connection_file().write_text(text, encoding="utf-8")
    result = CliRunner().invoke(main, ["notebook", "update", "chip", *arguments])
    assert result.exit_code != 0
    assert connection_file().read_text() == text


@pytest.mark.parametrize("other", [False, True])
def test_remove_immediately_preserves_other_connections(other):
    connections = {"chip": {"queue": "old"}}
    if other:
        connections["other"] = {"venv": "custom"}
    connection_file().write_text(json.dumps(connections), encoding="utf-8")
    with patch("qibocal_report.notebook.launch") as launch:
        result = CliRunner().invoke(main, ["notebook", "remove", "chip"])
    assert result.exit_code == 0, result.output
    assert "Removed notebook connection 'chip'" in result.output
    launch.assert_not_called()
    del connections["chip"]
    assert json.loads(connection_file().read_text()) == connections


@pytest.mark.parametrize(
    "arguments",
    [["update", "missing"], ["update", "missing", "--marimo"], ["remove", "missing"]],
)
@pytest.mark.parametrize("exists", [False, True])
def test_connection_mutation_requires_existing_name(arguments, exists):
    text = '{"chip": {}}\n'
    if exists:
        connection_file().write_text(text, encoding="utf-8")
    result = CliRunner().invoke(main, ["notebook", *arguments])
    assert result.exit_code == 1
    assert ("not found" if exists else "Could not read") in result.output
    if exists:
        assert connection_file().read_text() == text
    else:
        assert not connection_file().exists()


@pytest.mark.parametrize("command", ["update", "remove"])
@pytest.mark.parametrize("contents", ["{", "[]", '{"chip": []}'])
def test_mutation_invalid_registry_is_not_overwritten(command, contents):
    connection_file().write_text(contents, encoding="utf-8")
    result = CliRunner().invoke(
        main,
        ["notebook", command, "chip", *(["--marimo"] if command == "update" else [])],
    )
    assert result.exit_code == 1
    assert connection_file().read_text() == contents


@pytest.mark.parametrize("command", ["update", "remove"])
def test_mutation_write_failure_preserves_registry(command):
    text = '{"chip": {}}\n'
    path = connection_file()
    path.write_text(text, encoding="utf-8")
    with patch("qibocal_report.notebook.Path.replace", side_effect=OSError("denied")):
        result = CliRunner().invoke(
            main,
            [
                "notebook",
                command,
                "chip",
                *(["--marimo"] if command == "update" else []),
            ],
        )
    assert result.exit_code == 1
    assert "Could not write" in result.output
    assert path.read_text() == text
    assert list(path.parent.iterdir()) == [path]


def test_list_rich_literal_values():
    connection_file().write_text(
        json.dumps({"[red]chip[/red]": {"workdir": "/[blue]data[/blue]"}, "local": {}}),
        encoding="utf-8",
    )
    result = CliRunner().invoke(main, ["notebook", "list"], env={"COLUMNS": "120"})
    assert result.exit_code == 0, result.output
    for text in (
        "Notebook connections",
        "Connection",
        "Configured options",
        "[red]chip[/red]",
        "/[blue]data[/blue]",
        "local",
        "(defaults)",
    ):
        assert text in result.output
    assert "\x1b[" not in result.output


def test_list_empty_does_not_create_file():
    result = CliRunner().invoke(main, ["notebook", "list"])
    assert result.exit_code == 0, result.output
    assert "No notebook connections registered" in result.output
    assert not connection_file().exists()


@pytest.mark.parametrize(
    "contents", [b'{"chip": {}}\r\n', b'{ "local" : {} }', b"invalid"]
)
def test_list_raw_verbatim(contents):
    connection_file().write_bytes(contents)
    result = CliRunner().invoke(main, ["notebook", "list", "--raw"])
    assert result.exit_code == 0, result.output
    assert result.stdout_bytes == contents


def test_list_raw_missing_file():
    result = CliRunner().invoke(main, ["notebook", "list", "--raw"])
    assert result.exit_code == 1
    assert "Could not read" in result.output
    assert not connection_file().exists()


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
        subnet="192.168.0.0/24" if slurm else None,
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
    assert remote_options["subnet"] == ("192.168.0.0/24" if slurm else None)
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
