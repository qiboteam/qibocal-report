# Desktop Launcher: Agents

**Agents** manages the configurations of the [Qibocal MCP servers](https://github.com/qiboteam/qibocal-mcp-servers) — `qibocal-mcp-remote`, which an assistant such as Copilot, Claude or Cursor registers, and `qibocal-agent`, the autonomous calibration agent — and dispatches autonomous runs. It is laid out as **Notebooks** is: the configurations, with **Refresh**, and **New configuration** for the form.

## Where a configuration is kept

A configuration is **kept for this machine** or for **another machine**:

- For this machine, it is an entry of `agent.json` — `~/.config/qibocal/agent.json`, or `$XDG_CONFIG_HOME/qibocal/agent.json`, or `$QIBOCAL_MCP_CONFIG_DIR/agent.json` — the file the tools themselves read: the unnamed defaults under `agent`, a named configuration under `agents`. The file is theirs, and they refuse a key they do not know, so the launcher writes nothing else in it.
- For another machine — an assistant running on an access node, say — it is kept here, in `agent-hosts.json`, by the SSH destination of that machine, and written to the `agent.json` there when saved, with `qibocal agents push`: the named entries it owns are merged into the remote `agents`, and the rest of the remote file is left as it is. Only the configuration travels, never environments or keys. When the machine cannot be reached, the configuration is kept here anyway, and **Push** sends it again.

The chips above the list filter the configurations by where they are kept: this machine, or each host.

## The settings

They are those of the [configuration guide](https://github.com/qiboteam/qibocal-mcp-servers/blob/main/docs/guides/configuration.rst): the **Platform**, the **Model** of autonomous runs, the **SSH destination** of the access node and the **SLURM partition** first; under **More options**, the model endpoint, the output and working directories, the platforms folder, the environment or a server interpreter, the dependencies, platform repositories and srun options — one per line — and the timeout. A named configuration also keeps its **Objective**. What the form does not show, a `report` section for instance, is kept as it is.

## Each configuration

- **Run**, for a configuration of this machine, dispatches an autonomous agent: `qibocal-agent NAME "PROMPT"`, its output in **Running**. The prompt is typed in the dialog, picked among the **Saved prompts** — kept in `launcher.json`, apart from the configurations — or left empty for the configuration's own objective; a prompt can be saved under a name from the dialog. A run needs a model; its credentials, an `OPENAI_API_KEY` say, come from your shell profile, which the run is started through, since an application opened from the Dock inherits none: the launcher stores no key. The agent is **not a hardware safety layer**: give approved limits, a budget and when to stop.
- **Push**, for a configuration of another machine, writes it there again.
- **Reports** starts a report server on the execution host — the configuration's SSH destination, or the machine it is kept for — serving its output, `~/.cache/qibocal/agent/runs/NAME` unless set otherwise, and opens it in the dashboard; it is started for a look, and nothing is registered.
- **MCP** shows the registration of `qibocal-mcp-remote` for an assistant, to copy into its own configuration — for Copilot, `~/.copilot/mcp-config.json`. The launcher writes no other tool's file.
- **Edit**, its name and where it is kept included, **Duplicate**, and the bin.

## qibocal-agent

The tools come from qibocal-mcp-servers, installed apart: the row at the top of the page names the environment holding them — **Choose environment…**, for a checkout's `.venv` say — or, left to **Detect**, they are looked for on the `PATH` and in `~/.cache/qibocal/envs/qibocal-agent`.
