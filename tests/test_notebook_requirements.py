"""The requirements of a notebook connection, enforced in its kernel environment."""

import json
import shlex
from unittest.mock import MagicMock

import click
import pytest
from click.testing import CliRunner

from qibocal_report.cli import main
from qibocal_report.remote import notebook, notebook_worker as worker


def runtime_with_pip(installed):
    """A runtime whose environment has pip, recording each install's requirements."""
    runtime = MagicMock()

    def command(arguments, capture=False):
        if capture:
            return "true"
        installed.append(open(arguments[-1], encoding="utf-8").read())
        return ""

    runtime.command.side_effect = command
    return runtime


def test_requirements_compare_line_by_line_without_blanks_or_comments():
    assert worker.normalize_requirements("  numpy\n\n# a comment\nscipy>=1.11 \n") == "numpy\nscipy>=1.11\n"
    assert worker.normalize_requirements("") == ""
    assert worker.normalize_requirements(None) == ""
    assert worker.normalize_requirements("# only a comment\n") == ""


def test_new_requirements_are_installed_on_top_once_and_recorded(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "event", lambda *args, **kwargs: None)
    installed = []
    runtime = runtime_with_pip(installed)
    python = str(tmp_path / "bin" / "python")

    worker.apply_requirements(runtime, tmp_path, python, "numpy\n")
    assert installed == ["numpy\n"]
    assert (tmp_path / worker.REQUIREMENTS_MARKER).read_text() == "numpy\n"
    install = [call for call in runtime.command.call_args_list if not call.kwargs.get("capture")][0].args[0]
    assert install[:4] == [python, "-m", "pip", "install"] and install[4] == "-r"
    assert "--force-reinstall" not in install and "--upgrade" not in install, "on top, not a rebuild"
    assert not any(path.name.endswith(".pending") for path in tmp_path.iterdir())

    worker.apply_requirements(runtime, tmp_path, python, "numpy\n\n# same\n")
    assert installed == ["numpy\n"], "the same requirements again: nothing to do"

    worker.apply_requirements(runtime, tmp_path, python, "numpy\nscipy\n")
    assert installed == ["numpy\n", "numpy\nscipy\n"]
    assert (tmp_path / worker.REQUIREMENTS_MARKER).read_text() == "numpy\nscipy\n"


def test_no_requirements_any_more_removes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "event", lambda *args, **kwargs: None)
    (tmp_path / worker.REQUIREMENTS_MARKER).write_text("numpy\n")
    runtime = runtime_with_pip([])
    worker.apply_requirements(runtime, tmp_path, "python", None)
    runtime.command.assert_not_called()
    assert not (tmp_path / worker.REQUIREMENTS_MARKER).exists()


def test_a_failed_install_stops_the_session_and_records_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "event", lambda *args, **kwargs: None)
    runtime = MagicMock()
    runtime.command.side_effect = lambda arguments, capture=False: "true" if capture else (_ for _ in ()).throw(
        worker.WorkerError("Command failed (1)")
    )
    with pytest.raises(worker.WorkerError):
        worker.apply_requirements(runtime, tmp_path, "python", "no-such-package\n")
    assert not (tmp_path / worker.REQUIREMENTS_MARKER).exists(), "tried again next session"
    assert not any(path.name.endswith(".pending") for path in tmp_path.iterdir())


def test_requirements_are_a_connection_option_from_text_or_a_file(tmp_path, monkeypatch):
    options = notebook.load_options(None, {"requirements": "numpy\nscipy\n"})
    assert options.requirements == "numpy\nscipy\n"
    assert options.model_dump()["requirements"] == "numpy\nscipy\n", "it reaches the worker"

    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path / "config"))
    (tmp_path / "config").mkdir()
    listing = tmp_path / "requirements.txt"
    listing.write_text("pandas\n")
    result = CliRunner().invoke(main, ["notebook", "add", "lab", "--ssh", "lab", "--requirements", f"@{listing}"])
    assert result.exit_code == 0, result.output
    assert notebook.load_connections()["lab"]["requirements"] == "pandas\n", "kept in notebooks.json"
    missing = CliRunner().invoke(main, ["notebook", "add", "other", "--requirements", "@/no/such/file"])
    assert missing.exit_code != 0 and "Could not read" in missing.output


