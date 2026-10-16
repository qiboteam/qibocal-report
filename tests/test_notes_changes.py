"""Comments may be changed and removed: by their author, or an administrator."""

from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from qibocal_report import api, auth, generator
from qibocal_report.models import ProtocolDetail
from qibocal_report.notes import (
    NoteMismatch,
    append_note,
    load_notes,
    remove_note,
    replace_note,
)


@pytest.fixture
def report(tmp_path):
    directory = tmp_path / "run"
    directory.mkdir()
    (directory / "meta.json").write_text('{"author": "test", "stats": {}}')
    (directory / "history.json").write_text('["rabi-0"]')
    data = directory / "data" / "rabi-0"
    data.mkdir(parents=True)
    (data / "data.json").write_text("{}")
    generator.write_protocol_cache(directory, [ProtocolDetail(id="rabi-0", name="rabi-0", html="")])
    api.set_report_root(tmp_path, is_original=True)
    auth.set_auth_enabled(False)
    yield directory
    auth.set_auth_enabled(None)


def prefix():
    return f"/api/reports/{quote('run', safe='')}"


def stamp(note):
    return note.model_dump(mode="json")["timestamp"]


def test_a_comment_is_changed_and_removed_in_place(report):
    first, second = append_note(report, "first", "a")[0], append_note(report, "second", "b")[1]
    changed = replace_note(report, 1, second.timestamp, "second, revised")
    assert [n.content for n in changed] == ["first", "second, revised"]
    assert changed[1].author == "b" and changed[1].timestamp == second.timestamp
    left = remove_note(report, 0, first.timestamp)
    assert [n.content for n in left] == ["second, revised"]
    assert load_notes(report) == left


def test_a_stale_history_cannot_touch_the_wrong_comment(report):
    first = append_note(report, "first", None)[0]
    append_note(report, "second", None)
    remove_note(report, 0, first.timestamp)  # "second" is now at 0
    with pytest.raises(NoteMismatch):
        replace_note(report, 0, first.timestamp, "oops")
    with pytest.raises(NoteMismatch):
        remove_note(report, 5, first.timestamp)
    assert [n.content for n in load_notes(report)] == ["second"]


@pytest.mark.parametrize("scope", ["", "/protocols/rabi-0"])
def test_the_endpoints_on_an_open_server(report, scope):
    directory = report if not scope else report / "data" / "rabi-0"
    with TestClient(api.app) as client:
        notes = client.post(f"{prefix()}{scope}/notes", json={"content": "draft"}).json()
        timestamp = notes[0]["timestamp"]
        changed = client.put(
            f"{prefix()}{scope}/notes/0", json={"content": "**final**", "timestamp": timestamp}
        )
        assert changed.status_code == 200
        assert changed.json()[0]["content"] == "**final**"
        assert changed.headers["cache-control"] == "no-store"
        stale = client.put(
            f"{prefix()}{scope}/notes/0",
            json={"content": "x", "timestamp": "2000-01-01T00:00:00+00:00"},
        )
        assert stale.status_code == 409
        gone = client.delete(f"{prefix()}{scope}/notes/0", params={"timestamp": timestamp})
        assert gone.status_code == 200 and gone.json() == []
        assert client.delete(f"{prefix()}{scope}/notes/0", params={"timestamp": timestamp}).status_code == 409
    assert load_notes(directory) == []


def test_only_the_author_or_an_administrator_may_change_a_comment(report):
    auth.set_auth_enabled(True)
    writer = auth.create_user("writer", "password", "editor")
    other = auth.create_user("other", "password", "editor")
    admin = auth.create_user("boss", "password", "admin")
    viewer = auth.create_user("reader", "password", "viewer")
    headers = {
        name: {"Authorization": f"Bearer {auth.create_access_token(user)}"}
        for name, user in (("writer", writer), ("other", other), ("admin", admin), ("viewer", viewer))
    }
    with TestClient(api.app) as client:
        url = f"{prefix()}/notes"
        notes = client.post(url, json={"content": "mine"}, headers=headers["writer"]).json()
        timestamp = notes[0]["timestamp"]
        body = {"content": "changed", "timestamp": timestamp}
        assert client.put(f"{url}/0", json=body).status_code == 401
        assert client.put(f"{url}/0", json=body, headers=headers["viewer"]).status_code == 403
        assert client.put(f"{url}/0", json=body, headers=headers["other"]).status_code == 403
        assert client.delete(f"{url}/0", params={"timestamp": timestamp}, headers=headers["other"]).status_code == 403
        assert client.put(f"{url}/0", json=body, headers=headers["writer"]).status_code == 200
        assert client.put(f"{url}/0", json={"content": "by admin", "timestamp": timestamp}, headers=headers["admin"]).status_code == 200
        assert client.get(url, headers=headers["viewer"]).json()[0] == {
            "content": "by admin", "timestamp": timestamp, "author": "writer"
        }
        assert client.delete(f"{url}/0", params={"timestamp": timestamp}, headers=headers["admin"]).status_code == 200
        assert client.get(url, headers=headers["viewer"]).json() == []
