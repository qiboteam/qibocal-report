import json
import queue
import shlex
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from qibocal_report import report_worker
from qibocal_report.cli import main
from qibocal_report.remote import (
    RemoteServerOptions,
    launch,
    load_options,
    register,
    ssh_base,
    worker_command,
    worker_source,
)


def test_defaults_are_the_documented_ones():
    options = load_options({"ssh": "me@node"})
    assert options.venv == "qibocal"
    assert options.install == "qibocal-report"
    assert options.directory is None, "the shared directory of the remote host"
    assert options.timeout == 300.0
    assert options.auth is False


def test_unset_options_do_not_override_the_defaults():
    options = load_options({"ssh": "me@node", "venv": None, "workdir": None})
    assert options.venv == "qibocal"
    assert options.workdir is None


@pytest.mark.parametrize(
    "values",
    [
        {"ssh": ""},
        # The destination comes last, never an option, or ssh would read the
        # rest of the line as a remote command.
        {"ssh": "me@node -4"},
        {"ssh": "me@node", "venv": ""},
        {"ssh": "me@node", "timeout": 0},
        {"ssh": "me@node", "install": "'unterminated"},
        {"ssh": "me@node", "unknown": "value"},
    ],
)
def test_invalid_options_are_refused(values):
    with pytest.raises(click.ClickException, match="Invalid remote server options"):
        load_options(values)


def test_the_worker_carries_the_notebook_worker_along():
    source = worker_source()
    assert source.startswith("SHARED_SOURCE = ")
    compile(source, "shipped.py", "exec")
    # The first line restores the notebook worker verbatim, which is how the
    # remote host gets `ensure_environment` without the package installed.
    shared = (
        Path(report_worker.__file__).with_name("notebook_worker.py").read_text("utf-8")
    )
    namespace = {}
    exec(source.split("\n", 1)[0], namespace)
    assert namespace["SHARED_SOURCE"] == shared


