"""Process-local diagnostics capture and its admin-only polling API."""

import io
import json
import logging
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from rich.console import Console

from qibocal_report import api, auth, logger


@pytest.fixture
def history(monkeypatch):
    history = logger.LogHistory()
    monkeypatch.setattr(logger, "log_history", history)
    monkeypatch.setattr(api, "log_history", history)
    monkeypatch.setattr(
        logger, "console", Console(file=io.StringIO(), force_terminal=True, width=120)
    )
    monkeypatch.setattr(
        logger,
        "error_console",
        Console(file=io.StringIO(), force_terminal=True, width=120),
    )
    return history


@pytest.mark.parametrize(
    ("helper", "args", "stderr"),
    [
        ("log_info", ("Information",), False),
        ("log_step", (1, 3, "Generating plots"), False),
        ("log_success", ("Finished",), False),
        ("log_warning", ("Warning",), False),
        ("log_error", ("Failure",), True),
    ],
)
def test_rich_helpers_capture_rendered_colors_without_replacing_terminal(
    history, helper, args, stderr
):
    getattr(logger, helper)(*args)
    entries = history.snapshot()["entries"]
    assert len(entries) == 1
    text = entries[0]["text"]
    assert "\x1b[" in text
    assert str(args[-1]) in text
    assert "[bold" not in text
    terminal = logger.error_console if stderr else logger.console
    assert "\x1b[" in terminal.file.getvalue()
    assert str(args[-1]) in terminal.file.getvalue()


def test_raw_output_preserves_ansi_and_literal_markup(history):
    text = "\x1b[31m[download] package\x1b[0m\n"
    logger.log_output(text)
    assert history.snapshot()["entries"] == [{"id": 1, "text": text}]
    assert logger.console.file.getvalue() == text


def test_rich_capture_preserves_terminal_truecolor(history, monkeypatch):
    monkeypatch.setattr(
        logger,
        "console",
        Console(file=io.StringIO(), force_terminal=True, color_system="truecolor"),
    )
    logger.log_info("[#123456]truecolor[/#123456]")
    assert "\x1b[38;2;18;52;86m" in history.snapshot()["entries"][0]["text"]
    assert "\x1b[38;2;18;52;86m" in logger.console.file.getvalue()


def test_history_is_bounded_with_monotonic_cursors_and_independent_snapshots():
    history = logger.LogHistory(max_entries=3, max_entry_bytes=64)
    for text in ("first", "second", "third", "fourth"):
        history.append(text)
    assert history.snapshot() == {
        "entries": [
            {"id": 2, "text": "second"},
            {"id": 3, "text": "third"},
            {"id": 4, "text": "fourth"},
        ],
        "cursor": 4,
    }
    assert history.snapshot(3) == {
        "entries": [{"id": 4, "text": "fourth"}],
        "cursor": 4,
    }
    assert history.snapshot(4) == {"entries": [], "cursor": 4}
    assert history.snapshot(100) == history.snapshot()
    snapshot = history.snapshot()
    snapshot["entries"][0]["text"] = "mutated"
    assert history.snapshot()["entries"][0]["text"] == "second"


def test_stale_cursor_recovers_from_an_empty_process_history():
    history = logger.LogHistory()
    assert history.snapshot(100) == {"entries": [], "cursor": 0}
    history.append("new process startup")
    assert history.snapshot(100) == {
        "entries": [{"id": 1, "text": "new process startup"}],
        "cursor": 1,
    }


def test_default_history_limit_and_utf8_byte_cap():
    history = logger.LogHistory()
    for _ in range(logger.LOG_HISTORY_LIMIT + 5):
        history.append("entry")
    snapshot = history.snapshot()
    assert len(snapshot["entries"]) == logger.LOG_HISTORY_LIMIT
    assert snapshot["entries"][0]["id"] == 6
    assert snapshot["cursor"] == logger.LOG_HISTORY_LIMIT + 5

    small = logger.LogHistory(max_entry_bytes=64)
    small.append("\x1b[31m" + "\u00e9" * 100)
    text = small.snapshot()["entries"][0]["text"]
    assert len(text.encode("utf-8")) <= 64
    assert text.startswith("\x1b[31m")
    assert text.endswith("\x1b[0m [truncated]\n")
    assert "\ufffd" not in text


def test_history_cursors_are_thread_safe():
    history = logger.LogHistory()

    def append_entries(worker):
        for entry in range(100):
            history.append(f"{worker}:{entry}")
            snapshot = history.snapshot()
            assert all(item["id"] <= snapshot["cursor"] for item in snapshot["entries"])

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(append_entries, range(4)))
    snapshot = history.snapshot()
    assert [entry["id"] for entry in snapshot["entries"]] == list(range(1, 401))
    assert snapshot["cursor"] == 400


