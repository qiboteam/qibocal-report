import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from qibocal_report import config
from qibocal_report.api import app, set_report_root
from qibocal_report.scanner import scan_reports, filter_reports, compute_filter_stats
from qibocal_report.generator import has_cached_report, load_cached_protocols, regenerate_report

@pytest.fixture(autouse=True)
def setup_env(tmp_path, monkeypatch):
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path / "config"))
    sample_dir = Path(__file__).parent.parent / "sample_data"
    set_report_root(sample_dir)

def test_config_servers(tmp_path):
    servers = config.load_servers()
    assert len(servers) >= 1
    new_srv = config.add_server("http://example.com:9000", name="test-qpu")
    assert new_srv["name"] == "test-qpu"
    assert new_srv["url"] == "http://example.com:9000"

    # Update
    updated = config.update_server(new_srv["id"], {"description": "Updated desc"})
    assert updated["description"] == "Updated desc"

    # Delete
    deleted = config.delete_server(new_srv["id"])
    assert deleted is True

def test_scanner_and_filters():
    sample_dir = Path(__file__).parent.parent / "sample_data"
    reports = scan_reports(sample_dir)
    assert len(reports) == 3

    # Filter by author
    alice_reports = filter_reports(reports, authors=["Alice"])
    assert len(alice_reports) == 1
    assert alice_reports[0].author == "Alice"

    # Filter by query
    rigetti = filter_reports(reports, query="Aspen")
    assert len(rigetti) == 1
    assert "aspen" in rigetti[0].platform.lower()

    # Filter by protocol
    rb_reports = filter_reports(reports, protocols=["randomized_benchmarking"])
    assert len(rb_reports) == 1

    # Filter stats
    stats = compute_filter_stats(reports)
    assert "Alice" in stats.authors
    assert "daily" in stats.labels
    assert len(stats.protocols) > 0
    # verify protocols are sorted descending by frequency
    counts = [p.count for p in stats.protocols]
    assert counts == sorted(counts, reverse=True)

def test_generator_modes(tmp_path):
    # Test pre-cached reading
    sample_dir = Path(__file__).parent.parent / "sample_data"
    rep1 = sample_dir / "20241220-starfleet-5q"
    assert has_cached_report(rep1) is True
    cached_protos = load_cached_protocols(rep1)
    assert len(cached_protos) >= 2
    assert any(p.id == "resonator_spectroscopy" for p in cached_protos)
    assert len(cached_protos[0].figures) > 0

    # Test regeneration
    rep2 = sample_dir / "20241221-rigetti-8q"
    regenerated = regenerate_report(rep2)
    assert len(regenerated) > 0
    assert has_cached_report(rep2) is True

def test_api_endpoints():
    client = TestClient(app)

    # Health
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["reports_count"] == 3

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
    assert len(reports) == 3

    # Stats
    r = client.get("/api/reports/stats")
    assert r.status_code == 200
    stats = r.json()
    assert "protocols" in stats
    assert "date_histogram" in stats

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

def test_docs_endpoint():
    client = TestClient(app)
    r = client.get("/api/docs-content/usage")
    assert r.status_code == 200
    assert "# User Guide" in r.text

    r = client.get("/api/docs-content/nonexistent")
    assert r.status_code == 404
