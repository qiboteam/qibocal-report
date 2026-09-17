import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qibocal_report import config
from qibocal_report.api import app, get_report_root, set_report_root
from qibocal_report.generator import (
    has_cached_report,
    load_cached_protocols,
    regenerate_report,
)
from qibocal_report.scanner import compute_filter_stats, filter_reports, scan_reports


@pytest.fixture(autouse=True)
def setup_env(tmp_path, monkeypatch):
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path / "config"))
    sample_src = Path(__file__).parent.parent / "sample_data"
    test_reports = tmp_path / "sample_data"
    shutil.copytree(sample_src, test_reports, ignore=shutil.ignore_patterns("*.zip"))
    set_report_root(test_reports)


def test_config_servers(tmp_path):
    servers = config.load_servers()
    assert len(servers) >= 1
    new_srv = config.add_server("http://example.com:9000", name="test-qpu")
    assert new_srv["name"] == "test-qpu"
    assert new_srv["url"] == "http://example.com:9000"

    # Update
    updated = config.update_server(new_srv["id"], {"description": "Updated desc"})
    assert updated["description"] == "Updated desc"

    # URL normalization
    norm_srv = config.add_server("192.168.1.100:8000/", name="raw-ip")
    assert norm_srv["url"] == "http://192.168.1.100:8000"

    updated_norm = config.update_server(norm_srv["id"], {"url": "10.0.0.1:8080/"})
    assert updated_norm["url"] == "http://10.0.0.1:8080"

    # Delete
    deleted = config.delete_server(new_srv["id"])
    assert deleted is True
    config.delete_server(norm_srv["id"])


def test_scanner_and_filters():
    sample_dir = Path(__file__).parent.parent / "sample_data"
    reports = scan_reports(sample_dir)
    assert len(reports) >= 3

    # Filter by query
    pi_pulse = filter_reports(reports, query="pi-pulse")
    assert len(pi_pulse) == 1
    assert "pi-pulse" in pi_pulse[0].id.lower()

    # Filter by protocol
    ssc_reports = filter_reports(reports, protocols=["single_shot_classification"])
    assert len(ssc_reports) >= 2

    # Filter stats
    stats = compute_filter_stats(reports)
    assert len(stats.protocols) > 0
    # verify protocols are sorted descending by frequency
    counts = [p.count for p in stats.protocols]
    assert counts == sorted(counts, reverse=True)
    assert "broken" in stats.tags
    assert "broken" in stats.labels
    assert len(stats.platforms) > 0
    assert len(stats.author_frequencies) > 0
    assert stats.total_reports == len(reports)

    # Filter by platform
    top_platform = stats.platforms[0].name
    plat_reports = filter_reports(reports, platforms=[top_platform])
    assert len(plat_reports) == stats.platforms[0].count
    assert all(r.platform == top_platform for r in plat_reports)

    # Filter by tag / label
    broken_reports = filter_reports(reports, labels=["broken"])
    assert len(broken_reports) == 1
    assert "broken" in broken_reports[0].tags

    # Sort by platform
    sorted_by_platform = filter_reports(reports, sort_by="platform")
    platforms = [r.platform.lower() for r in sorted_by_platform if r.platform]
    assert platforms == sorted(platforms)