def test_python_logging_captures_colors_and_traceback_once(history):
    try:
        raise ValueError("diagnostic traceback")
    except ValueError:
        logging.getLogger("diagnostics.test").exception("Python failure")
    entries = history.snapshot()["entries"]
    assert len(entries) == 1
    assert "\x1b[" in entries[0]["text"]
    assert "Traceback" in entries[0]["text"]
    assert "ValueError: diagnostic traceback" in entries[0]["text"]


def test_repeated_setup_keeps_terminal_handlers_and_deduplicates_records(
    history, monkeypatch
):
    terminal = logging.StreamHandler(io.StringIO())
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        active = logging.getLogger(name)
        monkeypatch.setattr(active, "handlers", [terminal] if name == "uvicorn" else [])
        monkeypatch.setattr(active, "propagate", True)
        monkeypatch.setattr(active, "level", logging.INFO)
    root_handlers = list(logging.getLogger().handlers)
    logger.setup_uvicorn_logging()
    logger.setup_uvicorn_logging()
    assert terminal in logging.getLogger("uvicorn").handlers
    assert all(handler in logging.getLogger().handlers for handler in root_handlers)
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        assert (
            sum(
                isinstance(handler, logger.LogCaptureHandler)
                for handler in logging.getLogger(name).handlers
            )
            == 1
        )
    logging.getLogger("uvicorn.error").info("server startup")
    logging.getLogger("uvicorn.access").info(
        '%s - "%s %s HTTP/%s" %s',
        "127.0.0.1:54321",
        "GET",
        "/api/health",
        "1.1",
        200,
    )
    entries = history.snapshot()["entries"]
    assert len(entries) == 2
    assert "server startup" in entries[0]["text"]
    assert "GET /api/health HTTP/1.1" in entries[1]["text"]
    assert "127.0.0.1" not in entries[1]["text"]
    assert all("\x1b[" in entry["text"] for entry in entries)
    assert "server startup" in terminal.stream.getvalue()


def test_uvicorn_dict_config_captures_before_lifespan_without_duplicates():
    script = """
import json
import logging
import logging.config
from qibocal_report import logger
logging.config.dictConfig(logger.get_uvicorn_log_config())
logging.getLogger("uvicorn.error").info("early startup")
logger.setup_uvicorn_logging()
logger.setup_uvicorn_logging()
logging.getLogger("uvicorn.error").info("later startup")
logging.getLogger("diagnostics.root").warning("root terminal output")
print(json.dumps(logger.log_history.snapshot()))
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    snapshot = json.loads(result.stdout)
    assert len(snapshot["entries"]) == 3
    assert "early startup" in snapshot["entries"][0]["text"]
    assert "later startup" in snapshot["entries"][1]["text"]
    assert "early startup" in result.stderr
    assert "later startup" in result.stderr
    assert "root terminal output" in snapshot["entries"][2]["text"]
    assert "root terminal output" in result.stderr


def test_admin_logs_schema_cursors_and_query_validation(history, monkeypatch):
    monkeypatch.setattr(auth, "_AUTH_ENABLED", True)
    admin = auth.create_user("diagnostics-admin", "password123", "admin")
    headers = {"Authorization": f"Bearer {auth.create_access_token(admin)}"}
    logger.log_info("before lifespan")
    with TestClient(api.app) as client:
        response = client.get("/api/admin/logs?after=0", headers=headers)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        data = response.json()
        assert set(data) == {"entries", "cursor"}
        assert data["cursor"] == 1
        assert set(data["entries"][0]) == {"id", "text"}
        assert isinstance(data["entries"][0]["id"], int)
        assert "\x1b[" in data["entries"][0]["text"]
        logger.log_success("after cursor")
        newer = client.get(
            f"/api/admin/logs?after={data['cursor']}", headers=headers
        ).json()
        assert len(newer["entries"]) == 1
        assert "after cursor" in newer["entries"][0]["text"]
        assert client.get("/api/admin/logs?after=2", headers=headers).json() == {
            "entries": [],
            "cursor": 2,
        }
        expected = history.snapshot()
        recovered = client.get("/api/admin/logs?after=999", headers=headers)
        assert recovered.status_code == 200
        assert recovered.json() == expected
        for after in ("-1", "invalid"):
            assert (
                client.get(
                    f"/api/admin/logs?after={after}", headers=headers
                ).status_code
                == 422
            )


def test_lifespan_startup_rich_log_is_captured_once(history, monkeypatch):
    monkeypatch.setattr(auth, "_AUTH_ENABLED", True)
    monkeypatch.setattr(
        auth, "create_initial_admin_invite_if_needed", lambda: "startup-test-token"
    )
    with TestClient(api.app):
        assert len(history.snapshot()["entries"]) == 1
    text = history.snapshot()["entries"][0]["text"]
    assert "startup-test-token" in text
    assert "\x1b[" in text
