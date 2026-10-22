# Desktop Launcher: Agents

**Agents** manages the configurations of `qibocal-agent`, from the [Qibocal MCP servers](https://github.com/qiboteam/qibocal-mcp-servers) — the MCP server an assistant such as Copilot, Claude or Cursor registers, `qibocal-agent mcp`, and the autonomous calibration agent, `qibocal-agent run` — and dispatches autonomous runs. The page opens on **Setup**, what is not one configuration's own; then the configurations, with **Refresh**, and **New configuration** for the form; then the **Saved prompts**.

## How it fits together

Three machines may take part in a calibration: where the agent runs — an assistant, or an autonomous run — where the calibration server runs, and where the instruments are reached. A configuration says how they are arranged.

The **SSH destination** is where the calibration server starts, over SSH, from wherever the configuration is used: usually a cluster's access node. With a **SLURM partition**, the server dispatches each operation as one `srun` job on that partition, whose nodes reach the instruments, and holds no allocation in between:

```text
 this machine                      access node                     compute node
┌──────────────────────┐   ssh    ┌───────────────────────┐ srun  ┌──────────────────┐
│ assistant            │ ───────▶ │ calibration server    │ ────▶ │ one operation    │
│  └ qibocal-agent mcp │          │ (qibocal-mcp)         │       │ ── instruments   │
│ or autonomous run    │ ◀─────── │ reports, platform     │ ◀──── │                  │
└──────────────────────┘          └───────────────────────┘       └──────────────────┘
       kept for                        SSH destination              SLURM partition
```

Without a partition, the server runs the operations itself, so it must reach the instruments; without an SSH destination, the server starts where the agent runs. A lab workstation wired to the instruments needs neither:

```text
 this machine
┌─────────────────────────────────────────────────────────────────────┐
│ assistant ── qibocal-agent mcp ── calibration server ── instruments │
└─────────────────────────────────────────────────────────────────────┘
```

A configuration is **kept for** where its user is. **This machine**: an assistant here, or autonomous runs dispatched from here, read it from this machine's `agents.json`. **A remote**: an assistant running on that machine — the access node itself, say — reads it from the `agents.json` there, which the launcher writes for it:

```text
 this machine                         remote: the access node
┌──────────────────────┐   push    ┌──────────────────────────────┐ srun  ┌──────────────┐
│ Qibocal application  │ ────────▶ │ agents.json                  │ ────▶ │ compute node │
│  └ agent-hosts.json  │   (ssh)   │ assistant                    │       │ instruments  │
└──────────────────────┘           │  └ qibocal-agent mcp, server │       └──────────────┘
                                   └──────────────────────────────┘
```

In both cases an assistant registers `qibocal-agent mcp` **once**. It starts nothing by itself: its calibration tools appear when the assistant selects a configuration, which it does when asked to calibrate — listing the configurations, and asking which one when that is not said. Autonomous runs name their configuration, and start at once.

## Setup

- **What it is**: the explanation above, in brief, and a link here.
- **qibocal-agent**: the one the page runs and registers, by absolute path, with its version. **Install** — **Update** once installed — puts the branch, tag or commit given (`main` by default, the repository's branches and tags offered) in `~/.cache/qibocal/agents/tools`, an environment of its own with Python 3.12 or 3.13, which uv provides when needed: `qibocal agents install --ref REF`, its output in **Running**. **Choose environment…** takes another one instead, a checkout's `.venv` say, and **Detect** forgets it: the installed one is used, else the one on the `PATH`.
- **MCP registration**: the registration of `qibocal-agent mcp` for an assistant on this machine, with **Copy** — for Copilot, `~/.copilot/mcp-config.json`; other assistants take the same command and arguments. One serves every configuration, so there is nothing to register again when one is added. An assistant on a remote registers the same, with the path of the qibocal-agent installed there. The launcher writes no other tool's file.
- **Remotes**: the SSH remotes, each a name and a destination as `ssh` takes it — an alias of the SSH configuration, or `user@host` — named once, and reached by as many configurations as need them. A configuration is kept for one of them, and its SSH destination offers their destinations. They are kept in `agent-hosts.json`, with the configurations kept for each; a remote holding configurations is not removed until they are moved or removed.

## Where a configuration is kept

- For **this machine**, it is an entry of `agents.json` — `~/.config/qibocal/agents.json`, or `$XDG_CONFIG_HOME/qibocal/agents.json`, or `$QIBOCAL_AGENTS_CONFIG_DIR/agents.json` — the file `qibocal-agent` itself reads, every configuration under `agents`. Each has a name: `default` is the one used when none is given, an ordinary entry otherwise, and `agent` and `agents` are reserved. The file is the tool's, and it refuses a key it does not know, so the launcher writes nothing else in it.
- For **a remote**, it is kept here, under that remote in `agent-hosts.json`, and written to the `agents.json` there when saved, with `qibocal agents push`: the entries it owns are merged into the remote `agents`, and every other one is left as it is. Only the configuration travels, never environments or keys. When the remote cannot be reached, the configuration is kept here anyway, and **Push** sends it again.

Two rows of chips filter the list, together: **Kept for** — this machine, or each remote — and **Reaches** — **Directly**, a configuration without SSH destination, or the remote its SSH destination is. Each card says both: *this machine* or *for* a remote, and *direct* or *via* a remote.

## The settings

They are those of the [configuration guide](https://github.com/qiboteam/qibocal-mcp-servers/blob/main/docs/guides/configuration.rst): the **Platform**, the **Model** of autonomous runs, the **SSH destination** and the **SLURM partition** first; under **More options**, the model endpoint, the output and working directories, the platforms folder, the environment or a server interpreter, the dependencies, platform repositories and srun options — one per line — and the timeout, and the **Objective** of a run given none. Every configuration, `default` included, has its own environment, working folder and report folder, named after it. What the form does not show, a `report` section for instance, is kept as it is.

## Each configuration

- **Run**, for a configuration of this machine, dispatches an autonomous agent: `qibocal-agent run NAME "PROMPT"`, its output in **Running**. The prompt is typed in the dialog, picked among the **Saved prompts**, or left empty for the configuration's own objective. A run needs a model; its credentials, an `OPENAI_API_KEY` say, come from your shell profile, which the run is started through, since an application opened from the Dock inherits none: the launcher stores no key. The agent is **not a hardware safety layer**: give approved limits, a budget and when to stop.
- **Push**, for a configuration of a remote, writes it there again.
- **Reports** starts a report server on the execution host — the configuration's SSH destination, or the remote it is kept for — serving its output, `~/.local/share/qibocal/agents/runs/NAME` unless set otherwise, and opens it in the dashboard; it is started for a look, and nothing is registered.
- **Edit**, its name and where it is kept included, **Duplicate**, and the bin.

## Saved prompts

Prompts for autonomous runs, kept in `launcher.json`, apart from the configurations, and offered by **Run**. **+** saves one without running it; **Save prompt**, on an agent's run in **Running**, saves the prompt that run was given — or its configuration's objective, given none — under a name typed there.
