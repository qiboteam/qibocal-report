"""Asking a SLURM queue: the commands, the parsing, one round trip."""

import json
import os
import stat

import pytest
from click.testing import CliRunner

from qibocamp.remote import slurm
from qibocamp.cli import main

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


MACHINE_SQUEUE = """\
101|gpu|train|ann|RUNNING|1:02:03|4:00:00|2|node[01-02]|1200|2026-10-16T08:00:00|2026-10-16T08:01:00
102|gpu|qibocal|{me}|PENDING|0:00|2:00:00|1|(Priority)|900|2026-10-16T09:00:00|N/A
201|cpu|big|bob|RUNNING|5:00|1:00:00|8|cn[01-08]|100|2026-10-16T07:00:00|2026-10-16T07:00:00
202|cpu|big|bob|RUNNING|5:00|1:00:00|8|cn[09-16]|100|2026-10-16T07:00:00|2026-10-16T07:00:00
301|debug|mine|{me}|PENDING|0:00|0:10:00|1|(Resources)|10|2026-10-16T09:30:00|N/A
"""
MACHINE_SINFO = """\
gpu*|up|4|allocated
gpu*|up|2|idle
cpu|up|16|allocated
debug|down|2|down
"""


@pytest.fixture
def fake_machine(tmp_path, monkeypatch):
    """A machine of three partitions, gpu its default; one job each on gpu and debug is ours."""
    me = os.environ.get("USER") or __import__("getpass").getuser()
    for name, text in (("squeue", MACHINE_SQUEUE.format(me=me)), ("sinfo", MACHINE_SINFO)):
        answer = tmp_path / f"{name}.txt"
        answer.write_text(text)
        script = tmp_path / name
        script.write_text(f"#!/bin/sh\ncat {answer}\n")
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    return tmp_path


def test_a_machine_answers_its_known_queues_and_counts_the_rest(fake_machine):
    answer = slurm.query_machine(partitions=["gpu"], timeout=10)
    assert answer["error"] is None and answer["known"] == ["gpu"]
    gpu = answer["queues"]["gpu"]
    assert [job["id"] for job in gpu["jobs"]] == ["101", "102"], "the known partition's jobs, whole"
    assert gpu["summary"]["total_nodes"] == 6 and gpu["summary"]["jobs"] == {"RUNNING": 1, "PENDING": 1}
    lines = {line["partition"]: line for line in answer["partitions"]}
    assert [line["partition"] for line in answer["partitions"]] == ["gpu", "cpu", "debug"], "the known first"
    assert lines["gpu"]["known"] and lines["gpu"]["default"] and lines["gpu"]["mine"] == 1
    assert lines["cpu"] == {"partition": "cpu", "known": False, "default": False, "available": True,
                            "nodes": {"ALLOCATED": 16}, "jobs": {"RUNNING": 2}, "mine": 0}
    assert lines["debug"]["available"] is False and lines["debug"]["mine"] == 1 and lines["debug"]["jobs"] == {"PENDING": 1}


def test_only_the_known_partitions_jobs_travel(fake_machine):
    # Nothing known: counts only, however many jobs the machine holds.
    answer = slurm.query_machine(timeout=10)
    assert answer["queues"] == {} and sum(sum(line["jobs"].values()) for line in answer["partitions"]) == 5
    script = slurm.machine_script(["gpu", "qpu"])
    assert script.count("squeue") == 1, "one squeue for the whole machine"
    with pytest.raises(ValueError, match="Invalid partition"):
        slurm.query_machine(partitions=["gpu; rm -rf ~"], timeout=10)


def test_the_machine_command_prints_json_or_a_table(fake_machine):
    runner = CliRunner()
    result = runner.invoke(main, ["notebook", "queues", "-q", "gpu", "-q", "debug", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert sorted(data["queues"]) == ["debug", "gpu"]
    table = runner.invoke(main, ["notebook", "queues"])
    assert table.exit_code == 0 and "cpu (other)" in table.output
