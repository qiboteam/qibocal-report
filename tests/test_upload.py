"""Reports sent from another server: who may send them, and what is accepted."""

import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from qibocal_report import auth
from qibocal_report.reports import scanner
from qibocal_report.reports.upload import UploadError, receive_report
from qibocal_report.web import api


def report_zip(folder="10:00:00_[0]_rabi", files=None):
    files = files if files is not None else {"meta.json": "{}", "data/rabi-0/action.yml": "targets: [0]\n"}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(f"{folder}/{name}" if folder else name, content)
    return buffer.getvalue()


@pytest.fixture
def root(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    api.set_report_root(reports, is_original=True)
    scanner.invalidate_report_cache()
    return reports


def test_a_report_is_unpacked_under_its_folder_name_and_never_overwritten(root, tmp_path):
    archive = tmp_path / "report.zip"
    archive.write_bytes(report_zip())
    destination = receive_report(archive, root)
    assert destination == root / "10:00:00_[0]_rabi"
    assert (destination / "meta.json").is_file() and (destination / "data/rabi-0/action.yml").is_file()
    with pytest.raises(UploadError) as again:
        receive_report(archive, root)
    assert again.value.status_code == 409
    assert not [path for path in root.iterdir() if path.name.startswith(".upload-")], "nothing left behind"


@pytest.mark.parametrize(
    ("files", "folder", "reason"),
    [
        ({"meta.json": "{}", "../escape": "x"}, "run", "unsafe path"),
        ({"a/meta.json": "{}", "b/meta.json": "{}"}, None, "exactly one report folder"),
        ({"notes.txt": "x"}, "run", "no meta.json"),
        ({"meta.json": "{}"}, ".hidden", "hidden"),
        ({"meta.json": "{}"}, "C:", "unsafe path"),
    ],
)
def test_what_is_not_one_safe_report_is_refused(root, tmp_path, files, folder, reason):
    archive = tmp_path / "report.zip"
    archive.write_bytes(report_zip(folder, files))
    with pytest.raises(UploadError, match=reason):
        receive_report(archive, root)
    assert list(root.iterdir()) == [], "nothing written"


def test_a_report_larger_than_the_limit_is_refused(root, tmp_path, monkeypatch):
    monkeypatch.setenv("QIBOCAL_REPORT_UPLOAD_LIMIT", "10")
    archive = tmp_path / "report.zip"
    archive.write_bytes(report_zip(files={"meta.json": "x" * 100}))
    with pytest.raises(UploadError) as large:
        receive_report(archive, root)
    assert large.value.status_code == 413


def test_a_server_without_authentication_accepts_uploads(root):
    auth.set_auth_enabled(False)
    try:
        with TestClient(api.app) as client:
            assert client.get("/api/uploads").json() == {"accepted": True, "auth_enabled": False}
            response = client.post("/api/uploads", content=report_zip())
            assert response.status_code == 200, response.text
            assert response.json()["name"] == "10:00:00_[0]_rabi"
            assert any(report.id.endswith("rabi") for report in scanner.scan_reports(root)), "listed at once"
            assert client.post("/api/uploads", content=report_zip()).status_code == 409
    finally:
        auth.set_auth_enabled(None)


def test_an_authenticated_server_accepts_whom_its_policy_names(root):
    auth.set_auth_enabled(True)
    try:
        admin = auth.create_user("chief", "password", "admin")
        editor = auth.create_user("ed", "password", "editor")
        viewer = auth.create_user("vi", "password", "viewer")
        token = {user["username"]: auth.create_access_token(user) for user in (admin, editor, viewer)}
        headers = {name: {"Authorization": f"Bearer {value}"} for name, value in token.items()}
        with TestClient(api.app) as client:
            assert client.get("/api/uploads").json() == {"accepted": False, "auth_enabled": True}
            assert client.post("/api/uploads", content=report_zip()).status_code == 401, "anonymous: sign in"
            assert client.get("/api/uploads", headers=headers["chief"]).json()["accepted"] is True, "administrators always"
            assert client.get("/api/uploads", headers=headers["ed"]).json()["accepted"] is False, "admins only, by default"
            assert client.post("/api/uploads", content=report_zip(), headers=headers["ed"]).status_code == 403

            assert client.put("/api/admin/uploads", json={"policy": "editors"}, headers=headers["ed"]).status_code == 403
            assert client.put("/api/admin/uploads", json={"policy": "editors"}, headers=headers["chief"]).status_code == 200
            assert client.get("/api/uploads", headers=headers["ed"]).json()["accepted"] is True
            assert client.get("/api/uploads", headers=headers["vi"]).json()["accepted"] is False

            chosen = client.put("/api/admin/uploads", json={"policy": "admins", "users": [viewer["id"], "nobody"]}, headers=headers["chief"])
            assert chosen.json() == {"policy": "admins", "users": [viewer["id"]]}, "unknown users left out"
            assert client.get("/api/uploads", headers=headers["vi"]).json()["accepted"] is True, "a selected individual"
            assert client.get("/api/uploads", headers=headers["ed"]).json()["accepted"] is False
            assert client.post("/api/uploads", content=report_zip(), headers=headers["vi"]).status_code == 200

            client.put("/api/admin/uploads", json={"policy": "viewers"}, headers=headers["chief"])
            assert client.get("/api/uploads", headers=headers["ed"]).json()["accepted"] is True, "every signed-in user"
    finally:
        auth.set_auth_enabled(None)