def test_generator_modes():
    test_reports = get_report_root()
    rep1 = test_reports / "21:47:29_[3]_pi-pulse"
    cache_dir = rep1 / "report"
    cache_dir.mkdir(parents=True, exist_ok=True)
    proto_data = [
        {
            "id": "rabi_amplitude",
            "name": "Rabi Amplitude",
            "category": "calibration",
            "status": "success",
            "figures": [{"id": "fig1", "title": "Rabi Plot", "data": [], "layout": {}}],
            "html": "<p>Rabi results</p>",
        }
    ]
    with open(cache_dir / "protocols.json", "w", encoding="utf-8") as f:
        json.dump(proto_data, f)

    assert has_cached_report(rep1) is True
    cached_protos = load_cached_protocols(rep1)
    assert len(cached_protos) == 1
    assert "rabi" in cached_protos[0].id
    assert len(cached_protos[0].figures) > 0

    # Test regeneration on-the-fly with Qibocal
    rep2 = test_reports / "21:39:54_[3]_single_shot_classification"
    regenerated = regenerate_report(rep2)
    assert len(regenerated) > 0
    assert regenerated[0].status == "success"
    assert len(regenerated[0].figures) > 0
    assert has_cached_report(rep2) is True

    # Test error reporting when Qibocal is not available / cannot generate
    from unittest.mock import patch

    from qibocal_report.generator import generate_report_on_the_fly

    with patch(
        "qibocal_report.generator._generate_qibocal_protocols",
        return_value=(None, "Qibocal is not installed in the environment."),
    ):
        rep_unavail = test_reports / "nonexistent_run"
        rep_unavail.mkdir()
        err_protos = generate_report_on_the_fly(rep_unavail)
        assert len(err_protos) > 0
        assert err_protos[0].status == "error"
        assert "Qibocal is not installed" in (err_protos[0].error or "")


def test_api_endpoints():
    client = TestClient(app)

    # Health
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["reports_count"] >= 3

    # Servers
    r = client.get("/api/servers")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Add server
    r = client.post("/api/servers", json={"url": "http://192.168.1.50:8000"})
    assert r.status_code == 200
    srv_data = r.json()
    assert "url" in srv_data
    srv_id = srv_data["id"]

    # Save servers
    r = client.post("/api/servers/save")
    assert r.status_code == 200
    assert r.json()["saved"] is True

    # Delete server
    r = client.delete(f"/api/servers/{srv_id}")
    assert r.status_code == 200

    # Reports list
    r = client.get("/api/reports")
    assert r.status_code == 200
    reports = r.json()
    assert len(reports) >= 3

    # Filter by tag
    r_tag = client.get("/api/reports?tag=broken")
    assert r_tag.status_code == 200
    assert len(r_tag.json()) == 1
    assert "broken" in r_tag.json()[0]["tags"]

    # Stats
    r = client.get("/api/reports/stats")
    assert r.status_code == 200
    stats = r.json()
    assert "protocols" in stats
    assert "date_histogram" in stats
    assert "platforms" in stats
    assert "author_frequencies" in stats
    assert stats["total_reports"] > 0

    # Filter by platform via API
    plat_name = stats["platforms"][0]["name"]
    r_plat = client.get(f"/api/reports?platform={plat_name}")
    assert r_plat.status_code == 200
    assert len(r_plat.json()) == stats["platforms"][0]["count"]

    # Single report detail
    first_id = reports[0]["id"]
    r = client.get(f"/api/reports/{first_id}")
    assert r.status_code == 200
    detail = r.json()
    assert "protocols_summary" in detail

    # Report protocols
    r = client.get(f"/api/reports/{first_id}/protocols")
    assert r.status_code == 200
    protos = r.json()
    assert len(protos) > 0
    assert "figures" in protos[0]
    assert "html" in protos[0]

    # Regenerate report
    r = client.post(f"/api/reports/{first_id}/regenerate")
    assert r.status_code == 200
    protos_regen = r.json()
    assert len(protos_regen) > 0

    # WebSocket endpoint streaming
    with client.websocket_connect(f"/ws/reports/{first_id}") as ws:
        msg1 = ws.receive_json()
        assert msg1["type"] == "metadata"
        msg2 = ws.receive_json()
        assert msg2["type"] in ("status", "ready")


def test_docs_endpoint():
    client = TestClient(app)
    r = client.get("/api/docs-content/usage")
    assert r.status_code == 200
    assert "# User Guide" in r.text

    r = client.get("/api/docs-content/nonexistent")
    assert r.status_code == 404


def test_dev_mode_redirect(monkeypatch):
    monkeypatch.setenv("QIBOCAL_FRONTEND_URL", "http://localhost:5173")
    client = TestClient(app, follow_redirects=False)
    r = client.get("/")
    assert r.status_code in (307, 302)
    assert r.headers["location"] == "http://localhost:5173"


