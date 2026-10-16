"""Qibocal installed from a folder on the server."""

import pytest
from fastapi.testclient import TestClient

from qibocal_report import api, auth, qibocal_environment


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("QIBOCAL_AUTH_ENABLED", raising=False)
    auth.set_auth_enabled(False)
    yield TestClient(api.app)
    auth.set_auth_enabled(None)


def test_a_local_folder_must_be_an_absolute_python_project(tmp_path):
    with pytest.raises(qibocal_environment.EnvironmentOperationError, match="absolute"):
        qibocal_environment.local_project("relative/qibocal")
    with pytest.raises(qibocal_environment.EnvironmentOperationError, match="No such folder"):
        qibocal_environment.local_project(str(tmp_path / "missing"))
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(qibocal_environment.EnvironmentOperationError, match="not a Python project"):
        qibocal_environment.local_project(str(plain))
    project = tmp_path / "qibocal"
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\nname = 'qibocal'\n")
    target, source, version = qibocal_environment._installation_target(f"local:{project}")
    assert (target, source, version) == (str(project.resolve()), "local", None)
    command = qibocal_environment._installer_command(target, editable=True)
    assert command[-2:] == ["-e", str(project.resolve())], "a folder is installed editable"


def test_the_server_offers_the_folder_option(monkeypatch):
    monkeypatch.setattr(qibocal_environment, "_pypi_options", lambda: ([], None))
    monkeypatch.setattr(qibocal_environment, "_github_branches", lambda: ([], None, None))
    options = qibocal_environment.get_qibocal_options()
    assert any(option.source == "local" and option.id == "local" for option in options.options)


def test_the_folders_of_the_server_are_listed_for_administrators(client, tmp_path):
    (tmp_path / "qibocal").mkdir()
    (tmp_path / "qibocal" / "pyproject.toml").write_text("")
    (tmp_path / "notes").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "file.txt").write_text("")
    response = client.get("/api/admin/filesystem", params={"path": str(tmp_path)})
    assert response.status_code == 200, response.text
    listing = response.json()
    assert listing["path"] == str(tmp_path.resolve())
    assert [entry["name"] for entry in listing["entries"]] == ["notes", "qibocal"], "folders only, hidden ones left out"
    assert [entry["project"] for entry in listing["entries"]] == [False, True]
    assert listing["parent"] == str(tmp_path.resolve().parent)
    assert client.get("/api/admin/filesystem", params={"path": "relative"}).status_code == 400
    assert client.get("/api/admin/filesystem", params={"path": str(tmp_path / "nope")}).status_code == 404
    home = client.get("/api/admin/filesystem").json()
    assert home["path"], "no path: the home folder"
