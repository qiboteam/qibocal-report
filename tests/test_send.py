"""Reports uploaded from the command line, to a server as the dashboard reaches it."""

import json
import shutil
import zipfile

import pytest
from click.testing import CliRunner
from conftest import sample_reports
from fastapi.testclient import TestClient

from qibocamp import auth
from qibocamp.cli import main
from qibocamp.models import UserRole
from qibocamp.reports import scanner, send
from qibocamp.web.api import app, set_report_root

REPORT = "21:47:29_[3]_pi-pulse"
SERVER = "http://testserver"


@pytest.fixture
def setup(tmp_path, monkeypatch):
    """A receiving server with an empty root, and a report on this machine to send."""
    monkeypatch.delenv("QIBOCAMP_AUTH_ENABLED", raising=False)
    local = sample_reports(tmp_path / "local")
    root = tmp_path / "server"
    root.mkdir()
    set_report_root(root, is_original=True)
    scanner.invalidate_report_cache()
    client = TestClient(app, base_url=SERVER)
    yield local / REPORT, root, client._transport
    auth.set_auth_enabled(None)


def test_a_folder_is_sent_under_its_own_name_and_never_overwrites(setup):
    folder, root, transport = setup
    sent = send.send_report(folder, "testserver", transport=transport)
    assert sent.name == REPORT
    assert (root / REPORT / "meta.json").is_file()
    assert sorted(p.relative_to(root / REPORT) for p in (root / REPORT).rglob("*")) == sorted(
        p.relative_to(folder) for p in folder.rglob("*")
    )
    with pytest.raises(send.SendError, match="409"):
        send.send_report(folder, SERVER, transport=transport)


def test_a_zip_is_sent_as_it_is(setup, tmp_path):
    folder, root, transport = setup
    archive = send.zip_report(folder, tmp_path / "report.zip")
    with zipfile.ZipFile(archive) as opened:
        assert {name.split("/")[0] for name in opened.namelist()} == {REPORT}
    assert send.send_report(archive, SERVER, transport=transport).name == REPORT


def test_what_is_not_a_report_is_refused_before_sending(setup, tmp_path):
    _, _, transport = setup
    (tmp_path / "empty").mkdir()
    (tmp_path / "notes.txt").write_text("not a zip")
    for path, reason in ((tmp_path / "empty", "no meta.json"), (tmp_path / "notes.txt", "neither")):
        with pytest.raises(send.SendError, match=reason):
            send.send_report(path, SERVER, transport=transport)


def test_a_server_with_authentication_asks_to_sign_in(setup, monkeypatch):
    folder, root, transport = setup
    monkeypatch.setenv("QIBOCAMP_AUTH_ENABLED", "1")
    auth.set_auth_enabled(True)
    auth.create_user("alice", "password123", UserRole.ADMIN.value)
    auth.create_user("bob", "password123", UserRole.VIEWER.value)
    with pytest.raises(send.SendError, match="sign in"):
        send.send_report(folder, SERVER, transport=transport)
    with pytest.raises(send.SendError, match="Could not sign in"):
        send.send_report(folder, SERVER, username="alice", password="wrong", transport=transport)
    with pytest.raises(send.SendError, match="may not upload"):
        send.send_report(folder, SERVER, username="bob", password="password123", transport=transport)
    assert send.send_report(folder, SERVER, username="alice", password="password123", transport=transport).name == REPORT
    shutil.rmtree(root / REPORT)
    token = auth.create_access_token(auth.get_user_by_username("alice"))
    assert send.send_report(folder, SERVER, token=token, transport=transport).name == REPORT


def test_the_command_signs_in_and_answers(setup, monkeypatch):
    folder, root, transport = setup
    real = send.send_report
    monkeypatch.setattr(send, "send_report", lambda *args, **kwargs: real(*args, **kwargs, transport=transport))
    monkeypatch.setenv("QIBOCAMP_AUTH_ENABLED", "1")
    auth.set_auth_enabled(True)
    auth.create_user("alice", "password123", UserRole.ADMIN.value)
    result = CliRunner().invoke(main, ["report", "upload", str(folder), SERVER, "-u", "alice", "--json"], input="password123\n")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output.strip().splitlines()[-1])["name"] == REPORT
    again = CliRunner().invoke(main, ["report", "upload", str(folder), SERVER, "-u", "alice"], env={"QIBOCAMP_PASSWORD": "password123"})
    assert again.exit_code == 1 and "never overwritten" in again.output