def test_bulk_actions():
    client = TestClient(app)

    # 1. Test bulk label
    r = client.get("/api/reports")
    reports = r.json()
    assert len(reports) >= 2
    ids_to_label = [reports[0]["id"], reports[1]["id"]]

    res = client.post(
        "/api/reports/bulk-action",
        json={"action": "label", "report_ids": ids_to_label, "label": "bulk-tested"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["affected"] == 2

    # Verify both have the tag now
    r_tagged = client.get("/api/reports?tag=bulk-tested")
    assert r_tagged.status_code == 200
    assert len(r_tagged.json()) == 2

    # 2. Test bulk delete
    id_to_delete = reports[0]["id"]
    res_del = client.post(
        "/api/reports/bulk-action",
        json={"action": "delete", "report_ids": [id_to_delete]},
    )
    assert res_del.status_code == 200
    del_data = res_del.json()
    assert del_data["success"] is True
    assert del_data["affected"] == 1

    # Verify it is no longer listed
    r_after = client.get("/api/reports")
    remaining_ids = [rep["id"] for rep in r_after.json()]
    assert id_to_delete not in remaining_ids

    # 3. Test invalid action & empty label
    res_bad = client.post(
        "/api/reports/bulk-action",
        json={"action": "invalid_action", "report_ids": []},
    )
    assert res_bad.status_code == 400

    res_empty_label = client.post(
        "/api/reports/bulk-action",
        json={"action": "label", "report_ids": [], "label": "   "},
    )
    assert res_empty_label.status_code == 400


def test_single_report_actions():
    client = TestClient(app)
    r = client.get("/api/reports")
    reports = r.json()
    assert len(reports) >= 2
    rep_id = reports[0]["id"]

    # Test single label
    res_label = client.post(
        f"/api/reports/{rep_id}/label", json={"label": "single-tagged"}
    )
    assert res_label.status_code == 200
    assert res_label.json()["success"] is True

    r_verify = client.get(f"/api/reports/{rep_id}")
    assert r_verify.status_code == 200
    assert "single-tagged" in r_verify.json()["tags"]

    # Test single delete
    res_del = client.delete(f"/api/reports/{rep_id}")
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True

    r_after = client.get(f"/api/reports/{rep_id}")
    assert r_after.status_code == 404


def test_remove_label_and_author_actions():
    client = TestClient(app)
    r = client.get("/api/reports")
    reports = r.json()
    assert len(reports) >= 2
    target_rep = reports[0]
    target_id = target_rep["id"]

    # 1. Add a tag first
    res_add = client.post(
        f"/api/reports/{target_id}/label", json={"label": "to-remove"}
    )
    assert res_add.status_code == 200

    r_verify = client.get(f"/api/reports/{target_id}")
    assert "to-remove" in r_verify.json()["tags"]

    # 2. Delete the tag via single label delete endpoint
    res_del_tag = client.delete(f"/api/reports/{target_id}/label/to-remove")
    assert res_del_tag.status_code == 200
    assert res_del_tag.json()["success"] is True

    r_verify2 = client.get(f"/api/reports/{target_id}")
    assert "to-remove" not in r_verify2.json()["tags"]

    # 3. Test bulk unlabel
    # Add label to 2 reports
    id1, id2 = reports[0]["id"], reports[1]["id"]
    client.post(
        "/api/reports/bulk-action",
        json={"action": "label", "report_ids": [id1, id2], "label": "bulk-temp"},
    )
    # Remove via bulk unlabel
    res_bulk_unlabel = client.post(
        "/api/reports/bulk-action",
        json={"action": "unlabel", "report_ids": [id1, id2], "label": "bulk-temp"},
    )
    assert res_bulk_unlabel.status_code == 200
    assert res_bulk_unlabel.json()["success"] is True
    assert res_bulk_unlabel.json()["affected"] == 2

    # 4. Test single author update
    res_author = client.put(
        f"/api/reports/{target_id}/author", json={"author": "Alice Specialist"}
    )
    assert res_author.status_code == 200
    assert res_author.json()["success"] is True

    r_verify_author = client.get(f"/api/reports/{target_id}")
    assert r_verify_author.json()["author"] == "Alice Specialist"

    # 5. Test bulk author update
    res_bulk_author = client.post(
        "/api/reports/bulk-action",
        json={"action": "author", "report_ids": [id1, id2], "author": "Quantum Team"},
    )
    assert res_bulk_author.status_code == 200
    assert res_bulk_author.json()["affected"] == 2

    r1 = client.get(f"/api/reports/{id1}").json()
    r2 = client.get(f"/api/reports/{id2}").json()
    assert r1["author"] == "Quantum Team"
    assert r2["author"] == "Quantum Team"


def test_author_identities_and_search_index():
    from qibocal_report.config import resolve_author_identity

    # 1. Test resolve_author_identity helper
    identities = {
        "Alice": ["alice", "a.smith", "alicesmith"],
        "Bob": ["bob", "b.jones"],
    }
    assert resolve_author_identity("a.smith", identities) == "Alice"
    assert resolve_author_identity("Alice", identities) == "Alice"
    assert resolve_author_identity("BOB", identities) == "Bob"
    assert resolve_author_identity("UnknownPerson", identities) == "UnknownPerson"
    assert resolve_author_identity("Unknown", identities) == "Unknown"
    assert resolve_author_identity(None, identities) == "Unknown"

    # 2. Test server config with author_identities
    srv = config.add_server(
        "http://127.0.0.1:8001",
        name="alias-server",
        author_identities={"Dr. Quantum": ["alecandido", "qibo_user"]},
    )
    assert "author_identities" in srv
    assert srv["author_identities"]["Dr. Quantum"] == ["alecandido", "qibo_user"]

    # 3. Test scanner applies author_identities and produces search_index
    test_reports = get_report_root()
    reports = scan_reports(test_reports, author_identities=srv["author_identities"])
    assert len(reports) > 0
    first = reports[0]
    assert hasattr(first, "search_index")
    assert isinstance(first.search_index, str)
    assert len(first.search_index) > 0
    # verify search_index is lowercase and contains keywords
    assert first.platform.lower() in first.search_index
    assert first.id.lower() in first.search_index


def test_pagination_and_cache_invalidation():
    client = TestClient(app)
    test_reports = get_report_root()

    # 1. Test pagination query parameters
    r_p1 = client.get("/api/reports?page=1&page_size=2")
    assert r_p1.status_code == 200
    data_p1 = r_p1.json()
    assert "items" in data_p1
    assert "total" in data_p1
    assert data_p1["page"] == 1
    assert data_p1["page_size"] == 2
    assert len(data_p1["items"]) == 2
    assert data_p1["total"] >= 3
    assert data_p1["total_pages"] >= 2
    assert r_p1.headers.get("X-Total-Count") == str(data_p1["total"])
    assert r_p1.headers.get("X-Page") == "1"

    # Page 2
    r_p2 = client.get("/api/reports?page=2&page_size=2")
    assert r_p2.status_code == 200
    data_p2 = r_p2.json()
    assert data_p2["page"] == 2
    assert len(data_p2["items"]) >= 1
    # Check that items on page 1 and page 2 are distinct
    p1_ids = {item["id"] for item in data_p1["items"]}
    p2_ids = {item["id"] for item in data_p2["items"]}
    assert p1_ids.isdisjoint(p2_ids)

    # 2. Test backend caching and invalidation
    from qibocal_report.scanner import _REPORT_CACHE, invalidate_report_cache

    # First scan caches the results
    scan1 = scan_reports(test_reports)
    # Second scan returns the exact cached object
    scan2 = scan_reports(test_reports)
    assert scan1 is scan2

    # Invalidate cache manually
    invalidate_report_cache()
    scan3 = scan_reports(test_reports)
    assert len(scan3) == len(scan1)

    # Invalidation on file modification
    first_report_dir = Path(scan1[0].path)
    meta_file = first_report_dir / "meta.json"
    if meta_file.is_file():
        # Update modification time to future
        new_mtime = max(meta_file.stat().st_mtime, _REPORT_CACHE["last_mtime"]) + 10.0
        import os

        os.utime(meta_file, (new_mtime, new_mtime))
        scan_modified = scan_reports(test_reports)
        assert scan_modified is not scan3
