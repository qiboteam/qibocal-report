"""Incremental generation and live subscription coverage."""

import json
import shutil
import sys
from types import ModuleType, SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from qibocal_report import api, auth, generator, live
from qibocal_report.live_inputs import metadata_inputs, protocol_inputs
from qibocal_report.models import ProtocolDetail


@pytest.fixture
def report_dir(tmp_path, monkeypatch):
    report = tmp_path / "run"
    report.mkdir()
    (report / "meta.json").write_text('{"author": "test", "stats": {}}')
    for task in ("rabi-0", "ramsey-0"):
        directory = report / "data" / task
        directory.mkdir(parents=True)
        (directory / "data.json").write_text('{"value": 1}')
    (report / "history.json").write_text('["rabi-0", "ramsey-0"]')
    generator.write_protocol_cache(
        report,
        [
            ProtocolDetail(id=task, name=task, html="original")
            for task in ("rabi-0", "ramsey-0")
        ],
    )
    monkeypatch.setattr(api, "REPORT_ROOT_DIR", tmp_path)
    monkeypatch.setattr(live, "LIVE_POLL_INTERVAL", 0.01)
    auth.set_auth_enabled(False)
    yield report
    auth.set_auth_enabled(None)


def test_input_fingerprints_ignore_outputs_and_metadata(report_dir):
    before = protocol_inputs(report_dir)
    meta_before = metadata_inputs(report_dir)
    (report_dir / "report" / "another.json").write_text("{}")
    (report_dir / ".qibocal-generation-result.json").write_text("{}")
    (report_dir / "meta.json").write_text('{"author": "changed"}')
    assert protocol_inputs(report_dir) == before
    assert metadata_inputs(report_dir) != meta_before
    data = report_dir / "data" / "rabi-0" / "data.json"
    data.write_text('{"value": 2}')
    after = protocol_inputs(report_dir)
    assert after["rabi-0"] != before["rabi-0"]
    assert after["ramsey-0"] == before["ramsey-0"]
    data.unlink()
    assert protocol_inputs(report_dir)["rabi-0"] != after["rabi-0"]


def test_incremental_generation_preserves_cache_and_deduplicates(
    report_dir, monkeypatch
):
    previous = protocol_inputs(report_dir)
    (report_dir / "data" / "rabi-0" / "data.json").write_text('{"new": true}')
    current = protocol_inputs(report_dir)
    calls = []

    def generate(path, ids):
        calls.append(ids)
        return [ProtocolDetail(id=key, name=key, html="updated") for key in ids], None

    monkeypatch.setattr(live, "_generate_qibocal_protocols", generate)
    outputs, removed = live.refresh_live_protocols(report_dir, current, previous)
    assert [p.id for p in outputs] == ["rabi-0"]
    assert not removed
    # A second subscriber observes the same change but reuses its cached result.
    outputs, _ = live.refresh_live_protocols(report_dir, current, previous)
    assert outputs[0].html == "updated"
    assert calls == [["rabi-0"]]
    cached = {p.id: p for p in generator.load_cached_protocols(report_dir)}
    assert cached["rabi-0"].html == "updated"
    assert cached["ramsey-0"].html == "original"
    assert live.refresh_live_protocols(report_dir, current, current) == ([], [])


def test_new_and_removed_tasks(report_dir, monkeypatch):
    previous = protocol_inputs(report_dir)
    shutil.rmtree(report_dir / "data" / "ramsey-0")
    new = report_dir / "data" / "rabi-1"
    new.mkdir()
    (new / "data.json").write_text("{}")
    (report_dir / "history.json").write_text('["rabi-0", "rabi-1"]')
    current = protocol_inputs(report_dir)
    calls = []

    def generate(path, ids):
        calls.append(ids)
        return [ProtocolDetail(id=key, name=key) for key in ids], None

    monkeypatch.setattr(live, "_generate_qibocal_protocols", generate)
    outputs, removed = live.refresh_live_protocols(report_dir, current, previous)
    assert calls == [["rabi-1"]]
    assert [p.id for p in outputs] == ["rabi-1"]
    assert removed == ["ramsey-0"]
    assert [p.id for p in generator.load_cached_protocols(report_dir)] == [
        "rabi-0",
        "rabi-1",
    ]


def test_failed_generation_does_not_destroy_good_cache(report_dir, monkeypatch):
    previous = protocol_inputs(report_dir)
    (report_dir / "data" / "rabi-0" / "data.json").write_text("{}")
    monkeypatch.setattr(
        live, "_generate_qibocal_protocols", lambda *_: (None, "Unfinished write")
    )
    with pytest.raises(RuntimeError, match="Unfinished write"):
        live.refresh_live_protocols(report_dir, protocol_inputs(report_dir), previous)
    assert all(
        p.html == "original" for p in generator.load_cached_protocols(report_dir)
    )


