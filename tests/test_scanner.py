import json
import os
from pathlib import Path

import pytest

from qibocal_report.scanner import (
    IGNORED_DIRS,
    compute_filter_stats,
    filter_reports,
    get_directory_mtime,
    get_report_detail,
    is_report_directory,
    parse_report_directory,
    scan_reports,
)


@pytest.fixture
def make_report():
    def create(path, report_format="standard"):
        path.mkdir(parents=True, exist_ok=True)
        if report_format == "standard":
            (path / "meta.json").write_text(
                json.dumps({"title": "Session report"}), encoding="utf-8"
            )
            (path / "history.json").write_text("{}", encoding="utf-8")
            for name in ("platform", "new_platform", "data"):
                (path / name).mkdir()
        elif report_format == "cached":
            (path / "report").mkdir()
            (path / "report" / "meta.json").write_text("{}", encoding="utf-8")
        else:
            (path / "data" / "rabi-0").mkdir(parents=True)
            (path / "data" / "rabi-0" / "action.yml").write_text("{}", encoding="utf-8")
        return path

    return create


@pytest.mark.parametrize(
    "root_path",
    [".cache/qibocal/agent/runs/platinum", ".cache", ".hidden/runs", "build"],
)
@pytest.mark.parametrize("report_format", ["standard", "cached", "raw"])
def test_discovery_boundary(tmp_path, make_report, root_path, report_format):
    root = tmp_path / root_path
    report_id = "sessions/cdb13be1d07247478469c9538e1556f7"
    report_dir = make_report(root / report_id, report_format)
    make_report(report_dir / "nested_report")

    reports = scan_reports(root)

    assert [report.id for report in reports] == [report_id]
    assert reports[0].path == str(report_dir)
    assert is_report_directory(report_dir, root)
    detail = get_report_detail(root, report_id)
    assert detail is not None
    assert detail.id == report_id


@pytest.mark.parametrize("name", sorted(IGNORED_DIRS) + [".hidden"])
def test_excluded_descendants(tmp_path, make_report, name):
    root = tmp_path / ".cache" / "runs"
    make_report(root / "sessions" / "visible")
    excluded = make_report(root / name)
    make_report(excluded / "nested")
    make_report(root / "sessions" / name / "nested")

    assert [report.id for report in scan_reports(root)] == ["sessions/visible"]
    for report_id in (name, f"{name}/nested", f"sessions/{name}/nested"):
        assert not is_report_directory(root / report_id, root)
        assert get_report_detail(root, report_id) is None

    before = get_directory_mtime(root)
    future = before + 10
    os.utime(excluded / "meta.json", (future, future))
    os.utime(excluded, (future, future))
    assert get_directory_mtime(root) == before


@pytest.mark.parametrize("name", ["report", ".cache", ".hidden", "build"])
def test_selected_root_is_report(tmp_path, make_report, monkeypatch, name):
    root = make_report(tmp_path / ".cache" / "runs" / name)
    make_report(root / "sessions" / "nested")

    reports = scan_reports(root)

    assert [report.id for report in reports] == [name]
    assert reports[0].path == str(root)
    assert is_report_directory(root, root)
    detail = get_report_detail(root, name)
    assert detail is not None
    assert detail.id == name
    monkeypatch.chdir(root.parent)
    relative_detail = get_report_detail(Path(name), name)
    assert relative_detail is not None
    assert relative_detail.id == name


@pytest.mark.parametrize("root_is_report", [False, True])
@pytest.mark.parametrize("metadata", ["meta.json", "history.json", "report/meta.json"])
def test_cache_invalidation_beneath_ignored_ancestor(
    tmp_path, make_report, root_is_report, metadata
):
    root = tmp_path / ".cache" / "runs"
    report_dir = root if root_is_report else root / "sessions" / "session"
    make_report(report_dir)
    meta_file = report_dir / metadata
    meta_file.parent.mkdir(exist_ok=True)
    meta_file.write_text("{}", encoding="utf-8")
    reports = scan_reports(root)
    assert len(reports) == 1
    assert scan_reports(root) is reports

    before = get_directory_mtime(root)
    meta_file.write_text(json.dumps({"title": "Updated report"}), encoding="utf-8")
    future = before + 10
    os.utime(meta_file, (future, future))

    assert get_directory_mtime(root) == future
    updated = scan_reports(root)
    assert updated is not reports
    assert [report.id for report in updated] == [report.id for report in reports]
    if metadata == "meta.json":
        assert updated[0].title == "Updated report"


@pytest.mark.parametrize(
    ("meta", "expected_date"),
    [
        ({}, ""),
        ({"date": None}, ""),
        ({"date": ""}, ""),
        ({"date": "2024-01-02"}, "2024-01-02"),
        ({"date": "2024-01-02T12:34:56"}, "2024-01-02"),
    ],
)
def test_report_date(tmp_path, meta, expected_date):
    report_dir = tmp_path / "report"
    report_dir.mkdir()
    (report_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    report = parse_report_directory(report_dir, tmp_path)

    assert report.date == expected_date
    assert report.model_dump()["date"] == expected_date


def test_undated_reports_in_filters_and_stats(tmp_path):
    reports = []
    for name, date in [("undated", None), ("dated", "2024-01-02")]:
        report_dir = tmp_path / name
        report_dir.mkdir()
        (report_dir / "meta.json").write_text(
            json.dumps({"date": date}), encoding="utf-8"
        )
        reports.append(parse_report_directory(report_dir, tmp_path))

    assert len(filter_reports(reports)) == 2
    for date_range in [
        {"start_date": "2024-01-01"},
        {"end_date": "2024-01-03"},
        {"start_date": "2024-01-01", "end_date": "2024-01-03"},
    ]:
        assert [
            report.id for report in filter_reports(reports, **date_range)
        ] == ["dated"]

    stats = compute_filter_stats(reports)
    assert stats.total_reports == 2
    assert [bin.model_dump() for bin in stats.date_histogram] == [
        {"date": "2024-01-02", "count": 1}
    ]
