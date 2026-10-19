"""The targets a report shows, gathered from its protocols."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from qibocal_report import auth
from qibocal_report.reports import actions, scanner
from qibocal_report.web import api
from qibocal_report.cli import main


def make_report(root: Path, name: str, protocols: dict[str, list], meta_targets=None) -> Path:
    report = root / name
    report.mkdir(parents=True)
    meta = {"author": "test", "stats": {}, "targets": meta_targets}
    report.joinpath("meta.json").write_text(json.dumps(meta))
    report.joinpath("history.json").write_text(json.dumps(list(protocols)))
    for protocol, targets in protocols.items():
        folder = report / "data" / protocol
        folder.mkdir(parents=True)
        lines = ["id: x", "operation: x", "targets:"]
        for target in targets:
            if isinstance(target, list):
                lines.append(f"- - {target[0]}")
                lines.append(f"  - {target[1]}")
            else:
                lines.append(f"- {target}")
        folder.joinpath("action.yml").write_text("\n".join(lines) + "\n")
    return report


def test_the_protocols_targets_are_gathered_in_order_pairs_kept(tmp_path):
    report = make_report(tmp_path, "run", {"rabi-0": [0, 1], "cz-0": [[0, 1]], "t1-0": [1, 2]})
    assert actions.protocol_targets(report) == [0, 1, [0, 1], 2]
    assert actions.protocol_targets(tmp_path / "nowhere") == []


def test_inferring_writes_next_to_the_session_targets_and_the_scanner_prefers_it(tmp_path):
    report = make_report(tmp_path, "10:00:00_[7]_run", {"rabi-0": [0], "cz-0": [[0, 1]]}, meta_targets=[7])
    scanner.invalidate_report_cache()
    before = next(r for r in scanner.scan_reports(tmp_path) if r.id.endswith("run"))
    assert before.targets == [7], "the session's claim, until the protocols are read"

    counts = actions.infer_targets(tmp_path)
    assert counts == {"reports": 1, "updated": 1, "without_targets": 0}
    meta = json.loads((report / "meta.json").read_text())
    assert meta["targets"] == [7], "the session's own list is kept"
    assert meta["targets-inferred"] == [0, [0, 1]]
    after = next(r for r in scanner.scan_reports(tmp_path) if r.id.endswith("run"))
    assert after.targets == [0, [0, 1]]

    again = actions.infer_targets(tmp_path)
    assert again["updated"] == 0, "nothing to change the second time"


def test_a_report_without_protocol_targets_is_counted_and_left_alone(tmp_path):
    report = make_report(tmp_path, "run", {"calib-0": []}, meta_targets=[3])
    counts = actions.infer_targets(tmp_path)
    assert counts == {"reports": 1, "updated": 0, "without_targets": 1}
    assert "targets-inferred" not in json.loads((report / "meta.json").read_text())


def test_scanning_never_reads_the_protocols_only_inferring_does(tmp_path):
    """The traversal reads each report's `meta.json`, as before; the protocols'
    `action.yml` files are read on request alone, by `infer_targets`. A broken
    one therefore cannot slow or break a scan — and inferring passes over it."""
    report = make_report(tmp_path, "10:00:00_[5]_run", {"rabi-0": [5]}, meta_targets=[5])
    (report / "data" / "rabi-0" / "action.yml").write_text("targets: [unclosed\n")
    scanner.invalidate_report_cache()
    found = next(r for r in scanner.scan_reports(tmp_path) if r.id.endswith("run"))
    assert found.targets == [5]
    assert actions.infer_targets(tmp_path) == {"reports": 1, "updated": 0, "without_targets": 1}


def test_the_command_line_and_the_endpoint_run_it(tmp_path, monkeypatch):
    make_report(tmp_path, "run", {"rabi-0": [2]})
    result = CliRunner().invoke(main, ["report", "targets", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "1 report(s) looked at, 1 updated" in result.output

    make_report(tmp_path, "other", {"rabi-0": [4]})
    api.set_report_root(tmp_path, is_original=True)
    auth.set_auth_enabled(False)
    try:
        with TestClient(api.app) as client:
            response = client.post("/api/admin/reports/infer-targets")
            assert response.status_code == 200, response.text
            assert response.json() == {"reports": 2, "updated": 1, "without_targets": 0}
            assert response.headers["cache-control"] == "no-store"
    finally:
        auth.set_auth_enabled(None)