@pytest.mark.parametrize("with_pending", [False, True])
def test_native_selection_loads_and_plots_only_changed_task(
    tmp_path, monkeypatch, with_pending
):
    loaded, plotted = [], []
    output = ModuleType("qibocal.auto.output")
    output.Output = SimpleNamespace(load=lambda _: pytest.fail("Loaded entire output"))
    tasks = ModuleType("qibocal.auto.task")

    def load(path):
        loaded.append(path.name)
        if path.name == "pending-0":
            raise FileNotFoundError("Task parameters are still being written")
        return SimpleNamespace(task=SimpleNamespace(operation_name="rabi", targets=[0]))

    tasks.Completed = SimpleNamespace(load=load)
    report = ModuleType("qibocal.cli.report")

    def figures(completed, target):
        plotted.append(target)
        return [{"data": [], "layout": {}}], "<p>fit</p>"

    report.generate_figures_and_report = figures
    monkeypatch.setitem(sys.modules, "qibocal.auto.output", output)
    monkeypatch.setitem(sys.modules, "qibocal.auto.task", tasks)
    monkeypatch.setitem(sys.modules, "qibocal.cli.report", report)
    selected = ["rabi-1", "pending-0"] if with_pending else ["rabi-1"]
    protocols, error = generator._generate_qibocal_protocols_native(tmp_path, selected)
    assert error is None
    assert loaded == selected
    assert plotted == [0]
    assert protocols[0].id == "rabi-1"
    assert protocols[0].status == "success"
    if with_pending:
        assert protocols[1].id == "pending-0"
        assert protocols[1].status == "error"
        assert "still being written" in protocols[1].error


