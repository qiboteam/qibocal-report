"""Two reports on qubit pairs, as they came in: a CHSH and a JAZZ experiment.

Both failed to plot — the JAZZ one with "unhashable type: 'list'", the CHSH
one with the limit lines and no data — for one reason: a pair target is a
list off the YAML, and qibocal keys its data and results by the tuple. The
sample archive holds both, with caches written by the fixed generator; with
qibocal installed, the plots are generated again from the data.
"""

import importlib.util
import shutil

import pytest

from conftest import sample_reports
from qibocamp.reports import generator

from qibocamp.reports import scanner

CHSH = "13:36:40_[(2, 4)]_chsh"
JAZZ = "12:07:17_[(2, 3)]_jazz"


@pytest.fixture
def reports(tmp_path):
    root = sample_reports(tmp_path / "reports")
    scanner.invalidate_report_cache()
    return root


def test_the_pair_reports_are_found_with_their_pairs(reports):
    by_id = {report.id: report for report in scanner.scan_reports(reports)}
    assert by_id[CHSH].targets == [[2, 4]], "the pair, read off the folder name"
    assert by_id[JAZZ].targets == [[2, 3]]
    assert by_id[CHSH].protocols == ["chsh"] and by_id[JAZZ].protocols == ["jazz"]
    assert "q2 2" in by_id[CHSH].search_index and "2-4" in by_id[CHSH].search_index
    pairs = scanner.filter_reports(list(by_id.values()), qubits=["2-3"])
    assert [report.id for report in pairs] == [JAZZ]


def test_the_caches_hold_the_plots_as_they_should_be(reports):
    chsh = generator.load_cached_protocols(reports / CHSH)
    assert [p.status for p in chsh] == ["success"] and chsh[0].error is None
    names = [trace.get("name") for trace in chsh[0].figures[0]["data"]]
    assert "Bare" in names, "the CHSH curve, not only its limits"
    assert chsh[0].figures[0]["id"] == "chsh-0-q2-4"

    jazz = generator.load_cached_protocols(reports / JAZZ)
    assert [p.status for p in jazz] == ["success"] and jazz[0].error is None
    names = [trace.get("name", "").strip() for trace in jazz[0].figures[0]["data"]]
    assert "Data" in names and "Fit" in names
    assert "fitting-table" in jazz[0].html


@pytest.mark.skipif(importlib.util.find_spec("qibocal") is None, reason="qibocal is not installed")
def test_the_plots_are_generated_again_from_the_data(reports):
    for name, curve in ((CHSH, "Bare"), (JAZZ, "Fit")):
        shutil.rmtree(reports / name / "report")
        protocols, error = generator._generate_qibocal_protocols_native(reports / name)
        assert error is None, error
        assert [p.status for p in protocols] == ["success"], [p.error for p in protocols]
        names = [trace.get("name", "").strip() for trace in protocols[0].figures[0]["data"]]
        assert curve in names
