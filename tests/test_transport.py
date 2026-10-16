"""What goes over the wire, and what does not."""

import shutil
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qibocal_report import scanner
from qibocal_report.api import app, set_report_root


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("QIBOCAL_AUTH_ENABLED", raising=False)
    sample = Path(__file__).parent.parent / "sample_data"
    reports = tmp_path / "sample_data"
    shutil.copytree(sample, reports, ignore=shutil.ignore_patterns("*.zip"))
    archive = sample / "test-data.zip"
    if archive.is_file() and not any(p.is_dir() for p in reports.iterdir()):
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(reports)
    set_report_root(reports, is_original=True)
    scanner.invalidate_report_cache()
    return TestClient(app)


def test_the_list_and_the_statistics_are_conditional(client):
    first = client.get("/api/reports?page=1&page_size=2")
    assert first.status_code == 200
    etag = first.headers["etag"]
    assert etag.startswith('W/"')
    assert first.headers["cache-control"] == "private, no-cache"

    again = client.get("/api/reports?page=1&page_size=2", headers={"If-None-Match": etag})
    assert again.status_code == 304
    assert again.headers["etag"] == etag
    assert again.content == b""

    stats = client.get("/api/reports/stats")
    assert stats.headers["etag"] == etag, "the same index, the same tag"
    assert client.get("/api/reports/stats", headers={"If-None-Match": etag}).status_code == 304
    assert client.get("/api/reports/stats", headers={"If-None-Match": 'W/"other"'}).status_code == 200


def test_large_responses_are_compressed(client):
    listing = client.get("/api/reports?page_size=500").json()
    report_id = next(r["id"] for r in listing["items"] if r["has_cached_report"])
    response = client.get(
        f"/api/reports/{report_id}/protocols", headers={"Accept-Encoding": "gzip"}
    )
    assert response.status_code == 200
    assert response.headers.get("content-encoding") == "gzip"
    assert response.json(), "the body is readable through the compression"


def test_what_the_client_never_read_is_not_sent(client):
    item = client.get("/api/reports?page=1&page_size=1").json()["items"][0]
    assert "search_index" not in item
    assert item["id"]

    with_platform = next(
        r for r in client.get("/api/reports?page_size=500").json()["items"] if r["has_new_platform"] or r["has_old_platform"]
    )
    detail = client.get(f"/api/reports/{with_platform['id']}").json()
    assert detail["platform_snapshot"] == {}
    assert "search_index" not in detail
    # Still there for whoever selects it.
    selected = client.post(
        "/api/graphql",
        json={"query": "query ($id: String!) { report(id: $id) { platform_snapshot } }", "variables": {"id": with_platform["id"]}},
    ).json()["data"]["report"]["platform_snapshot"]
    assert isinstance(selected, dict)


def test_the_index_is_validated_at_most_every_interval(client, monkeypatch):
    walks = []
    original = scanner.get_directory_mtime

    def counted(root):
        walks.append(root)
        return original(root)

    monkeypatch.setattr(scanner, "get_directory_mtime", counted)
    monkeypatch.setenv("QIBOCAL_REPORT_SCAN_INTERVAL", "60")
    scanner.invalidate_report_cache()
    for _ in range(3):
        assert client.get("/api/reports/stats").status_code == 200
    assert len(walks) == 1, "three requests, one walk"

    monkeypatch.setenv("QIBOCAL_REPORT_SCAN_INTERVAL", "0")
    client.get("/api/reports/stats")
    client.get("/api/reports/stats")
    assert len(walks) == 3, "at zero, every request walks"


def test_health_does_not_walk_the_tree(client, monkeypatch):
    client.get("/api/reports")  # the index exists
    walks = []
    monkeypatch.setattr(scanner, "get_directory_mtime", lambda root: walks.append(root) or 0.0)
    monkeypatch.setenv("QIBOCAL_REPORT_SCAN_INTERVAL", "0")
    health = client.get("/api/health").json()
    assert health["reports_count"] >= 1
    assert walks == []