def test_a_rebuild_removes_the_environment_and_makes_it_in_one_install(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "event", lambda *args, **kwargs: None)
    monkeypatch.setattr(worker, "cache_home", lambda: tmp_path / "cache")
    environment = tmp_path / "envs" / "chip"
    (environment / "lib").mkdir(parents=True)
    (environment / "pyvenv.cfg").write_text("home = /usr/bin\n")
    (environment / "lib" / "leftover.py").write_text("")
    installs = []

    def create(runtime, path, packages=()):
        assert not (path / "lib" / "leftover.py").exists(), "the old environment is gone first"
        listing = packages[packages.index("-r") + 1]
        installs.append((list(packages[:-1]), open(listing, encoding="utf-8").read()))
        path.mkdir(parents=True)
        return path / "bin" / "python"

    monkeypatch.setattr(worker, "create_environment", create)
    worker.rebuild_environment(MagicMock(), {"venv": str(environment), "requirements": "numpy\n# fits\nscipy\n"})
    assert installs == [(["qibocal", "-r"], "numpy\nscipy\n")], "qibocal and the requirements, together"
    assert (environment / worker.REQUIREMENTS_MARKER).read_text() == "numpy\nscipy\n", "recorded as installed"
    assert not any(path.name.endswith(".pending") for path in environment.parent.iterdir())


def test_uv_makes_and_fills_environments_when_there_is_one(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "event", lambda *args, **kwargs: None)
    monkeypatch.setitem(worker._UV, "path", "/tools/uv")
    runtime = MagicMock()
    path = tmp_path / "env"
    worker.create_environment(runtime, path, ["qibocal", "-r", "requirements.txt"])
    venv, install = (call.args[0] for call in runtime.command.call_args_list)
    assert venv[:3] == ["/tools/uv", "venv", "--seed"], "seeded: pip is still there for whoever uses it"
    assert install == ["/tools/uv", "pip", "install", "--python", str(path / "bin" / "python"),
                       "qibocal", "-r", "requirements.txt"]
    upgrade = worker.install_command(runtime, "/env/bin/python", ["pkg"], upgrade=True, reinstall=True, no_deps=True)
    assert upgrade == ["/tools/uv", "pip", "install", "--python", "/env/bin/python",
                       "--upgrade", "--no-deps", "--reinstall", "pkg"]


def test_without_uv_the_worker_installs_none_when_told_not_to(monkeypatch):
    monkeypatch.delitem(worker._UV, "path")
    monkeypatch.setenv("QIBOCAL_NO_UV", "1")
    runtime = MagicMock()
    assert worker.find_uv(runtime) is None
    runtime.command.assert_not_called()


def test_a_rebuild_refuses_what_is_not_a_virtual_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(worker, "event", lambda *args, **kwargs: None)
    monkeypatch.setattr(worker, "cache_home", lambda: tmp_path / "cache")
    folder = tmp_path / "precious"
    folder.mkdir()
    (folder / "thesis.tex").write_text("")
    with pytest.raises(worker.WorkerError, match="not a Python virtual environment"):
        worker.rebuild_environment(MagicMock(), {"venv": str(folder)})
    assert (folder / "thesis.tex").exists()
    with pytest.raises(worker.WorkerError, match="must be separate"):
        worker.rebuild_environment(MagicMock(), {"venv": str(tmp_path / "cache" / "qibocal" / "envs" / "jupyter")})


def test_rebuild_is_a_command_that_runs_the_worker_in_rebuild_mode(monkeypatch):
    captured = {}
    monkeypatch.setattr(notebook, "rebuild", lambda options: captured.update(options=options))
    result = CliRunner().invoke(main, ["notebook", "rebuild", "--ssh", "lab", "--venv", "chip", "--requirements", "numpy"])
    assert result.exit_code == 0, result.output
    assert captured["options"].venv == "chip" and captured["options"].requirements == "numpy"
    command, _, destination = notebook._worker_command(captured["options"], _rebuild=True)
    assert destination == "lab" and '"_rebuild": true' in command[-1]


def test_a_slurm_connection_regenerates_on_the_access_node_unless_asked(monkeypatch):
    rebuilt, submitted = [], []
    monkeypatch.setattr(worker, "rebuild_environment", lambda runtime, options: rebuilt.append(options))
    monkeypatch.setattr(worker, "srun_command", lambda options, nested: submitted.append(nested) or (["true"], ""))
    monkeypatch.setattr(worker, "event", lambda *args, **kwargs: None)
    runtime = MagicMock()
    runtime.spawn.return_value = (MagicMock(returncode=0), MagicMock(get=MagicMock(return_value=None)))
    worker.run_rebuild(runtime, {"queue": "chip"}, scheduled=True)
    assert rebuilt and not submitted, "the access node: nothing waits in the queue"
    rebuilt.clear()
    worker.run_rebuild(runtime, {"queue": "chip", "rebuild_on_compute": True}, scheduled=True)
    assert submitted and not rebuilt, "a computing node, through srun, when asked"


def test_a_requirement_line_names_its_distribution():
    assert worker.requirement_name("Qibocal[extra]>=0.2") == "qibocal"
    assert worker.requirement_name("qibocal @ git+ssh://git@github.com/qiboteam/qibocal.git@protodev") == "qibocal"
    assert worker.requirement_name("git+https://github.com/qiboteam/qibocal-widgets.git#egg=qibocal_widgets") == "qibocal-widgets"
    assert worker.requirement_name("git+https://github.com/x/y.git") is None, "a bare URL names nothing we can read"
    assert worker.requirement_name("--index-url https://example.org") is None
    assert worker.requirement_name("-e ./local") is None


