"""Agent configurations kept here for another machine, written there.

qibocal-agent reads `agents.json` on the machine it runs on. A configuration
meant for an access node — an assistant running there — is kept by the
launcher on this machine and pushed to that one: the entries it owns are
merged into the remote `agents`, every other one is left as it is. Only the
configuration travels, never environments or keys.
"""

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import click

from qibocal_report.remote.notebook import ssh_arguments

# What the remote side runs: the standard library only, on the system python3.
MERGE = r"""
import json, os, sys, tempfile
from pathlib import Path

request = json.loads(sys.argv[1])
custom = os.environ.get("QIBOCAL_AGENTS_CONFIG_DIR")
xdg = os.environ.get("XDG_CONFIG_HOME")
directory = Path(custom) if custom else (Path(xdg) / "qibocal" if xdg else Path.home() / ".config" / "qibocal")
path = directory / "agents.json"
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
handle, temporary = tempfile.mkstemp(dir=directory, prefix=".agents.json.")
with os.fdopen(handle, "w", encoding="utf-8") as file:
    json.dump(document, file, indent=2)
    file.write("\n")
os.replace(temporary, path)
print(json.dumps({"path": str(path), "agents": sorted(agents)}))
"""

NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
# Names qibocal-agent reserves.
RESERVED = {"agent", "agents"}


def push(ssh: str, agents: dict, remove: list[str] | None = None, timeout: float = 60.0) -> dict:
    """Merge `agents` into the remote agents.json, dropping the names in `remove`."""
    remove = list(remove or [])
    for name in [*agents, *remove]:
        if not NAME.fullmatch(name) or name in RESERVED:
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


# The tools an assistant registers, `qibocal-agent`, installed by the
# application in an environment of their own: they need Python 3.12 or 3.13,
# which uv provides when this Python is another one.
TOOLS_REPOSITORY = "https://github.com/qiboteam/qibocal-mcp-servers"
TOOLS_PYTHON = ">=3.12,<3.14"
TOOLS_MARKER = "qibocal-tools.txt"


def tools_directory() -> Path:
    """The environment of the tools: `~/.cache/qibocal/agents/tools`, in qibocal-agent's own folder."""
    cache = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(cache) / "qibocal" / "agents" / "tools"


def tools_requirement(ref: str = "main") -> str:
    """qibocal-agent, with what autonomous runs need, from a branch, tag or commit of its repository."""
    return f"qibocal-agent[agent] @ git+{TOOLS_REPOSITORY}@{ref}#subdirectory=packages/agent"


def install_tools(ref: str = "main", timeout: float = 1800.0) -> Path:
    """Create the tools' environment when missing, and install `ref` in it, replacing what was there.

    Answers the `qibocal-agent` executable, the absolute path an assistant registers.
    """
    from qibocal_report.remote import notebook_worker as worker

    if not re.fullmatch(r"[A-Za-z0-9._/-]+", ref):
        raise click.ClickException(f"Invalid version: {ref!r}: a branch, tag or commit.")
    path = tools_directory()
    python = worker._bin(path, "python")
    runtime = worker.Runtime(timeout)
    try:
        uv = worker.find_uv(runtime)
        if not python.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            if uv:
                runtime.command([uv, "venv", "--seed", "--python", TOOLS_PYTHON, str(path)])
            elif (3, 12) <= sys.version_info[:2] < (3, 14):
                runtime.command([sys.executable, "-m", "venv", str(path)])
            else:
                raise click.ClickException(
                    "qibocal-agent needs Python 3.12 or 3.13, and this one is "
                    f"{sys.version_info[0]}.{sys.version_info[1]}: install uv, which provides it."
                )
        requirement = tools_requirement(ref)
        if uv:
            runtime.command([uv, "pip", "install", "--python", str(python), "--reinstall-package", "qibocal-agent", requirement])
        else:
            runtime.command([str(python), "-m", "pip", "install", "--upgrade", "--force-reinstall", "--no-deps", requirement])
            runtime.command([str(python), "-m", "pip", "install", requirement])
    except worker.WorkerError as error:
        raise click.ClickException(str(error)) from error
    finally:
        runtime.close()
    (path / TOOLS_MARKER).write_text(requirement + "\n", encoding="utf-8")
    return worker._bin(path, "qibocal-agent")
