# Desktop Launcher: Machines

**Machines** names the machines the application reaches over SSH — a cluster's access node, a lab workstation — once, for every page: each is a name and an SSH destination, as `ssh` takes it, an alias of the SSH configuration or `user@host`. They are kept in `machines.json`, a versioned file of the application in the configuration folder: `{"version": 1, "machines": {"lab": {"ssh": "me@login"}}}`.

The connections themselves keep storing the destination: `notebooks.json`, `remotes.json`, `agents.json` and the servers' remembered launches hold `ssh` as before, so the command line, qibocal-widgets and qibocal-agent read them without the application. A connection is on a machine when its destination is the machine's; a name is only ever the application's.

## The page

- **Named**: a grid of the machines, each with its destination and what uses it — **Notebooks** sessions, **Remote execution** connections, **Servers** started there, **Agents** configurations that reach it and those kept for it — each leading to its page, and **Its queues**, when the application knows a SLURM partition there. The last cell adds a machine.
- **Edit** changes a machine's destination, and offers to move what uses it to the new one: every file storing the old destination is rewritten with the new one. A configuration kept for the machine is moved here; **Push**, on **Agents**, writes it there again.
- The bin forgets a machine's name; what used it keeps its destination, and is shown by it. A machine for which agent configurations are kept stays until they are moved or removed.
- **In use, not named**: the destinations the connections reach that no machine names yet, each with what uses it, named in one go.

## Everywhere else

- Every form that asks for an SSH destination — a notebook session, a remote execution connection, a server on another machine, an agent configuration — offers the machines, by destination and name; any other destination can still be typed.
- **Notebooks**, **Remote execution** and **Servers** filter their lists by machine, as **Agents** does with **Reaches**: chips while there are few, a dropdown past that. A server's machine is the destination remembered with its launch.
- **Agents** keeps configurations for a machine — an assistant running there — and its **Reaches** filter names machines as here.
- **Queues**, and the queue lines of **Home**, name each machine as here.

The remotes the Agents page kept before there were machines became machines of the same name, once, the first time this version started: `agent-hosts.json` keeps only the configurations kept for each.
