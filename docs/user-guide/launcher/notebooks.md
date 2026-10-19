# Desktop Launcher: Notebooks & Queues

## 📓 Notebook sessions

**Notebooks** is the graphical face of `qibocal notebook`, laid out as **Servers** is: the page opens on the **Registered sessions**, with their count and **Refresh**, and **New session**, in the top-right corner, opens the form for a new one. Every option of the command line is a control, and none is required — empty, the session is a local one:

- **SSH destination** — empty for a local session.
- **SLURM partition**, and **Interface**: JupyterLab or Marimo.

Under **More options**, with their defaults:

- **Extra srun options**.
- **Working directory**, chosen with the file browser for local sessions.
- **Kernel environment** on the computing node, `qibocal` by default, under the same `~/.cache/qibocal/envs/` as the launcher's own environment.
- **Computing node subnet**, validated the way Python's `ip_network` validates it: a network with host bits set is refused before the command is run. Left empty, the computing node binds the notebook to the interface it routes through to reach the access node, leaving out any address the two nodes share — a container bridge every host has at the same address, say — and the access node checks that it can reach the notebook before forwarding to it; when it cannot, the session fails with the address it tried and this is the option to set.
- **Kernel requirements**, in `requirements.txt` format, one requirement per line: what the kernel environment must hold beyond `qibocal`. They are installed when the environment is created; whenever the list changes, the next session installs it with pip on top of the existing environment, which is never rebuilt — nothing is uninstalled, and the requirements last installed are recorded inside the environment, so an unchanged list costs nothing. A failed installation stops the session, and is tried again at the next one. On the command line, `--requirements` takes the text or `@requirements.txt`.
- **Startup timeout**.

Named connections are read from and written to `notebooks.json`, the file `qibocal notebook add` manages, so a connection saved here is usable as `qibocal notebook connect <name>`. Only the options that differ from the defaults are stored.

**Open and register** keeps the new session in `notebooks.json` under its **Name** and opens it; **Open** opens it for a look, saving nothing.

Every registered session is a card, with the same actions as a server's. **Start** opens a session with its options — while one runs, the card wears a *running* pill leading to Running, and **Open** takes its address to the browser. **Wipe and rebuild** deletes the session's kernel environment entirely, with everything ever installed in it, and creates it again from `qibocal` and the session's **Kernel requirements** alone — after asking, since it cannot be undone, and only while no session of it runs; it is `qibocal notebook rebuild`, and its output is in **Running**. Only a Python virtual environment is ever removed: a folder without `pyvenv.cfg` is refused. **Edit** opens the form on the session, its name included, **Duplicate** opens the form for a new session with its options, and the bin forgets it — its environment stays.

Opening a session runs it with `--no-interactive`: the address appears in **Running** as soon as the session answers.

---

## 🧵 SLURM queues

A notebook session dispatched to a SLURM partition waits in its queue before it runs, and the one looking at it wants to know why: who is ahead, which nodes are busy, whether the partition is up at all. In **Running**, the card of such a session shows its **queue** under the actions — the partition's nodes by state in one line, the jobs in a table with this session's own job marked and first, and, while it waits, where it stands in line. Filters narrow the table to one's own jobs, to a state, or to a text; **Refresh** asks the controller now; **Full view** opens the queue on the **Queues** page (`g q`), where every queue the launcher knows — of the sessions it runs, and of the saved connections — is one click away, with links back to the sessions on it. From a card, `q` goes there.

The columns of the table are dragged at their edge, reset by a double click, and remembered. The job is marked as this session's as soon as it is submitted: the worker names it `qibocal-nb-…` unless the extra `srun` options name it, and the launcher finds it by that name until the compute node reports its id. The home page lists, under what runs, the queues of the running sessions in a line each — how many nodes are busy and free, how many jobs run and wait, and one's own jobs — from the last answer, asked once on arrival and not again while there.

The controller is asked sparingly, since every `squeue` costs it something: once the moment a session is dispatched — so the answer is there when its card appears — then every 30 seconds while a queue is on screen, and never otherwise. The interval is the `queuePollSeconds` preference in `launcher.json`, editable in **Configuration**, and never goes under 10. Several panels on the same queue share one question. The question itself is `qibocal notebook queue`, which runs `squeue`, `sinfo` and `whoami` in a single round trip over the session's own SSH destination.
