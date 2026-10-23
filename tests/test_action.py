"""A protocol's parameter file, inline and as a download."""

from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from qibocamp import auth

from qibocamp.web import api

ACTION = "id: rabi\noperation: rabi_amplitude\nparameters:\n  min_amp: 0.0\n  max_amp: 1.0\n"


@pytest.fixture
def client(tmp_path):
    directory = tmp_path / "21:00:00_run"
    (directory / "data" / "rabi-0").mkdir(parents=True)
    (directory / "data" / "rabi-0" / "action.yml").write_text(ACTION)
    (directory / "data" / "flipping-0").mkdir(parents=True)
    (directory / "meta.json").write_text('{"author": "test", "stats": {}}')
    (directory / "history.json").write_text('["rabi-0", "flipping-0"]')
    api.set_report_root(tmp_path, is_original=True)
    auth.set_auth_enabled(False)
    yield TestClient(api.app)
    auth.set_auth_enabled(None)


def test_the_action_is_read_inline_and_downloaded(client):
    base = f"/api/reports/{quote('21:00:00_run', safe='')}/protocols/rabi-0/parameters"
    inline = client.get(base)
    assert inline.status_code == 200
    assert inline.text == ACTION
    assert inline.headers["content-type"].startswith("application/yaml")
    assert inline.headers["x-parameters-file"] == "action.yml"
    assert "content-disposition" not in inline.headers

    download = client.get(base, params={"download": "true"})
    assert download.status_code == 200
    assert download.text == ACTION
    assert download.headers["content-disposition"].startswith('attachment; filename="21-00-00_run_rabi-0_action.yml";')


def test_missing_actions_and_protocols_are_404(client):
    report = f"/api/reports/{quote('21:00:00_run', safe='')}"
    assert client.get(f"{report}/protocols/flipping-0/parameters").status_code == 404
    assert client.get(f"{report}/protocols/no-such/parameters").status_code == 404


def test_a_params_json_is_served_as_json(client, tmp_path):
    (tmp_path / "21:00:00_run" / "data" / "flipping-0" / "params.json").write_text('{"nflips": 10}')
    response = client.get(f"/api/reports/{quote('21:00:00_run', safe='')}/protocols/flipping-0/parameters")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["x-parameters-file"] == "params.json"