def test_the_shipped_worker_runs_on_a_bare_python(tmp_path):
    """The remote host has an interpreter and nothing else of ours."""
    script = tmp_path / "shipped.py"
    script.write_text(worker_source(), encoding="utf-8")
    result = subprocess.run(
        [
            "python3",
            "-u",
            str(script),
            json.dumps({"directory": str(tmp_path / "absent"), "timeout": 5}),
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 1
    assert "No report directory" in result.stderr


def test_the_ssh_command_keeps_the_destination_last():
    options = load_options(
        {
            "ssh": "-J bastion me@node",
            "directory": "/shared/runs",
            "venv": "chip",
            "auth": True,
        }
    )
    command = worker_command(options)
    assert command[:2] == ["ssh", "-J"]
    assert command[-2] == "me@node"
    remote = shlex.split(command[-1])
    assert remote[:3] == ["python3", "-u", "-c"]
    assert json.loads(remote[4]) == {
        "directory": "/shared/runs",
        "venv": "chip",
        "workdir": None,
        "install": "qibocal-report",
        "upgrade": False,
        "auth": True,
        "timeout": 300.0,
    }


def test_the_tunnel_survives_an_idle_connection():
    options = shlex.join(ssh_base([]))
    assert "ServerAliveInterval=30" in options
    assert "ExitOnForwardFailure=yes" in options


def test_the_tunnelled_address_is_registered(monkeypatch):
    recorded = {}
    monkeypatch.setattr(
        "qibocal_report.config.add_server",
        lambda **values: recorded.update(values) or values,
    )
    register(
        "http://127.0.0.1:41234",
        load_options({"ssh": "me@node", "directory": "/shared/runs"}),
        "me@node",
    )
    assert recorded["url"] == "http://127.0.0.1:41234"
    assert recorded["name"] == "me@node-runs"
    assert "/shared/runs" in recorded["description"]
    assert "me@node" in recorded["description"]


def test_an_unregisterable_server_is_reported(monkeypatch):
    def refuse(**_):
        raise OSError("read-only configuration")

    monkeypatch.setattr("qibocal_report.config.add_server", refuse)
    with pytest.raises(click.ClickException, match="Could not register"):
        register("http://127.0.0.1:1", load_options({"ssh": "me@node"}), "me@node")


def test_a_worker_that_dies_before_readiness_is_reported():
    process = MagicMock()
    process.poll.return_value = 255
    process.stdout = iter(())
    process.stderr = iter(())
    with patch("qibocal_report.remote.subprocess.Popen", return_value=process):
        with pytest.raises(click.ClickException, match="Report launcher exited"):
            launch(load_options({"ssh": "me@node", "timeout": 5}))


def test_a_nonsensical_readiness_response_is_refused(monkeypatch):
    monkeypatch.setattr(
        "qibocal_report.remote._wait_message",
        lambda *_args, **_kwargs: {"port": 0},
    )
    process = MagicMock()
    process.stdout = iter(())
    process.stderr = iter(())
    with patch("qibocal_report.remote.subprocess.Popen", return_value=process):
        with pytest.raises(click.ClickException, match="Invalid report startup"):
            launch(load_options({"ssh": "me@node", "timeout": 5}))


def test_the_cli_delegates_to_the_remote_launcher(tmp_path):
    captured = {}

    def record(options: RemoteServerOptions):
        captured["options"] = options

    with patch("qibocal_report.remote.launch", record):
        result = CliRunner().invoke(
            main,
            [
                "report",
                "server",
                "/shared/runs",
                "--ssh",
                "me@node",
                "--venv",
                "chip",
                "--workdir",
                "/shared",
                "--install",
                "qibocal-report==0.1.0",
                "--timeout",
                "60",
                "--auth",
            ],
        )
    assert result.exit_code == 0, result.output
    options = captured["options"]
    assert options.ssh == "me@node"
    assert options.directory == "/shared/runs"
    assert options.venv == "chip"
    assert options.workdir == "/shared"
    assert options.install == "qibocal-report==0.1.0"
    assert options.timeout == 60.0
    assert options.auth is True


def test_a_remote_directory_is_not_checked_here():
    """`/shared/runs` exists on the other machine, not on this one."""
    with patch("qibocal_report.remote.launch") as launcher:
        result = CliRunner().invoke(
            main, ["report", "server", "/definitely/not/here", "--ssh", "me@node"]
        )
    assert result.exit_code == 0, result.output
    launcher.assert_called_once()


def test_a_local_directory_is_still_checked():
    result = CliRunner().invoke(main, ["report", "server", "/definitely/not/here"])
    assert result.exit_code != 0
    assert "does not exist" in result.output


@pytest.mark.parametrize(
    "flag,value",
    [
        ("--venv", "chip"),
        ("--workdir", "/shared"),
        ("--install", "pkg"),
        ("--timeout", "60"),
    ],
)
def test_remote_flags_need_a_destination(tmp_path, flag, value):
    result = CliRunner().invoke(main, ["report", "server", str(tmp_path), flag, value])
    assert result.exit_code != 0
    assert "only applies together with --ssh" in result.output


def test_the_worker_refuses_options_that_are_not_an_object(capsys):
    with patch("sys.argv", ["worker", json.dumps([1, 2])]):
        assert report_worker.main() == 1
    assert "must be a JSON object" in capsys.readouterr().err


def test_the_worker_rejects_an_impossible_timeout():
    with pytest.raises(report_worker.WorkerError, match="finite and positive"):
        report_worker.run({"timeout": 0})


def test_the_worker_needs_a_package_to_install(tmp_path):
    with pytest.raises(report_worker.WorkerError, match="at least one package"):
        report_worker.run({"directory": str(tmp_path), "install": "   ", "timeout": 5})


def test_the_worker_reads_the_report_directory_on_its_own_host(tmp_path):
    with pytest.raises(report_worker.WorkerError, match="No report directory"):
        report_worker.run({"directory": str(tmp_path / "absent"), "timeout": 5})


def test_the_worker_names_the_environment_as_the_notebooks_do(monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/cache")
    assert report_worker.environment_path("qibocal") == Path(
        "/tmp/cache/qibocal/envs/qibocal"
    )
    assert report_worker.environment_path("/opt/envs/chip") == Path("/opt/envs/chip")


def test_an_environment_without_qibocal_is_filled_in(tmp_path):
    """An environment created for something else still gets the report package."""
    environment = tmp_path / "env"
    (environment / "bin").mkdir(parents=True)
    python = environment / "bin" / "python"
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(0o755)
    runtime = MagicMock()
    executable = environment / "bin" / "qibocal"

    def install(command, capture=False):
        if capture:
            return "true"
        executable.write_text("#!/bin/sh\n", encoding="utf-8")
        executable.chmod(0o755)
        return ""

    runtime.command.side_effect = install
    assert (
        report_worker.ensure_qibocal(runtime, environment, ["qibocal-report"])
        == executable
    )


def test_an_environment_that_stays_empty_is_reported(tmp_path):
    environment = tmp_path / "env"
    (environment / "bin").mkdir(parents=True)
    python = environment / "bin" / "python"
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(0o755)
    runtime = MagicMock()
    runtime.command.return_value = "true"
    with pytest.raises(report_worker.WorkerError, match="no executable bin/qibocal"):
        report_worker.ensure_qibocal(runtime, environment, ["wrong-package"])


def test_an_answering_server_ends_the_wait():
    runtime = MagicMock()
    process = MagicMock()
    process.poll.return_value = None
    opener = MagicMock()
    with patch("qibocal_report.report_worker.build_opener", return_value=opener):
        report_worker.wait_http(runtime, "http://127.0.0.1:1/", process)
    opener.open.assert_called_once()


def test_a_server_that_exits_ends_the_wait_too():
    runtime = MagicMock()
    process = MagicMock()
    process.poll.return_value = 1
    process.returncode = 1
    with pytest.raises(report_worker.WorkerError, match="exited before startup"):
        report_worker.wait_http(runtime, "http://127.0.0.1:1/", process)


def test_the_readiness_line_names_the_port(capsys):
    report_worker.announce(41234)
    out = capsys.readouterr().out
    assert out.startswith(report_worker.READY_PREFIX)
    assert json.loads(out[len(report_worker.READY_PREFIX) :]) == {"port": 41234}


def test_the_launcher_and_the_worker_agree_on_the_prefix():
    from qibocal_report.remote import READY_PREFIX

    assert READY_PREFIX == report_worker.READY_PREFIX


def test_waiting_for_a_message_gives_up(monkeypatch):
    from qibocal_report.notebook import _wait_message

    with pytest.raises(click.ClickException, match="Timed out waiting for report"):
        _wait_message(MagicMock(), queue.Queue(), time.monotonic() - 1, "report")


def test_the_name_and_the_registration_travel_with_the_options():
    captured = {}
    with patch("qibocal_report.remote.launch", lambda options: captured.update(o=options)):
        result = CliRunner().invoke(
            main,
            ["report", "server", "--ssh", "me@node", "--name", "Lab", "--no-register"],
        )
    assert result.exit_code == 0, result.output
    assert captured["o"].name == "Lab"
    assert captured["o"].registered is False
    assert captured["o"].directory is None


def test_the_worker_is_not_told_how_the_server_is_registered():
    command = worker_command(
        load_options({"ssh": "me@node", "name": "Lab", "registered": False})
    )
    remote = shlex.split(command[-1])
    options = json.loads(remote[-1])
    assert "name" not in options
    assert "registered" not in options
    assert options["directory"] is None


def test_a_server_that_is_not_to_be_registered_is_left_alone(monkeypatch):
    def refuse(**_):
        raise AssertionError("add_server must not be called")

    monkeypatch.setattr("qibocal_report.config.add_server", refuse)
    register("http://127.0.0.1:1", load_options({"ssh": "me@node", "registered": False}), "me@node")


def test_the_given_name_wins_over_the_generated_one(monkeypatch):
    recorded = {}
    monkeypatch.setattr(
        "qibocal_report.config.add_server",
        lambda **values: recorded.update(values) or values,
    )
    register("http://127.0.0.1:1", load_options({"ssh": "me@node", "name": "Lab"}), "me@node")
    assert recorded["name"] == "Lab"
    assert "shared reports directory" in recorded["description"]


def test_the_worker_and_the_package_agree_on_the_shared_directory(monkeypatch, tmp_path):
    from qibocal_report import config

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    monkeypatch.delenv("QIBOCAL_REPORT_DATA_DIR", raising=False)
    assert report_worker.reports_path() == config.get_reports_dir(create=False)
    monkeypatch.setenv("QIBOCAL_REPORT_DATA_DIR", str(tmp_path / "data"))
    assert report_worker.reports_path() == config.get_reports_dir(create=False)


def test_the_worker_creates_the_shared_directory_when_none_is_named(monkeypatch, tmp_path):
    monkeypatch.setenv("QIBOCAL_REPORT_DATA_DIR", str(tmp_path / "data"))
    directory = report_worker.reports_directory(None)
    assert directory == tmp_path / "data" / "reports"
    assert directory.is_dir()
    # A named directory, on the other hand, has to be there already.
    with pytest.raises(report_worker.WorkerError, match="No report directory"):
        report_worker.reports_directory(str(tmp_path / "absent"))


def test_the_worker_starts_from_a_temporary_directory_by_default(monkeypatch, tmp_path):
    """Nothing is written where the server starts, so the home folder is spared."""
    monkeypatch.setenv("QIBOCAL_REPORT_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("TMPDIR", str(tmp_path / "tmp"))
    (tmp_path / "tmp").mkdir()
    import tempfile

    tempfile.tempdir = None
    seen = {}

    def stop_here(*_args, **_kwargs):
        seen["cwd"] = Path.cwd()
        raise report_worker.Stopped()

    monkeypatch.setattr(report_worker, "ensure_qibocal", stop_here)
    try:
        report_worker.run({"timeout": 5})
    finally:
        tempfile.tempdir = None
    assert seen["cwd"].parent == (tmp_path / "tmp").resolve()
    assert seen["cwd"].name.startswith("qibocal-report-")


def test_an_update_travels_to_the_worker_and_puts_the_package_back_by_force():
    options = load_options({"ssh": "me@node", "upgrade": True})
    assert options.upgrade is True
    assert load_options({"ssh": "me@node"}).upgrade is False
    from qibocal_report.remote import worker_command

    command = worker_command(options)
    assert '"upgrade": true' in command[-1]

    from qibocal_report import report_worker

    first, second = report_worker.upgrade_commands("/env/bin/python", ["qibocal-report"], seeded=True)
    assert first[-4:] == ["--upgrade", "--force-reinstall", "--no-deps", "qibocal-report"]
    assert second[-2:] == ["--upgrade", "qibocal-report"]
    assert first[:4] == ["/env/bin/python", "-m", "pip", "install"]


def test_the_cli_passes_upgrade_only_with_a_destination():
    captured = {}
    with patch("qibocal_report.remote.launch", lambda options: captured.update(o=options)):
        result = CliRunner().invoke(main, ["report", "server", "--ssh", "me@node", "--upgrade"])
    assert result.exit_code == 0, result.output
    assert captured["o"].upgrade is True
    alone = CliRunner().invoke(main, ["report", "server", "--upgrade"])
    assert alone.exit_code != 0 and "only applies together with --ssh" in alone.output