def test_worker_forwards_selection_and_uses_fresh_process(tmp_path, monkeypatch):
    import subprocess

    def run(command, **options):
        assert command[:3] == [sys.executable, "-m", "qibocal_report.generation_worker"]
        assert json.loads(command[-1]) == ["rabi-1"]
        (tmp_path / command[-2]).write_text(
            json.dumps({"protocols": [{"id": "rabi-1", "name": "Rabi"}], "error": None})
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    outputs, error = generator._generate_qibocal_protocols(tmp_path, ["rabi-1"])
    assert error is None
    assert outputs[0].id == "rabi-1"


def test_live_socket_pushes_changed_protocol_and_stops(report_dir, monkeypatch):
    calls = []
    monkeypatch.setattr(
        live,
        "get_report_detail",
        lambda *_: SimpleNamespace(model_dump=lambda: {"id": "run"}),
    )

    def generate(path, ids):
        calls.append(ids)
        return [ProtocolDetail(id=key, name=key, html="live") for key in ids], None

    monkeypatch.setattr(live, "_generate_qibocal_protocols", generate)
    with TestClient(api.app) as client:
        with client.websocket_connect("/ws/live/reports/run") as ws:
            assert ws.receive_json() == {"type": "live", "active": True}
            assert ws.receive_json()["type"] == "snapshot"
            assert ws.receive_json()["type"] == "metadata"
            (report_dir / "data" / "rabi-0" / "data.json").write_text('{"new": 2}')
            assert ws.receive_json()["type"] == "metadata"
            update = ws.receive_json()
            assert update["type"] == "update"
            assert [p["id"] for p in update["protocols"]] == ["rabi-0"]
            assert update["protocols"][0]["html"] == "live"
            assert not update["removed"]
            ws.send_text("ping")
            assert ws.receive_text() == "pong"
        assert calls == [["rabi-0"]]


@pytest.mark.parametrize("role", [None, "viewer", "editor", "admin"])
def test_live_socket_permissions(report_dir, role):
    auth.set_auth_enabled(True)
    token = None
    if role:
        user = auth.create_user(role, "password", role)
        token = auth.create_access_token(user)
    url = "/ws/live/reports/run" + (f"?token={token}" if token else "")
    with TestClient(api.app) as client:
        if role in ("editor", "admin"):
            with client.websocket_connect(url) as ws:
                assert ws.receive_json()["type"] == "live"
        else:
            with pytest.raises(WebSocketDisconnect) as error:
                with client.websocket_connect(url):
                    pytest.fail("Viewer subscription accepted")
            assert error.value.code == 1008


def test_live_socket_revokes_changed_role(report_dir):
    auth.set_auth_enabled(True)
    user = auth.create_user("editor", "password", "editor")
    token = auth.create_access_token(user)
    with TestClient(api.app) as client:
        with client.websocket_connect(f"/ws/live/reports/run?token={token}") as ws:
            assert ws.receive_json()["type"] == "live"
            auth.update_user_role(user["id"], "viewer")
            while (message := ws.receive_json())["type"] != "error":
                pass
            assert "editor access" in message["message"]
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()


def test_live_socket_rejects_outside_root(report_dir):
    with TestClient(api.app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/live/reports/..%2F.."):
                pytest.fail("Outside-root subscription accepted")


def test_live_socket_supports_single_report_root(report_dir, monkeypatch):
    monkeypatch.setattr(api, "REPORT_ROOT_DIR", report_dir)
    with TestClient(api.app) as client:
        with client.websocket_connect("/ws/live/reports/run") as ws:
            assert ws.receive_json()["type"] == "live"


def test_failed_task_is_not_acknowledged_by_a_sibling_update(report_dir, monkeypatch):
    previous = protocol_inputs(report_dir)
    (report_dir / "data" / "rabi-0" / "data.json").write_text('{"changed": true}')
    failed_inputs = protocol_inputs(report_dir)
    monkeypatch.setattr(
        live, "_generate_qibocal_protocols", lambda *_: (None, "Incomplete input")
    )
    with pytest.raises(RuntimeError):
        live.refresh_live_protocols(report_dir, failed_inputs, previous)
    # The watcher remembers observing the failure, but the cache must not.
    (report_dir / "data" / "ramsey-0" / "data.json").write_text('{"changed": true}')

    def generate(path, ids):
        assert ids == ["ramsey-0"]
        return [ProtocolDetail(id="ramsey-0", name="Ramsey", html="updated")], None

    monkeypatch.setattr(live, "_generate_qibocal_protocols", generate)
    current = protocol_inputs(report_dir)
    live.refresh_live_protocols(report_dir, current, failed_inputs)
    saved = live.cached_inputs(report_dir, current)
    assert saved["rabi-0"] == previous["rabi-0"]
    assert saved["rabi-0"] != current["rabi-0"]
    assert saved["ramsey-0"] == current["ramsey-0"]


def test_native_protocol_errors_preserve_good_plots_and_fingerprints(
    report_dir, monkeypatch
):
    previous = protocol_inputs(report_dir)
    (report_dir / "data" / "rabi-0" / "data.json").write_text("{}")
    current = protocol_inputs(report_dir)
    failure = ProtocolDetail(
        id="rabi-0", name="Rabi", status="error", error="Data is incomplete"
    )
    monkeypatch.setattr(
        live, "_generate_qibocal_protocols", lambda *_: ([failure], None)
    )
    outputs, _ = live.refresh_live_protocols(report_dir, current, previous)
    assert outputs[0].status == "error"
    assert outputs[0].error == "Data is incomplete"
    assert outputs[0].html == "original"
    cached = {p.id: p for p in generator.load_cached_protocols(report_dir)}
    assert cached["rabi-0"].status == "success"
    assert cached["rabi-0"].html == "original"
    assert live.cached_inputs(report_dir, current)["rabi-0"] == previous["rabi-0"]


def test_legacy_cache_removes_previously_deleted_protocols(report_dir):
    shutil.rmtree(report_dir / "data" / "ramsey-0")
    (report_dir / "history.json").write_text('["rabi-0"]')
    current = protocol_inputs(report_dir)
    baseline = live.cached_inputs(report_dir, current)
    outputs, removed = live.refresh_live_protocols(report_dir, current, baseline)
    assert not outputs
    assert removed == ["ramsey-0"]
    assert [p.id for p in generator.load_cached_protocols(report_dir)] == ["rabi-0"]


def test_subscription_replays_updates_missed_while_disconnected(report_dir):
    current = protocol_inputs(report_dir)
    generator.write_protocol_cache(
        report_dir, [ProtocolDetail(id="rabi-0", name="Rabi", html="updated-elsewhere")]
    )
    (report_dir / "report" / ".live-inputs.json").write_text(json.dumps(current))
    with TestClient(api.app) as client:
        with client.websocket_connect("/ws/live/reports/run") as ws:
            assert ws.receive_json()["type"] == "live"
            snapshot = ws.receive_json()
            assert snapshot["type"] == "snapshot"
            assert [p["id"] for p in snapshot["protocols"]] == ["rabi-0"]
            assert snapshot["protocols"][0]["html"] == "updated-elsewhere"


def test_input_manifest_alone_is_not_a_plot_cache(tmp_path):
    live.cached_inputs(tmp_path, {})
    assert not generator.has_cached_report(tmp_path)


def test_legacy_per_task_cache_ignores_live_fingerprints_and_temporary_files(
    report_dir,
):
    original = generator.load_cached_protocols(report_dir)
    (report_dir / "report" / "protocols.json").unlink()
    for protocol in original:
        (report_dir / "report" / f"{protocol.id}.json").write_text(
            protocol.model_dump_json()
        )
    current = protocol_inputs(report_dir)
    assert live.cached_inputs(report_dir, current) == current
    (report_dir / "report" / ".protocols-temporary.json").write_text("partial json")
    assert generator.load_cached_protocols(report_dir) == original


def test_initial_snapshot_and_fingerprints_share_a_lock(report_dir, monkeypatch):
    from contextlib import contextmanager

    active = False

    @contextmanager
    def lock(_):
        nonlocal active
        active = True
        try:
            yield
        finally:
            active = False

    def read_cache(_):
        assert active
        return [ProtocolDetail(id="rabi-0", name="Rabi")]

    def read_inputs(_, current):
        assert active
        return current

    monkeypatch.setattr(live, "report_generation_lock", lock)
    monkeypatch.setattr(live, "load_cached_protocols", read_cache)
    monkeypatch.setattr(live, "cached_inputs", read_inputs)
    inputs = {"rabi-0": []}
    protocols, baseline = live.live_initial_state(report_dir, inputs)
    assert protocols[0].id == "rabi-0"
    assert baseline == inputs
