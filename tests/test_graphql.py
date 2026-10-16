"""The GraphQL endpoint answers what the REST endpoints answer, together."""

import json
import shutil
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qibocal_report.web.api import app, set_report_root


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("QIBOCAL_AUTH_ENABLED", raising=False)
    sample = Path(__file__).parent.parent / "sample_data"
    reports = tmp_path / "sample_data"
    shutil.copytree(sample, reports, ignore=shutil.ignore_patterns("*.zip"))
    archive = sample / "test-data.zip"
    # The sample reports travel zipped; unpacked next to the archive when they are not.
    if archive.is_file() and not any(p.is_dir() for p in reports.iterdir()):
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(reports)
    set_report_root(reports, is_original=True)
    return TestClient(app)


def graphql(client, query, variables=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.post(
        "/api/graphql", json={"query": query, "variables": variables or {}}, headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


REPORT_FIELDS = (
    "id path title date time author platform targets protocols tags labels "
    "total_execution_time has_cached_report has_old_platform has_new_platform"
)
STATS_FIELDS = (
    "authors tags labels protocols { name count } date_histogram { date count } "
    "platforms { name count } author_frequencies { name count } "
    "tag_frequencies { name count } total_reports"
)


def test_the_list_page_is_one_request(client):
    body = graphql(
        client,
        f"""
        query Dashboard($where: ReportFilter, $page: Int!, $page_size: Int!) {{
          reports(where: $where, page: $page, page_size: $page_size) {{
            items {{ {REPORT_FIELDS} }} total page page_size total_pages
          }}
          stats {{ {STATS_FIELDS} }}
          filtered: stats(where: $where) {{ total_reports }}
        }}
        """,
        {"where": {"sort_by": "date_desc"}, "page": 1, "page_size": 2},
    )
    assert "errors" not in body, body
    data = body["data"]
    rest = client.get("/api/reports?page=1&page_size=2").json()
    stats = client.get("/api/reports/stats").json()

    # The very shapes the REST endpoints answer with, field for field.
    assert data["reports"]["total"] == rest["total"]
    assert data["reports"]["total_pages"] == rest["total_pages"]
    assert [r["id"] for r in data["reports"]["items"]] == [r["id"] for r in rest["items"]]
    first_graphql, first_rest = data["reports"]["items"][0], rest["items"][0]
    for key in first_graphql:
        assert first_graphql[key] == first_rest[key], key
    assert data["stats"]["total_reports"] == stats["total_reports"]
    assert data["stats"]["protocols"] == stats["protocols"]
    assert data["stats"]["date_histogram"] == stats["date_histogram"]
    assert data["filtered"]["total_reports"] == stats["total_reports"]


def test_a_filter_narrows_both_the_page_and_the_statistics(client):
    everything = graphql(client, "{ stats { platforms { name count } total_reports } }")["data"]["stats"]
    platform = everything["platforms"][0]["name"]
    narrowed = graphql(
        client,
        """
        query ($where: ReportFilter) {
          reports(where: $where) { total items { platform } }
          stats(where: $where) { total_reports platforms { name } }
        }
        """,
        {"where": {"platforms": [platform]}},
    )["data"]
    assert narrowed["reports"]["total"] == narrowed["stats"]["total_reports"]
    assert all(item["platform"] == platform for item in narrowed["reports"]["items"])
    assert [p["name"] for p in narrowed["stats"]["platforms"]] == [platform]
    assert narrowed["reports"]["total"] <= everything["total_reports"]


def test_a_report_comes_with_its_protocols(client):
    listing = graphql(client, "{ reports(page_size: 500) { items { id has_cached_report } } }")
    cached = [r for r in listing["data"]["reports"]["items"] if r["has_cached_report"]]
    assert cached, "the sample data has pre-cached reports"
    report_id = cached[0]["id"]

    body = graphql(
        client,
        f"""
        query ($id: String!) {{
          report(id: $id) {{
            {REPORT_FIELDS}
            history platform_snapshot
            protocols_summary {{ id name status num_figures }}
            notes {{ content timestamp author }}
            protocols_detail {{ id name status html figures error notes {{ content }} }}
          }}
        }}
        """,
        {"id": report_id},
    )
    assert "errors" not in body, body
    report = body["data"]["report"]
    rest_detail = client.get(f"/api/reports/{report_id}").json()
    rest_protocols = client.get(f"/api/reports/{report_id}/protocols").json()
    assert report["id"] == rest_detail["id"]
    assert report["protocols"] == rest_detail["protocols"]
    assert [p["id"] for p in report["protocols_summary"]] == [
        p["id"] for p in rest_detail["protocols_summary"]
    ]
    assert [p["id"] for p in report["protocols_detail"]] == [p["id"] for p in rest_protocols]
    assert report["protocols_detail"][0]["figures"] == rest_protocols[0]["figures"]

    missing = graphql(client, 'query { report(id: "no-such-report") { id } }')
    assert missing["data"]["report"] is None


def test_the_session_is_one_request_too(client):
    body = graphql(client, "{ session { auth_enabled user { id username role } } health { status reports_count } }")
    assert body["data"]["session"] == {
        "auth_enabled": False,
        "user": {"id": "admin", "username": "local-admin", "role": "admin"},
    }
    assert body["data"]["health"]["status"] == "ok"
    assert body["data"]["health"]["reports_count"] >= 1


def test_without_a_token_the_reports_answer_as_the_rest_api_does(client, monkeypatch):
    from qibocal_report import auth

    monkeypatch.setenv("QIBOCAL_AUTH_ENABLED", "1")
    monkeypatch.setattr(auth, "_AUTH_ENABLED", None, raising=False)
    try:
        body = graphql(client, "{ session { auth_enabled user { id } } reports { total } }")
    finally:
        monkeypatch.setattr(auth, "_AUTH_ENABLED", None, raising=False)
    assert body["data"]["session"] == {"auth_enabled": True, "user": None}
    assert body["data"]["reports"] is None
    codes = [error.get("extensions", {}).get("code") for error in body["errors"]]
    assert codes == ["UNAUTHENTICATED"]


def test_a_server_without_graphql_answers_404_to_the_client(client):
    # The client reads a 404 or a 405 as "an older server": the REST fallback.
    # An older server's page catch-all answered a POST with 405; this one has
    # no page, and an endpoint it does not have is a 404.
    response = client.post("/api/no-such-endpoint", json={})
    assert response.status_code == 404
    assert json.loads(client.post("/api/graphql", json={"query": "{ health { status } }"}).text)["data"]


def test_outputs_come_one_protocol_at_a_time(client):
    listing = graphql(client, "{ reports(page_size: 500) { items { id has_cached_report } } }")
    report_id = next(r["id"] for r in listing["data"]["reports"]["items"] if r["has_cached_report"])

    # The report with its protocols named, their figures left out: what a card
    # needs to exist, without the megabytes it shows.
    body = graphql(
        client,
        """
        query ($id: String!) {
          report(id: $id) {
            has_cached_report
            protocols_detail { id name status num_figures notes { content } }
          }
        }
        """,
        {"id": report_id},
    )
    assert "errors" not in body, body
    stubs = body["data"]["report"]["protocols_detail"]
    rest = client.get(f"/api/reports/{report_id}/protocols").json()
    assert [p["id"] for p in stubs] == [p["id"] for p in rest]
    assert [p["num_figures"] for p in stubs] == [len(p["figures"]) for p in rest]
    assert all("figures" not in p for p in stubs)

    # One protocol's outputs, as the card comes into view.
    one = graphql(
        client,
        """
        query ($report_id: String!, $protocol_id: String!) {
          protocol(report_id: $report_id, protocol_id: $protocol_id) { id html figures error }
        }
        """,
        {"report_id": report_id, "protocol_id": stubs[0]["id"]},
    )["data"]["protocol"]
    assert one["id"] == rest[0]["id"]
    assert one["figures"] == rest[0]["figures"]
    assert one["html"] == rest[0]["html"]

    missing = graphql(
        client,
        'query ($r: String!) { protocol(report_id: $r, protocol_id: "no-such-protocol") { id } }',
        {"r": report_id},
    )
    assert missing["data"]["protocol"] is None
