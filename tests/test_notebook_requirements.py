"""The requirements of a notebook connection, enforced in its kernel environment."""

from unittest.mock import MagicMock

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
