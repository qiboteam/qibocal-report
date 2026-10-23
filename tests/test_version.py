"""What a server says it is."""

import json

from fastapi.testclient import TestClient

from qibocamp import __version__, auth, version
from qibocamp.web.api import app


def test_the_version_is_public_and_the_package_s(monkeypatch):
    monkeypatch.setenv("QIBOCAMP_AUTH_ENABLED", "1")
    auth.set_auth_enabled(True)
    try:
        answer = TestClient(app).get("/api/version")
    finally:
        auth.set_auth_enabled(None)
    assert answer.status_code == 200
    body = answer.json()
    assert body["version"] == __version__ != "0+unknown"
    assert body["api_version"] == version.API_VERSION
    assert "graphql" in body["features"]


class Recorded:
    def __init__(self, origin):
        self.origin = origin

    def read_text(self, name):
        assert name == "direct_url.json"
        return json.dumps(self.origin) if self.origin is not None else None


def test_the_commit_is_the_one_pip_recorded(monkeypatch):
    sha = "0123456789abcdef0123456789abcdef01234567"
    cases = [
        ({"url": "https://github.com/qiboteam/qibocamp", "vcs_info": {"vcs": "git", "commit_id": sha}}, sha),
        ({"url": f"https://github.com/qiboteam/qibocamp/archive/{sha}.tar.gz", "archive_info": {}}, sha),
        ({"url": "https://github.com/qiboteam/qibocamp/archive/refs/heads/main.tar.gz"}, None),
        ({"url": "file:///src", "dir_info": {"editable": True}}, None),
        (None, None),
    ]
    for origin, commit in cases:
        monkeypatch.setattr(version, "distribution", lambda _name, origin=origin: Recorded(origin))
        assert version.installed_commit() == commit
