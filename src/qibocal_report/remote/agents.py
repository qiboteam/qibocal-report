"""Agent configurations kept here for another machine, written there.

qibocal-agent and qibocal-mcp-remote read `agent.json` on the machine they
run on. A configuration meant for an access node — an assistant running
there — is kept by the launcher on this machine and pushed to that one: the
named entries it owns are merged into the remote `agents`, everything else
in the remote file is left as it is. Only the configuration travels, never
environments or keys.
"""

import json
import re
import shlex
import subprocess

import click

from qibocal_report.remote.notebook import ssh_arguments

# What the remote side runs: the standard library only, on the system python3.
MERGE = r"""
import json, os, sys, tempfile
from pathlib import Path

request = json.loads(sys.argv[1])
custom = os.environ.get("QIBOCAL_MCP_CONFIG_DIR")
xdg = os.environ.get("XDG_CONFIG_HOME")
directory = Path(custom) if custom else (Path(xdg) / "qibocal" if xdg else Path.home() / ".config" / "qibocal")
path = directory / "agent.json"
try:
    document = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
except ValueError as error:
    sys.exit(f"{path} is not valid JSON ({error}); left as it is")
if not isinstance(document, dict):
    sys.exit(f"{path} does not hold a JSON object; left as it is")
agents = document.get("agents") if isinstance(document.get("agents"), dict) else {}
agents.update(request["agents"])
for name in request["remove"]:
    agents.pop(name, None)
if agents:
    document["agents"] = agents
else:
    document.pop("agents", None)
directory.mkdir(parents=True, exist_ok=True)
handle, temporary = tempfile.mkstemp(dir=directory, prefix=".agent.json.")
with os.fdopen(handle, "w", encoding="utf-8") as file:
    json.dump(document, file, indent=2)
    file.write("\n")
os.replace(temporary, path)
print(json.dumps({"path": str(path), "agents": sorted(agents)}))
"""

NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def push(ssh: str, agents: dict, remove: list[str] | None = None, timeout: float = 60.0) -> dict:
    """Merge `agents` into the remote agent.json, dropping the names in `remove`."""
    remove = list(remove or [])
    for name in [*agents, *remove]:
        if not NAME.fullmatch(name):
            raise click.ClickException(f"Invalid agent name: {name!r}.")
    if not all(isinstance(entry, dict) for entry in agents.values()):
        raise click.ClickException("Every agent configuration must be a JSON object.")
    options, destination = ssh_arguments(ssh)
    request = json.dumps({"agents": agents, "remove": remove})
    remote = f"python3 -c {shlex.quote(MERGE)} {shlex.quote(request)}"
    try:
        completed = subprocess.run(
            ["ssh", *options, "-T", "-o", "BatchMode=yes", destination, remote],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise click.ClickException(f"{destination} did not answer within {timeout:g} s.") from error
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip() or f"status {completed.returncode}"
        raise click.ClickException(f"On {destination}: {detail}")
    return json.loads(completed.stdout.strip().splitlines()[-1])
