"""Asking a SLURM queue: the commands, the parsing, one round trip."""

import json
import os
import stat

import pytest
from click.testing import CliRunner

from qibocal_report.remote import slurm
from qibocal_report.cli import main

SQUEUE = """\
101|gpu|train|ann|RUNNING|1:02:03|4:00:00|2|node[01-02]|1200|2026-10-16T08:00:00|2026-10-16T08:01:00
102|gpu|qibocal|me|PENDING|0:00|2:00:00|1|(Priority)|900|2026-10-16T09:00:00|N/A
"""
SINFO = """\
gpu*|up|4|allocated
gpu*|up|2|idle
gpu*|up|1|drained
"""


def test_the_commands_ask_exactly_what_is_needed():
    assert slurm.squeue_command("gpu", "me", ["PENDING", "RUNNING"]) == [
        "squeue", "-h", "-o", slurm.SQUEUE_FORMAT, "--sort=-p,i", "-p", "gpu", "-u", "me", "-t", "PENDING,RUNNING",
    ]
    assert slurm.sinfo_command() == ["sinfo", "-h", "-o", slurm.SINFO_FORMAT]
    script = slurm.shell_script("gpu", None, None)
    assert script.count(slurm.SEPARATOR) == 2 and script.endswith("whoami")


def test_the_answers_are_parsed_into_jobs_and_nodes():
    jobs = slurm.parse_squeue(SQUEUE)
    assert [job["id"] for job in jobs] == ["101", "102"]
    assert jobs[0]["nodes"] == "node[01-02]" and jobs[0]["reason"] == ""
    assert jobs[1]["nodes"] == "" and jobs[1]["reason"] == "Priority" and jobs[1]["start"] == ""
    assert jobs[0]["node_count"] == 2
    nodes = slurm.parse_sinfo(SINFO)
    assert nodes[0] == {"partition": "gpu", "default": True, "available": "up", "nodes": 4, "state": "allocated"}
    summary = slurm.summarize(jobs, nodes)
    assert summary["jobs"] == {"RUNNING": 1, "PENDING": 1}
    assert summary["nodes"] == {"ALLOCATED": 4, "IDLE": 2, "DRAINED": 1}
    assert summary["total_nodes"] == 7 and summary["available"] is True


@pytest.fixture
def fake_slurm(tmp_path, monkeypatch):
    """squeue and sinfo as shell scripts answering the texts above."""
    for name, text in (("squeue", SQUEUE), ("sinfo", SINFO)):
        answer = tmp_path / f"{name}.txt"
        answer.write_text(text)
        script = tmp_path / name
        script.write_text(f"#!/bin/sh\ncat {answer}\n")
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    return tmp_path


def test_one_local_round_trip(fake_slurm):
    answer = slurm.query_queue(partition="gpu", timeout=10)
    assert answer["error"] is None
    assert [job["id"] for job in answer["jobs"]] == ["101", "102"]
    assert answer["summary"]["total_nodes"] == 7
    assert answer["user"], "whoami answered"
    assert answer["fetched_at"].endswith("+00:00")


def test_the_command_line_prints_json_or_a_table(fake_slurm):
    runner = CliRunner()
    result = runner.invoke(main, ["notebook", "queue", "--queue", "gpu", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["partition"] == "gpu" and len(data["jobs"]) == 2
    table = runner.invoke(main, ["notebook", "queue", "--queue", "gpu", "--state", "PENDING"])
    assert table.exit_code == 0, table.output
    assert "102" in table.output


def test_a_missing_squeue_is_an_error_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    answer = slurm.query_queue(partition="gpu", timeout=10)
    assert answer["jobs"] == [] and answer["error"]
