import json

import pytest

from qibocal_report.scanner import (
    compute_filter_stats,
    filter_reports,
    parse_report_directory,
)


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
