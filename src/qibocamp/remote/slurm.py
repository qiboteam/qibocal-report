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

import re
import shlex
import subprocess
from datetime import datetime, timezone
from typing import Any

from qibocamp.remote.notebook import ssh_arguments

SEPARATOR = "---QIBOCAMP-QUEUE---"

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


# --- A whole machine, in one round trip ----------------------------------------

#: What a count line starts with, among the job lines of a machine's answer.
COUNT_PREFIX = "#count|"

#: A partition name as SLURM writes them: what may go into the filter.
PARTITION = re.compile(r"[A-Za-z0-9_.-]+")

#: Keeps the jobs of the partitions asked for, and counts every job by partition,
#: state, and whether it is the caller's: one squeue for the whole machine, and
#: only what is shown travels back.
AWK_FILTER = (
    'BEGIN { n = split(keep, wanted, ","); for (i = 1; i <= n; i++) if (wanted[i] != "") keepers[wanted[i]] = 1 }'
    ' { split($5, state, " "); counts[$2 "|" toupper(state[1]) "|" ($4 == me)]++; if ($2 in keepers) print }'
    ' END { for (key in counts) print "#count|" key "|" counts[key] }'
)


def machine_script(partitions: list[str]) -> str:
    """squeue once, filtered there; sinfo for every partition; whoami — as one shell command."""
    keep = ",".join(partitions)
    squeue = shlex.join(["squeue", "-h", "-o", SQUEUE_FORMAT, "--sort=-p,i"])
    awk = shlex.join(["awk", "-F", "|", "-v", f"keep={keep}", "-v", "me=$ME", AWK_FILTER]).replace("'me=$ME'", '"me=$me"')
    return "; ".join([
        "me=$(whoami)",
        f"{squeue} | {awk}",
        f"printf '\\n{SEPARATOR}\\n'",
        shlex.join(sinfo_command()),
        f"printf '\\n{SEPARATOR}\\n'",
        'echo "$me"',
    ])


def parse_counts(text: str) -> list[dict[str, Any]]:
    """The count lines: jobs by partition, state, and whether they are the caller's."""
    counts = []
    for line in text.splitlines():
        if not line.startswith(COUNT_PREFIX):
            continue
        fields = line[len(COUNT_PREFIX):].split("|")
        if len(fields) < 4:
            continue
        partition, state, mine, number = fields[:4]
        try:
            counts.append({"partition": partition, "state": state or "UNKNOWN", "mine": mine == "1", "jobs": int(number)})
        except ValueError:
            continue
    return counts


def machine_overview(
    known: list[str], jobs: list[dict[str, Any]], nodes: list[dict[str, Any]], counts: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Each known partition's queue, as `query_queue` answers it, and a line for every partition there."""
    queues = {}
    for partition in known:
        own_jobs = [job for job in jobs if job["partition"] == partition]
        own_nodes = [row for row in nodes if row["partition"] == partition]
        queues[partition] = {"jobs": own_jobs, "nodes": own_nodes, "summary": summarize(own_jobs, own_nodes)}
    lines: dict[str, dict[str, Any]] = {}

    def line(partition: str) -> dict[str, Any]:
        return lines.setdefault(partition, {
            "partition": partition, "known": partition in known, "default": False,
            "available": None, "nodes": {}, "jobs": {}, "mine": 0,
        })

    for row in nodes:
        entry = line(row["partition"])
        entry["default"] = entry["default"] or row["default"]
        entry["available"] = bool(entry["available"]) or row["available"] == "up"
        key = row["state"].rstrip("*~#$@^!%").upper()
        entry["nodes"][key] = entry["nodes"].get(key, 0) + row["nodes"]
    for count in counts:
        entry = line(count["partition"])
        entry["jobs"][count["state"]] = entry["jobs"].get(count["state"], 0) + count["jobs"]
        entry["mine"] += count["jobs"] if count["mine"] else 0
    for partition in known:
        line(partition)
    # The known first, as asked; then the others, by name.
    ordered = sorted(lines.values(), key=lambda entry: (not entry["known"], known.index(entry["partition"]) if entry["known"] else 0, entry["partition"]))
    return queues, ordered


def query_machine(ssh: str | None = None, partitions: list[str] | None = None, timeout: float = 30.0) -> dict[str, Any]:
    """Ask a machine's controller once for the queues of `partitions`, and a line for every partition.

    One squeue for the whole machine, filtered on the machine itself: the
    jobs of the partitions asked for travel back, and only counts for the
    rest — however large the cluster, the answer is as large as what is
    shown. Each partition asked for is answered as `query_queue` would.
    """
    known = list(dict.fromkeys(partitions or []))
    for partition in known:
        if not PARTITION.fullmatch(partition):
            raise ValueError(f"Invalid partition name: {partition!r}")
    script = machine_script(known)
    if ssh:
        arguments, destination = ssh_arguments(ssh)
        command = ["ssh", "-o", "BatchMode=yes", *arguments, destination, script]
    else:
        command = ["/bin/sh", "-c", script]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Could not run {command[0]}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"The queues did not answer within {timeout:g} s") from exc
    squeue_text, sinfo_text, whoami = split_answers(completed.stdout)
    jobs = parse_squeue("\n".join(line for line in squeue_text.splitlines() if not line.startswith(COUNT_PREFIX)))
    counts = parse_counts(squeue_text)
    nodes = parse_sinfo(sinfo_text)
    queues, lines = machine_overview(known, jobs, nodes, counts)
    stderr = completed.stderr.strip() or None
    error = None
    if not jobs and not counts and not nodes and (stderr or completed.returncode != 0):
        error = stderr or f"The queue command failed ({completed.returncode})"
    return {
        "ssh": ssh,
        "user": whoami or None,
        "known": known,
        "queues": queues,
        "partitions": lines,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "error": error,
        "stderr": stderr,
    }
