"""The server is headless: no page of its own, and links that lead to the dashboard."""

import json

from click.testing import CliRunner
from fastapi.testclient import TestClient

from qibocal_report import config

from qibocal_report.web import api
from qibocal_report.cli import main


def test_the_root_tells_where_the_dashboard_is_and_serves_no_page():
    with TestClient(api.app) as client:
        root = client.get("/")
        assert root.status_code == 200
        assert "text/html" in root.headers["content-type"]
        assert config.DASHBOARD_URL in root.text
        assert "/api/docs/swagger" in root.text
        assert client.get("/index.html").status_code == 404
        assert client.get("/assets/index.js").status_code == 404
        assert client.get("/servers").status_code == 404, "no page, so no page to fall back to"


def test_an_invitation_opens_the_dashboard_on_its_server():
    link = config.invite_link("http://lab:8000/", "t0k3n")
    assert link == f"{config.DASHBOARD_URL}/#/invite?token=t0k3n&server=http%3A%2F%2Flab%3A8000"
    dev = config.invite_link("http://localhost:8000", "t", dashboard="http://localhost:5173/")
    assert dev.startswith("http://localhost:5173/#/invite?token=t&server=")


def test_the_command_line_offers_no_client_nor_export():
    result = CliRunner().invoke(main, ["report", "--help"])
    assert result.exit_code == 0
    for word in ("client", "export", "dashboard"):
        assert f"  {word} " not in result.output, result.output
    assert "server" in result.output and "dev" in result.output


def test_the_root_links_to_the_dashboard_with_its_own_address(monkeypatch):
    with TestClient(api.app) as client:
        page = client.get("/").text
    # Built in the browser, from the address as it reached the server.
    assert f'{json.dumps(config.DASHBOARD_URL)} + "/#/connect?server=" + encodeURIComponent(here)' in page
    assert f'href="{config.DASHBOARD_URL}"' in page, "without scripts, the dashboard itself"
    monkeypatch.setattr(config, "DASHBOARD_URL", 'https://x.example/"</script><script>alert(1)//')
    with TestClient(api.app) as client:
        page = client.get("/").text
    assert "</script><script>alert" not in page, "a dashboard address never ends the script"
    assert 'href="https://x.example/&quot;' in page
