"""Protocols on qubit pairs: a target that is not a single qubit."""

from qibocal_report import generator, scanner
from qibocal_report.models import ReportSummary


def test_targets_are_keyed_as_qibocal_keys_them():
    # action.yml gives a pair as a list; qibocal's data and results want the tuple.
    assert generator.normalize_targets([2, 3]) == (2, 3)
    assert generator.normalize_targets([[0, 1], 2]) == ((0, 1), 2)
    assert generator.normalize_targets(2) == 2
    assert generator.normalize_targets("D1") == "D1"
    assert hash(generator.normalize_targets([2, 3]))  # a key at last
    assert generator.target_label((2, 3)) == "2-3"
    assert generator.target_label([2, 3]) == "2-3"
    assert generator.target_label(2) == "2"


def test_a_folder_name_may_hold_pairs():
    assert scanner.parse_targets_text("3") == [3]
    assert scanner.parse_targets_text("0, 1") == [0, 1]
    assert scanner.parse_targets_text("(2, 3)") == [[2, 3]]
    assert scanner.parse_targets_text("[2, 3], [4, 5]") == [[2, 3], [4, 5]]
    assert scanner.parse_targets_text("'D1', (2, 3)") == [[2, 3], "D1"]
    assert scanner.flat_qubits([0, [2, 3], 3]) == [0, 2, 3]


def _report(identifier, targets):
    return ReportSummary(
        id=identifier, path=f"/tmp/{identifier}", date="2026-10-16", targets=targets,
        search_index=" ".join(f"q{q} {q}" for q in scanner.flat_qubits(targets)),
    )


def test_the_filter_knows_a_qubit_in_a_pair_and_the_pair_itself():
    reports = [_report("single", [2]), _report("pair", [[2, 3]]), _report("other", [[4, 5]])]
    by_qubit = scanner.filter_reports(reports, qubits=["3"])
    assert [r.id for r in by_qubit] == ["pair"], "a qubit in a pair counts"
    by_q = scanner.filter_reports(reports, qubits=["q2"])
    assert {r.id for r in by_q} == {"single", "pair"}
    by_pair = scanner.filter_reports(reports, qubits=["2-3"])
    assert [r.id for r in by_pair] == ["pair"], "a pair asks for that pair"
    assert scanner.filter_reports(reports, qubits=["4-5"])[0].id == "other"
