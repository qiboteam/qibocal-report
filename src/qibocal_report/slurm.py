"""What a SLURM queue is doing: one round trip, parsed.

A notebook session dispatched to a partition waits in its queue, and the
one looking at the session wants to know why — who is ahead, which nodes
are busy, whether the partition is up at all. This module asks the
controller once, through the same SSH destination the session used, with
``squeue``, ``sinfo`` and ``whoami`` in a single remote shell command, and
answers a plain structure. It never polls: how often to ask is the
caller's decision, and the launcher asks sparingly, since every call costs
the controller something.
"""

from __future__ import annotations

import shlex
import subprocess
from datetime import datetime, timezone
from typing import Any

from qibocal_report.notebook import ssh_arguments

SEPARATOR = "---QIBOCAL-QUEUE---"

#: The fields asked of squeue, in order: id, partition, name, user, state,
#: time used, time limit, node count, nodes or reason, priority, submitted, start.
SQUEUE_FORMAT = "%i|%P|%j|%u|%T|%M|%l|%D|%R|%Q|%V|%S"
SINFO_FORMAT = "%P|%a|%D|%T"


def squeue_command(
    partition: str | None = None,
    user: str | None = None,
    states: list[str] | None = None,
) -> list[str]:
    command = ["squeue", "-h", "-o", SQUEUE_FORMAT, "--sort=-p,i"]
    if partition:
        command += ["-p", partition]
    if user:
        command += ["-u", user]
    if states:
        command += ["-t", ",".join(states)]
    return command


def sinfo_command(partition: str | None = None) -> list[str]:
    command = ["sinfo", "-h", "-o", SINFO_FORMAT]
    if partition:
        command += ["-p", partition]
    return command


def shell_script(
    partition: str | None, user: str | None, states: list[str] | None
) -> str:
    """The three questions as one shell command, their answers separated."""
    parts = [
        shlex.join(squeue_command(partition, user, states)),
        f"printf '\\n{SEPARATOR}\\n'",
        shlex.join(sinfo_command(partition)),
        f"printf '\\n{SEPARATOR}\\n'",
        "whoami",
    ]
    return "; ".join(parts)


def parse_squeue(text: str) -> list[dict[str, Any]]:
    jobs = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        if len(fields) < 9:
            continue
        fields += [""] * (12 - len(fields))
        (
            job_id, partition, name, user, state, time_used, time_limit,
            node_count, nodes_or_reason, priority, submitted, start,
        ) = fields[:12]
        pending = state.upper().startswith("PENDING")
        try:
            count = int(node_count)
        except ValueError:
            count = 0
        jobs.append(
            {
                "id": job_id,
                "partition": partition,
                "name": name,
                "user": user,
                "state": state,
                "time": time_used,
                "time_limit": time_limit,
                "node_count": count,
                "nodes": "" if pending else nodes_or_reason,
                "reason": nodes_or_reason.strip("()") if pending else "",
                "priority": priority,
                "submitted": submitted,
                "start": "" if start == "N/A" else start,
            }
        )
    return jobs


def parse_sinfo(text: str) -> list[dict[str, Any]]:
    """Node groups by partition and state; the default partition loses its asterisk."""
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        if len(fields) < 4:
            continue
        partition, available, count, state = fields[:4]
        try:
            nodes = int(count)
        except ValueError:
            nodes = 0
        rows.append(
            {
                "partition": partition.rstrip("*"),
                "default": partition.endswith("*"),
                "available": available,
                "nodes": nodes,
                "state": state,
            }
        )
    return rows


def summarize(jobs: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """The figures the panel shows first: jobs by state, nodes by state."""
    by_state: dict[str, int] = {}
    for job in jobs:
        key = job["state"].split()[0].upper() if job["state"] else "UNKNOWN"
        by_state[key] = by_state.get(key, 0) + 1
    node_states: dict[str, int] = {}
    for row in nodes:
        key = row["state"].rstrip("*~#$@^!%").upper()
        node_states[key] = node_states.get(key, 0) + row["nodes"]
    return {
        "jobs": by_state,
        "nodes": node_states,
        "total_jobs": len(jobs),
        "total_nodes": sum(node_states.values()),
        "available": any(row["available"] == "up" for row in nodes) if nodes else None,
    }


def split_answers(output: str) -> tuple[str, str, str]:
    parts = output.split(SEPARATOR)
    while len(parts) < 3:
        parts.append("")
    return parts[0], parts[1], parts[2].strip().splitlines()[-1].strip() if parts[2].strip() else ""


def query_queue(
    ssh: str | None = None,
    partition: str | None = None,
    user: str | None = None,
    states: list[str] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Ask the controller once — over SSH when a destination is given — and parse.

    The answer carries the jobs, the node groups, the user the question was
    asked as (for a "mine" filter), the summary, and when it was asked.
    """
    script = shell_script(partition, user, states)
    if ssh:
        arguments, destination = ssh_arguments(ssh)
        command = ["ssh", "-o", "BatchMode=yes", *arguments, destination, script]
    else:
        # The system shell by its path: the PATH may be anything, or nothing.
        command = ["/bin/sh", "-c", script]
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Could not run {command[0]}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"The queue did not answer within {timeout:g} s") from exc
    squeue_text, sinfo_text, whoami = split_answers(completed.stdout)
    jobs = parse_squeue(squeue_text)
    nodes = parse_sinfo(sinfo_text)
    error = None
    if completed.returncode != 0 and not jobs and not nodes:
        error = completed.stderr.strip() or f"The queue command failed ({completed.returncode})"
    return {
        "ssh": ssh,
        "partition": partition,
        "user": whoami or None,
        "jobs": jobs,
        "nodes": nodes,
        "summary": summarize(jobs, nodes),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "error": error,
        "stderr": completed.stderr.strip() or None,
    }
