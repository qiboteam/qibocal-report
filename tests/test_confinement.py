"""Report and archive ids name what is inside the reports root, and nothing else."""

import pytest
from conftest import sample_reports
from fastapi.testclient import TestClient

from qibocamp.reports import archive, scanner
from qibocamp.web.api import app, set_report_root

REPORT = "21:47:29_[3]_pi-pulse"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("QIBOCAMP_AUTH_ENABLED", raising=False)
    root = sample_reports(tmp_path / "reports")
    set_report_root(root, is_original=True)
    scanner.invalidate_report_cache()
    # What must stay out of reach: a sibling of the root, holding a secret.
    secret = tmp_path / "secret"
    secret.mkdir()
    (secret / "auth.json").write_text('{"secret_key": "x"}')
    (secret / "meta.json").write_text("{}")
    return TestClient(app)


@pytest.mark.parametrize(
    "report_id",
    ["..%2Fsecret", "%2E%2E%2Fsecret", "SECRET_ABSOLUTE", "%2E", f"{REPORT}%2F..%2F..%2Fsecret"],
)
@pytest.mark.parametrize("suffix", ["/download/full", "/download/new-platform", "/meta", "/protocols", ""])
def test_a_report_id_never_leaves_the_root(client, tmp_path, report_id, suffix):
    report_id = report_id.replace("SECRET_ABSOLUTE", str(tmp_path / "secret").replace("/", "%2F"))
    response = client.get(f"/api/reports/{report_id}{suffix}")
    assert response.status_code == 404, response.text[:200]


def test_a_report_inside_the_root_is_found(client):
    assert client.get(f"/api/reports/{REPORT}/download/full").status_code == 200


def test_the_live_socket_refuses_an_id_outside_the_root(client):
    with client.websocket_connect("/ws/reports/..%2Fsecret") as socket:
        assert socket.receive_json()["type"] == "error"


@pytest.mark.parametrize("archive_id", ["..", "%2E%2E", "arc-x%2F..%2F..", "not-an-archive"])
def test_an_archive_id_names_an_archive_folder_only(client, tmp_path, archive_id):
    response = client.delete(f"/api/archives/{archive_id}")
    assert response.status_code in (404, 405), response.text[:200]
    assert (tmp_path / "reports" / REPORT).is_dir(), "the reports are untouched"
    assert archive.archive_directory(tmp_path, "..") is None


def test_the_root_itself_is_never_archived(client, tmp_path):
    response = client.post("/api/archives", json={"report_ids": ["."], "remove_from_active": True})
    assert response.status_code >= 400
    assert (tmp_path / "reports" / REPORT).is_dir(), "the reports are untouched"


@pytest.mark.parametrize(
    ("origin", "allowed"),
    [
        ("https://evil.example", False),
        ("https://qibo.science", True),
        ("tauri://localhost", True),
        ("http://tauri.localhost", True),
        ("http://localhost:5173", True),
        ("http://testserver", True),
    ],
)
def test_only_the_dashboard_the_launcher_and_this_machine_may_call(client, origin, allowed):
    preflight = client.options(
        "/api/admin/qibocal/install",
        headers={"origin": origin, "access-control-request-method": "POST", "access-control-request-headers": "content-type"},
    )
    # The server's own pages need no preflight at all.
    if origin != "http://testserver":
        assert (preflight.headers.get("access-control-allow-origin") == origin) is allowed
    # A form needs no preflight: the server itself refuses it.
    upload = client.post(
        "/api/reports/upload", headers={"origin": origin}, files={"file": ("r.zip", b"PK", "application/zip")}
    )
    assert (upload.status_code == 403) is not allowed


def test_another_deployment_of_the_dashboard_can_be_allowed(client, monkeypatch):
    monkeypatch.setenv("QIBOCAMP_ALLOWED_ORIGINS", "https://lab.example.org/, https://other.example")
    upload = client.post(
        "/api/reports/upload", headers={"origin": "https://lab.example.org"}, files={"file": ("r.zip", b"PK", "application/zip")}
    )
    assert upload.status_code != 403


def test_a_report_in_a_subfolder_is_tagged_untagged_and_kept(client, tmp_path):
    import shutil

    root = tmp_path / "reports"
    shutil.copytree(root / REPORT, root / "runs" / "chip" / REPORT)
    scanner.invalidate_report_cache()
    nested = f"runs/chip/{REPORT}".replace("/", "%2F")
    assert client.post(f"/api/reports/{nested}/label", json={"label": "fresh"}).status_code == 200
    assert client.put(f"/api/reports/{nested}/author", json={"author": "someone"}).status_code == 200
    assert client.delete(f"/api/reports/{nested}/label/fresh").status_code == 200
    assert (root / "runs" / "chip" / REPORT / "meta.json").is_file()
    # A URL collapses `..`: such a tag would be removed by deleting the report.
    for tag in (".", "..", "a/b"):
        refused = client.post("/api/reports/bulk-action", json={"action": "label", "report_ids": [REPORT], "label": tag})
        assert refused.status_code == 400


@pytest.mark.parametrize("name", ["..%2F..%2FREADME", "%2E%2E%2Fpyproject", ".hidden", "user-guide%2F..%2F..%2FREADME"])
def test_the_documentation_serves_its_own_pages_only(client, name):
    assert client.get(f"/api/docs-content/{name}").status_code == 404


def test_a_documentation_page_is_served(client):
    assert client.get("/api/docs-content/user-guide/quickstart").status_code == 200


def test_a_folder_of_any_name_downloads(client, tmp_path):
    import shutil

    shutil.copytree(tmp_path / "reports" / REPORT, tmp_path / "reports" / 'calibração "α"')
    scanner.invalidate_report_cache()
    response = client.get("/api/reports/calibra%C3%A7%C3%A3o%20%22%CE%B1%22/download/full")
    assert response.status_code == 200
    assert "filename*=utf-8''calibra%C3%A7%C3%A3o%20%22%CE%B1%22.zip" in response.headers["content-disposition"]


@pytest.mark.parametrize("target", [f"{REPORT}/platform", f"{REPORT}/data", "..", f"../reports/{REPORT}"])
def test_an_action_reaches_reports_only(client, tmp_path, target):
    response = client.post("/api/reports/bulk-action", json={"action": "delete", "report_ids": [target]})
    assert response.status_code == 404 or response.json()["affected"] == 0
    for folder in ("platform", "data"):
        assert (tmp_path / "reports" / REPORT / folder).is_dir(), "nothing but a report is deleted"


@pytest.mark.parametrize("path", [f"/ws/reports/{REPORT}", f"/ws/live/reports/{REPORT}"])
def test_a_socket_from_a_foreign_page_is_refused(client, path):
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(path, headers={"origin": "https://evil.example"}) as socket:
            socket.receive_json()
    with client.websocket_connect(f"/ws/reports/{REPORT}", headers={"origin": "https://qibo.science"}) as socket:
        assert socket.receive_json()["type"] != "error"


def test_the_documentation_serves_no_other_package_s_markdown(client):
    # site-packages is one of the roots: its other files are not documentation.
    assert client.get("/api/docs-content/uvicorn-0.54.0.dist-info/licenses/LICENSE").status_code == 404
    assert client.get("/api/docs-content/README").status_code == 404