def test_explicit_requirements_override_the_defaults_and_the_dependencies(tmp_path, monkeypatch):
    monkeypatch.setitem(worker._UV, "path", "/tools/uv")
    wanted = "qibocal @ git+ssh://git@github.com/qiboteam/qibocal.git@protodev\nqibocal-widgets==0.0.1\n--index-url https://pypi.org/simple\n"
    arguments, files = worker.requirement_arguments(MagicMock(), tmp_path, "chip", wanted, defaults=("qibocal",))
    assert "qibocal" not in arguments, "the default qibocal yields to the one asked for"
    listing = arguments[arguments.index("-r") + 1]
    override = arguments[arguments.index("--override") + 1]
    assert open(listing, encoding="utf-8").read() == wanted
    assert open(override, encoding="utf-8").read().splitlines() == [
        "qibocal @ git+ssh://git@github.com/qiboteam/qibocal.git@protodev", "qibocal-widgets==0.0.1"
    ], "what they say of a package holds for its dependants too; options are not overrides"
    assert len(files) == 2

    kept, _ = worker.requirement_arguments(MagicMock(), tmp_path, "other", "numpy\n", defaults=("qibocal",))
    assert kept[0] == "qibocal", "a default the requirements do not name stays"

    monkeypatch.setitem(worker._UV, "path", None)
    plain, _ = worker.requirement_arguments(MagicMock(), tmp_path, "pip", wanted, defaults=("qibocal",))
    assert "--override" not in plain, "pip has no overrides"


def test_the_reports_folder_is_a_connection_option_exported_to_the_session(tmp_path, monkeypatch):
    options = notebook.load_options(None, {"reports": "reports"})
    assert options.model_dump()["reports"] == "reports", "it reaches the worker"
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path / "config"))
    (tmp_path / "config").mkdir()
    result = CliRunner().invoke(main, ["notebook", "add", "lab", "--ssh", "lab", "--reports", "calibration"])
    assert result.exit_code == 0, result.output
    assert notebook.load_connections()["lab"]["reports"] == "calibration"
    assert worker.REPORTS_VARIABLE == "QIBOCAL_REPORTS_DIR"


def test_a_remote_execution_connection_travels_with_the_session(tmp_path, monkeypatch):
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path / "config"))
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "remotes.json").write_text(json.dumps({"version": 1, "connections": {"lab": {"ssh": "me@login", "queue": "qpu"}}}))
    options = notebook.load_options(None, {"ssh": "login", "remote": "lab"})
    command, _, _ = notebook._worker_command(options)
    shipped = json.loads(shlex.split(command[-1])[-1])
    assert shipped["_remote_connection"] == {"lab": {"ssh": "me@login", "queue": "qpu"}}, "the entry itself, not just its name"
    with pytest.raises(click.ClickException, match="No remote execution connection 'nope'"):
        notebook._worker_command(notebook.load_options(None, {"remote": "nope"}))


def test_the_worker_writes_the_connection_where_the_notebook_runs_and_only_when_it_differs(tmp_path, monkeypatch):
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path))
    remotes = tmp_path / "remotes.json"
    remotes.write_text(json.dumps({"version": 1, "connections": {"other": {"ssh": "x"}}}))
    assert worker.install_remote_connection({"lab": {"queue": "qpu"}}) == "lab"
    assert json.loads(remotes.read_text()) == {"version": 1, "connections": {"other": {"ssh": "x"}, "lab": {"queue": "qpu"}}}
    stamp = remotes.stat().st_mtime_ns
    worker.install_remote_connection({"lab": {"queue": "qpu"}})
    assert remotes.stat().st_mtime_ns == stamp, "the same entry: the file is left untouched"
    remotes.write_text(json.dumps({"version": 2}))
    with pytest.raises(worker.WorkerError, match="another format"):
        worker.install_remote_connection({"lab": {}})
    assert worker.REMOTE_VARIABLE == "QIBOCAL_WIDGETS_CONNECTION"


def test_a_registered_connection_has_its_own_environment_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path))
    for name, venv in (("tuna", None), ("QW5Q platinum / v2", None), ("named", "shared")):
        CliRunner().invoke(main, ["notebook", "add", name, "--ssh", "lab", *(["--venv", venv] if venv else [])])
    assert notebook.load_options("tuna", {}).venv == "tuna"
    assert notebook.load_options("QW5Q platinum / v2", {}).venv == "QW5Q-platinum-v2", "safe for a folder"
    assert notebook.load_options("named", {}).venv == "shared", "one it names is kept"
    assert notebook.load_options("tuna", {"venv": "other"}).venv == "other", "the command line still wins"
    assert notebook.load_options(None, {}).venv == "qibocal", "a session not saved: qibocal, as before"
    assert notebook.environment_name("..x") == "x" and notebook.environment_name("***") == "qibocal"
