import json
import os
import queue
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from qibocal_report import notebook_worker as worker


def test_node_identity_logging(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    for name, value in {
        "SLURM_CLUSTER_NAME": "lab",
        "SLURM_JOB_ID": "12345",
        "SLURM_JOB_PARTITION": "chip",
        "SLURM_STEP_ID": "0",
        "SLURM_JOB_NODELIST": "compute-[1-2]",
        "SLURM_CPUS_PER_TASK": "4",
        "SLURM_MEM_PER_NODE": "8192",
        "SLURM_JOB_GPUS": "0",
        "CUDA_VISIBLE_DEVICES": "0",
        "PRIVATE_TOKEN": "do-not-log",
    }.items():
        monkeypatch.setenv(name, value)
    with (
        patch.object(worker.socket, "gethostname", return_value="compute-1"),
        patch.object(worker.socket, "getfqdn", return_value="compute-1.lab"),
        patch.object(worker.getpass, "getuser", return_value="scientist"),
    ):
        worker.log_node("compute")
    output = capsys.readouterr()
    assert output.out == ""
    prefix = worker.EVENT_PREFIX
    assert output.err.startswith(prefix)
    event = json.loads(output.err[len(prefix) :])
    assert event["kind"] == "node"
    assert event["role"] == "compute"
    identity = event["identity"]
    assert identity["hostname"] == "compute-1"
    assert identity["fqdn"] == "compute-1.lab"
    assert identity["user"] == "scientist"
    assert identity["cwd"] == str(tmp_path.resolve())
    assert identity["python"] == sys.executable
    assert identity["python_version"] == worker.platform.python_version()
    assert identity["pid"] == os.getpid()
    assert identity["system"] == worker.platform.system()
    assert identity["release"] == worker.platform.release()
    assert identity["architecture"] == worker.platform.machine()
    assert identity["slurm"]["SLURM_JOB_ID"] == "12345"
    assert identity["slurm"]["SLURM_JOB_PARTITION"] == "chip"
    assert identity["slurm"]["SLURM_STEP_ID"] == "0"
    assert identity["slurm"]["SLURM_CPUS_PER_TASK"] == "4"
    assert identity["slurm"]["SLURM_MEM_PER_NODE"] == "8192"
    assert identity["slurm"]["SLURM_JOB_GPUS"] == "0"
    assert "PRIVATE_TOKEN" not in output.err
    assert "do-not-log" not in output.err


@pytest.mark.parametrize(
    "options, role",
    [
        ({}, "access and compute"),
        ({"queue": "chip"}, "access"),
        ({"slurm": "--mem=4G"}, "access"),
        ({"_node_role": "compute"}, "compute"),
    ],
)
def test_node_logged_before_setup_failure(options, role, tmp_path, capsys):
    with pytest.raises(FileNotFoundError):
        worker.run(dict(options, workdir=str(tmp_path / "missing")))
    output = capsys.readouterr()
    assert output.out == ""
    event = json.loads(output.err[len(worker.EVENT_PREFIX) :])
    assert event["kind"] == "node"
    assert event["role"] == role


def test_environment_resolution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    assert worker.environment_path("chip") == tmp_path / "cache/qibocal/envs/chip"
    assert worker.environment_path("./chip") == tmp_path / "chip"
    assert worker.environment_path("../chip") == tmp_path.parent / "chip"
    assert worker.environment_path("~/chip") == tmp_path / "home/chip"
    monkeypatch.delenv("XDG_CACHE_HOME")
    assert (
        worker.environment_path("qibocal")
        == tmp_path / "home/.cache/qibocal/envs/qibocal"
    )
    monkeypatch.setenv("XDG_CACHE_HOME", "")
    assert (
        worker.environment_path("qibocal")
        == tmp_path / "home/.cache/qibocal/envs/qibocal"
    )
    with pytest.raises(worker.WorkerError):
        worker.environment_path("ambiguous/path")


@pytest.mark.parametrize(
    "server, packages",
    [
        (False, ()),
        (False, ("qibocal",)),
        (True, ()),
    ],
)
def test_new_environment_commands(tmp_path, monkeypatch, server, packages):
    monkeypatch.setattr(worker.util, "find_spec", lambda name: object())
    runtime = MagicMock()
    path = tmp_path / "environment"

    def command(arguments):
        if arguments[1:3] == ["-m", "venv"]:
            (path / "bin").mkdir(parents=True)
            python = path / "bin/python"
            python.write_text("#!/bin/sh\n")
            python.chmod(0o700)

    runtime.command.side_effect = command
    assert worker.ensure_environment(runtime, path, server, packages=packages) == str(
        path / "bin/python"
    )
    creation = runtime.command.call_args_list[0].args[0]
    assert "--without-pip" not in creation
    if server:
        packages = ["jupyterlab", "ipykernel"]
    if packages:
        assert runtime.command.call_args_list[1].args[0] == [
            str(path / "bin/python"),
            "-m",
            "pip",
            "install",
            *packages,
        ]
    else:
        assert runtime.command.call_count == 1


@pytest.mark.parametrize(
    "server, packages",
    [
        (False, ()),
        (False, ("qibocal",)),
        (True, ()),
    ],
)
def test_environment_without_ensurepip(tmp_path, monkeypatch, server, packages):
    monkeypatch.setattr(
        worker.util,
        "find_spec",
        lambda name: object() if name == "pip" else None,
    )
    path = tmp_path / "environment"
    runtime = MagicMock()

    def command(arguments):
        if arguments[1:3] == ["-m", "venv"]:
            (path / "bin").mkdir(parents=True)
            (path / "bin/python").symlink_to(sys.executable)

    runtime.command.side_effect = command
    python = worker.ensure_environment(runtime, path, server=server, packages=packages)
    assert runtime.command.call_args_list[0].args[0] == [
        sys.executable,
        "-m",
        "venv",
        "--without-pip",
        str(path),
    ]
    packages = ["jupyterlab", "ipykernel"] if server else list(packages)
    expected = [
        sys.executable,
        "-m",
        "pip",
        "--python",
        python,
        "install",
        "pip",
        *packages,
    ]
    assert runtime.command.call_args_list[1].args[0] == expected


@pytest.mark.skipif(worker.util.find_spec("ensurepip") is None, reason="no ensurepip")
def test_new_empty_environment_has_pip(tmp_path):
    runtime = MagicMock()
    runtime.command.side_effect = lambda arguments: subprocess.run(
        arguments, check=True, capture_output=True, text=True
    )
    path = tmp_path / "environment"
    python = worker.ensure_environment(runtime, path)
    result = subprocess.run(
        [python, "-m", "pip", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert str(path) in result.stdout
    assert (path / "bin/pip").is_file()


@pytest.mark.parametrize("packages", [(), ("qibocal",)])
@pytest.mark.parametrize("server", [False, True])
def test_environment_without_installer_fails_before_creation(
    tmp_path, monkeypatch, server, packages
):
    monkeypatch.setattr(worker.util, "find_spec", lambda name: None)
    runtime = MagicMock()
    path = tmp_path / "server"
    with pytest.raises(worker.WorkerError, match="pip >= 22.3"):
        worker.ensure_environment(runtime, path, server=server, packages=packages)
    assert not path.exists()
    runtime.command.assert_not_called()
    runtime.command.side_effect = worker.WorkerError("import failed")
    with pytest.raises(worker.WorkerError, match="no external package installer"):
        worker.server_sites(runtime, "/env/bin/python")


def test_missing_server_dependencies_without_ensurepip(monkeypatch):
    monkeypatch.setattr(
        worker.util, "find_spec", lambda name: object() if name == "pip" else None
    )
    runtime = MagicMock()
    runtime.command.side_effect = worker.WorkerError("import failed")
    with pytest.raises(
        worker.WorkerError,
        match=r"-m pip --python /env/bin/python install jupyterlab ipykernel",
    ):
        worker.server_sites(runtime, "/env/bin/python")
    assert runtime.command.call_count == 1


@pytest.mark.parametrize("server", [False, True])
def test_existing_environment_never_modified(tmp_path, server):
    path = tmp_path / "environment"
    (path / "bin").mkdir(parents=True)
    (path / "bin/python").symlink_to(sys.executable)
    runtime = MagicMock()
    worker.ensure_environment(runtime, path, server=server, packages=("qibocal",))
    runtime.command.assert_not_called()
    (path / "bin/python").unlink()
    with pytest.raises(worker.WorkerError, match="repair it manually"):
        worker.ensure_environment(runtime, path, server=server, packages=("qibocal",))
    runtime.command.assert_not_called()


def test_existing_missing_dependencies_actionable():
    runtime = MagicMock()
    runtime.command.side_effect = worker.WorkerError("import failed")
    with pytest.raises(
        worker.WorkerError, match="python -m pip install jupyterlab ipykernel"
    ):
        worker.server_sites(runtime, "/env/bin/python")
    assert runtime.command.call_count == 1


@pytest.mark.parametrize("server", [False, True])
def test_failed_install_is_not_implicitly_retried(tmp_path, server):
    runtime = MagicMock()
    path = tmp_path / "server"

    def command(arguments):
        if arguments[1:3] == ["-m", "venv"]:
            (path / "bin").mkdir(parents=True)
            (path / "bin/python").symlink_to(sys.executable)
        else:
            raise worker.WorkerError("Installation failed")

    runtime.command.side_effect = command
    with pytest.raises(worker.WorkerError, match="Installation failed"):
        worker.ensure_environment(runtime, path, server=server, packages=("qibocal",))
    runtime.command.reset_mock()
    python = worker.ensure_environment(
        runtime, path, server=server, packages=("qibocal",)
    )
    runtime.command.assert_not_called()
    runtime.command.side_effect = worker.WorkerError("missing dependency")
    with pytest.raises(worker.WorkerError, match="Repair the server environment"):
        worker.server_sites(runtime, python)


def test_overlapping_environments_fail_without_creation(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    with (
        patch.object(worker, "monitor_stdin"),
        patch.object(worker, "ensure_environment") as ensure,
        pytest.raises(worker.WorkerError, match="must be separate"),
    ):
        worker.run({"venv": "jupyter"})
    ensure.assert_not_called()


def test_symlinked_overlapping_environments_fail_without_creation(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    server_path = tmp_path / "qibocal/envs/jupyter"
    server_path.mkdir(parents=True)
    target_path = tmp_path / "target"
    target_path.symlink_to(server_path, target_is_directory=True)
    with (
        patch.object(worker, "monitor_stdin"),
        patch.object(worker, "ensure_environment") as ensure,
        pytest.raises(worker.WorkerError, match="must be separate"),
    ):
        worker.run({"venv": str(target_path)})
    ensure.assert_not_called()


@pytest.mark.parametrize("venv", ["./qibocal/envs", "./qibocal/envs/jupyter/nested"])
def test_nested_environments_fail_without_creation(tmp_path, monkeypatch, venv):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    with (
        patch.object(worker, "monitor_stdin"),
        patch.object(worker, "ensure_environment") as ensure,
        pytest.raises(worker.WorkerError, match="must be separate"),
    ):
        worker.run({"venv": venv})
    ensure.assert_not_called()


@pytest.mark.parametrize("value", ["[]", "{", '{"timeout": 0}', '{"timeout": "nan"}'])
def test_main_errors_are_stderr_only(value, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["worker", value])
    assert worker.main() == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.startswith("Notebook worker:")


@pytest.mark.parametrize(
    "value",
    [
        "--output=result",
        "-ofile",
        "--input /dev/null",
        "--error=x",
        "--unbuffered",
        "--pty",
        "--multi-prog=x",
        "--wrap=x",
        "--label",
        "--chdir=/elsewhere",
        "--",
        "python3 evil.py",
        "--time=1 python3",
        "--ntasks=2",
        "--nodes=2",
        "-N 2",
        "-n 2",
        "-u",
    ],
)
def test_slurm_rejects_command_or_io_override(value):
    with pytest.raises(worker.WorkerError):
        worker.slurm_arguments(value)


def test_slurm_options():
    assert worker.slurm_arguments(
        '--time 01:00:00 --mem=4G -c 2 --job-name "chip run"'
    ) == [
        "--time",
        "01:00:00",
        "--mem=4G",
        "-c",
        "2",
        "--job-name",
        "chip run",
    ]


def test_node_addresses():
    runtime = MagicMock()
    runtime.command.return_value = (
        "127.0.0.1 ::1 0.0.0.0 :: 169.254.1.1 fe80::1 224.0.0.1 ff02::1 "
        "192.0.2.10 2001:db8::10 192.0.2.10\n"
    )
    assert worker.node_addresses(runtime) == ["192.0.2.10", "2001:db8::10"]
    runtime.command.assert_called_once_with(["hostname", "-I"], capture=True)


@pytest.mark.parametrize("result", ["", "127.0.0.1 fe80::1", "not-an-ip"])
def test_node_addresses_fail_explicitly(result):
    runtime = MagicMock()
    runtime.command.return_value = result
    with pytest.raises(worker.WorkerError):
        worker.node_addresses(runtime)


@pytest.mark.parametrize(
    "access, compute, expected",
    [
        (
            ["198.51.100.10", "192.0.2.10"],
            ["203.0.113.20", "192.0.2.20"],
            "192.0.2.20",
        ),
        (
            ["192.0.2.130"],
            ["192.0.2.20", "192.0.2.140"],
            "192.0.2.140",
        ),
        (
            ["2001:db8:1::10"],
            ["2001:db8:2::20", "2001:db8:1::20"],
            "2001:db8:1::20",
        ),
        (["192.0.2.10", "2001:db8::10"], ["192.0.2.20"], "192.0.2.20"),
    ],
)
def test_compute_address_longest_network_prefix(access, compute, expected):
    assert worker.compute_address(access, compute) == expected


def test_compute_address_requires_matching_family():
    with pytest.raises(worker.WorkerError, match="no common IP address family"):
        worker.compute_address(["192.0.2.10"], ["2001:db8::20"])


@pytest.mark.parametrize(
    "access, compute, subnet, expected",
    [
        (
            ["10.0.0.10"],
            ["10.0.0.20", "192.168.0.20", "192.168.1.20"],
            "192.168.0.0/24",
            "192.168.0.20",
        ),
        (
            ["192.168.0.130"],
            ["192.168.0.20", "192.168.0.140", "192.168.1.130"],
            "192.168.0.0/24",
            "192.168.0.140",
        ),
        (
            ["2001:db8:2::10"],
            ["192.168.0.20", "2001:db8:2::20", "2001:db8:1::20"],
            "2001:db8:1::/64",
            "2001:db8:1::20",
        ),
        (
            ["192.168.0.10"],
            ["192.168.0.0", "192.168.0.255"],
            "192.168.0.255/32",
            "192.168.0.255",
        ),
    ],
)
def test_compute_address_subnet(access, compute, subnet, expected):
    assert worker.compute_address(access, compute, subnet) == expected


@pytest.mark.parametrize("compute", [[], ["192.168.1.20"], ["2001:db8::20"]])
def test_compute_address_subnet_no_match(compute):
    with pytest.raises(worker.WorkerError, match="match subnet 192.168.0.0/24"):
        worker.compute_address(["192.168.0.10"], compute, "192.168.0.0/24")


def test_compute_address_subnet_requires_matching_family():
    with pytest.raises(worker.WorkerError, match="no common IP address family"):
        worker.compute_address(
            ["2001:db8::10"], ["192.168.0.20"], "192.168.0.0/24"
        )


@pytest.mark.parametrize("marimo", [False, True])
@pytest.mark.parametrize("ipv6", [False, True])
def test_slurm_composition_and_readiness(tmp_path, monkeypatch, capsys, marimo, ipv6):
    access_addresses = ["2001:db8::10"] if ipv6 else ["192.0.2.10"]
    compute_host = "2001:db8::20" if ipv6 else "192.0.2.20"
    runtime = worker.Runtime(5)
    process = MagicMock()
    process.poll.return_value = None
    forwarder = MagicMock()
    forwarder.port = 9100
    messages = queue.Queue()
    messages.put("scheduler progress\n")
    messages.put(
        worker.READY_PREFIX
        + json.dumps(
            {
                "host": compute_host,
                "port": 8100,
                "token": "secret",
                "path": "/" if marimo else "/lab",
            }
        )
        + "\n"
    )
    monkeypatch.setattr(
        worker, "WORKER_SOURCE", "print('embedded source')", raising=False
    )
    monkeypatch.chdir(tmp_path)
    (tmp_path / "work").mkdir()
    announce = worker.announce

    def announce_and_stop(*args):
        announce(*args)
        runtime.stop.set()

    with (
        patch.object(worker, "Runtime", return_value=runtime),
        patch.object(runtime, "spawn", return_value=(process, messages)) as spawn,
        patch.object(worker, "Forwarder", return_value=forwarder) as forward,
        patch.object(runtime, "close") as close,
        patch.object(worker, "monitor_stdin"),
        patch.object(
            worker, "node_addresses", return_value=access_addresses
        ) as addresses,
        patch.object(worker, "wait_http") as wait,
        patch.object(worker, "announce", side_effect=announce_and_stop),
    ):
        worker.run(
            {
                "queue": "chip",
                "slurm": "--mem=4G",
                "workdir": "./work",
                "marimo": marimo,
                "subnet": "2001:db8::/64" if ipv6 else "192.0.2.0/24",
            }
        )
    command = spawn.call_args_list[0].args[0]
    assert command[:5] == ["srun", "--unbuffered", "--partition", "chip", "--mem=4G"]
    assert command[5:11] == [
        "--nodes=1",
        "--ntasks=1",
        "--ntasks-per-node=1",
        "python3",
        "-u",
        "-c",
    ]
    assert command[11].startswith("WORKER_SOURCE = ")
    nested = json.loads(command[12])
    assert nested["queue"] is None and nested["slurm"] is None
    assert nested["_node_role"] == "compute"
    assert nested["_access_addresses"] == access_addresses
    assert nested["subnet"] == ("2001:db8::/64" if ipv6 else "192.0.2.0/24")
    assert nested["workdir"] == str(tmp_path / "work")
    forward.assert_called_once_with(compute_host, 8100)
    forwarder.close.assert_called_once()
    addresses.assert_called_once_with(runtime)
    assert spawn.call_count == 1
    wait.assert_called_once()
    close.assert_called_once()
    output = capsys.readouterr()
    assert output.out.count(worker.READY_PREFIX) == 1
    assert "scheduler progress" in output.err
    event = json.loads(output.err.splitlines()[0][len(worker.EVENT_PREFIX) :])
    assert event["kind"] == "node"
    assert event["role"] == "access"
    ready = json.loads(output.out[len(worker.READY_PREFIX) :])
    assert ready == {
        "host": socket.gethostname(),
        "port": 9100,
        "token": "secret",
        "path": "/" if marimo else "/lab",
    }


@pytest.mark.parametrize(
    "data",
    [
        {"host": "-bad", "port": 123, "token": "a", "path": "/lab"},
        {"host": "192.0.2.20", "port": True, "token": "a", "path": "/lab"},
        {"host": "192.0.2.20", "port": 123, "token": "", "path": "/lab"},
        {"host": "192.0.2.20", "port": 123, "token": "a", "path": "//evil"},
        {
            "host": "not-an-ip",
            "port": 123,
            "token": "a",
            "path": "/lab",
        },
        {
            "host": "127.0.0.1",
            "port": 123,
            "token": "a",
            "path": "/lab",
        },
        {
            "host": "fe80::1%eth0",
            "port": 123,
            "token": "a",
            "path": "/lab",
        },
        {
            "host": "",
            "port": 123,
            "token": "a",
            "path": "/lab",
        },
    ],
)
def test_nested_readiness_validation(data):
    messages = queue.Queue()
    messages.put(worker.READY_PREFIX + json.dumps(data))
    with pytest.raises(worker.WorkerError, match="Invalid nested"):
        worker.wait_nested(worker.Runtime(1), MagicMock(), messages)


def test_nested_timeout_and_stop():
    runtime = worker.Runtime(1)
    runtime.deadline = time.monotonic() - 1
    with pytest.raises(worker.WorkerError, match="Timed out"):
        worker.wait_nested(runtime, MagicMock(), queue.Queue())
    runtime.stop.set()
    with pytest.raises(worker.Stopped):
        runtime.check()


@pytest.mark.parametrize("marimo", [False, True])
@pytest.mark.parametrize("host", ["192.0.2.20", "2001:db8::20"])
@pytest.mark.parametrize("venv", [None, "qibocal", "newenv", "./qibocal"])
@pytest.mark.parametrize("subnet", [False, True])
def test_compute_worker_binds_selected_interface(
    tmp_path, monkeypatch, marimo, host, venv, subnet
):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    runtime = worker.Runtime(5)
    process = MagicMock()
    process.poll.return_value = None

    def announce_and_stop(*args):
        runtime.stop.set()

    with (
        patch.object(worker, "Runtime", return_value=runtime),
        patch.object(runtime, "spawn", return_value=(process, queue.Queue())) as spawn,
        patch.object(
            runtime, "command", return_value="true" if marimo else '["/target-sites"]'
        ) as install,
        patch.object(runtime, "close"),
        patch.object(worker, "monitor_stdin"),
        patch.object(
            worker, "node_addresses", return_value=["10.0.0.10", host]
        ) as addresses,
        patch.object(
            worker,
            "ensure_environment",
            side_effect=["/target/python", "/server/python"],
        ) as ensure,
        patch.object(worker, "server_sites", return_value=["/server-sites"]) as sites,
        patch.object(worker.util, "find_spec", return_value=object()),
        patch.object(worker, "free_port", return_value=8100) as port,
        patch.object(worker, "wait_http") as wait,
        patch.object(worker, "announce", side_effect=announce_and_stop) as announce,
    ):
        options = {
            "marimo": marimo,
            "_node_role": "compute",
            "_access_addresses": [host.replace("20", "10")],
        }
        if venv is not None:
            options["venv"] = venv
        if subnet:
            options["subnet"] = (
                "2001:db8::/64" if ":" in host else "192.0.2.0/24"
            )
        worker.run(options)
    assert ensure.call_args_list[0].kwargs == {"packages": ("qibocal",)}
    addresses.assert_called_once_with(runtime)
    port.assert_called_once_with(host)
    command = spawn.call_args.args[0]
    if marimo:
        assert ensure.call_count == 1
        sites.assert_not_called()
        assert install.call_count == 2
        assert install.call_args.args[0] == [
            "/target/python",
            "-m",
            "pip",
            "install",
            "marimo",
        ]
        assert command[:4] == ["/target/python", "-m", "marimo", "edit"]
        assert spawn.call_args.kwargs["env"].get("PYTHONPATH") == os.environ.get(
            "PYTHONPATH"
        )
        assert command[command.index("--host") + 1] == host
    else:
        assert ensure.call_count == 2
        assert ensure.call_args_list[1].args == (
            runtime,
            tmp_path / "qibocal/envs/jupyter",
        )
        assert ensure.call_args_list[1].kwargs == {"server": True}
        assert f"--ServerApp.ip={host}" in command
    assert spawn.call_count == 1
    assert wait.call_args.kwargs["host"] == host
    assert announce.call_args.args[3] == host


@pytest.mark.parametrize("seeded", [False, True])
def test_marimo_install_failure_stops_startup(tmp_path, monkeypatch, seeded):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    runtime = worker.Runtime(5)
    with (
        patch.object(worker, "Runtime", return_value=runtime),
        patch.object(worker, "monitor_stdin"),
        patch.object(
            worker, "ensure_environment", return_value="/target/python"
        ) as ensure,
        patch.object(worker, "server_sites") as sites,
        patch.object(
            worker.util,
            "find_spec",
            side_effect=lambda name: object() if seeded or name == "pip" else None,
        ),
        patch.object(
            runtime,
            "command",
            side_effect=[
                json.dumps(seeded),
                worker.WorkerError("Installation failed"),
            ],
        ) as install,
        patch.object(runtime, "spawn") as spawn,
        patch.object(runtime, "close"),
        pytest.raises(worker.WorkerError, match="Installation failed"),
    ):
        worker.run({"marimo": True, "venv": "jupyter"})
    ensure.assert_called_once_with(
        runtime, tmp_path / "qibocal/envs/jupyter", packages=("qibocal",)
    )
    sites.assert_not_called()
    spawn.assert_not_called()
    assert install.call_count == 2
    assert install.call_args.args[0] == (
        ["/target/python", "-m", "pip", "install", "marimo"]
        if seeded
        else [
            sys.executable,
            "-m",
            "pip",
            "--python",
            "/target/python",
            "install",
            "marimo",
        ]
    )


def test_forwarder_bidirectional_and_half_close():
    payload = b"notebook websocket data" * 10000
    received = queue.Queue()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        listener.settimeout(5)

        def serve():
            with listener.accept()[0] as connection:
                connection.settimeout(5)
                connection.sendall(b"connected")
                chunks = []
                while chunk := connection.recv(65536):
                    chunks.append(chunk)
                received.put(b"".join(chunks))
                connection.sendall(payload)

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        forwarder = worker.Forwarder("127.0.0.1", listener.getsockname()[1])
        try:
            assert forwarder.server.server_address[0] == "127.0.0.1"
            with socket.create_connection(
                ("127.0.0.1", forwarder.port), timeout=5
            ) as client:
                assert client.recv(9) == b"connected"
                client.sendall(payload)
                client.shutdown(socket.SHUT_WR)
                chunks = []
                while chunk := client.recv(65536):
                    chunks.append(chunk)
                assert b"".join(chunks) == payload
            assert received.get(timeout=5) == payload
        finally:
            forwarder.close()
            thread.join(timeout=5)
        assert not forwarder.thread.is_alive()
        assert not thread.is_alive()
        with pytest.raises(OSError):
            socket.create_connection(("127.0.0.1", forwarder.port), timeout=0.2)


def test_forwarder_shutdown_closes_idle_connections():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        listener.settimeout(5)
        forwarder = worker.Forwarder("127.0.0.1", listener.getsockname()[1])
        try:
            with (
                socket.create_connection(
                    ("127.0.0.1", forwarder.port), timeout=5
                ) as client,
                listener.accept()[0] as remote,
            ):
                remote.settimeout(5)
                forwarder.close()
                assert client.recv(1) == b""
                assert remote.recv(1) == b""
        finally:
            if not forwarder.stop.is_set():
                forwarder.close()


def test_forwarder_connection_failure_is_reported(capsys):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    forwarder = worker.Forwarder("127.0.0.1", port)
    try:
        with socket.create_connection(
            ("127.0.0.1", forwarder.port), timeout=5
        ) as client:
            assert client.recv(1) == b""
        assert "Notebook forwarding connection failed" in capsys.readouterr().err
    finally:
        forwarder.close()


def test_http_authenticated_readiness_bypasses_proxy(monkeypatch):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    monkeypatch.setenv("http_proxy", "http://127.0.0.1:1")
    monkeypatch.setenv("no_proxy", "")
    process = MagicMock()
    process.poll.return_value = None
    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        worker.wait_http(
            worker.Runtime(2),
            server.server_port,
            "a token",
            "/lab",
            False,
            [process],
        )
        thread.join(2)
    assert requests == ["/lab?token=a+token"]


def test_bootstrap_target_package_precedence(tmp_path):
    target, fallback = tmp_path / "target", tmp_path / "server"
    target.mkdir()
    fallback.mkdir()
    (target / "shared.py").write_text("VALUE = 'target'\n")
    (fallback / "shared.py").write_text("VALUE = 'server'\n")
    (fallback / "entry.py").write_text("import shared; print(shared.VALUE)\n")
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(fallback), str(target)]))
    result = subprocess.run(
        [sys.executable, "-c", worker.bootstrap([str(fallback)], "entry")],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "target"


FAKE_SERVER = """
import json, os, sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit
args = sys.argv
marimo = '--token-password' in args
if marimo:
    assert Path(os.environ['EXPECTED_TARGET']).with_name('marimo-installed').is_file()
    port = int(args[args.index('--port') + 1])
    token = args[args.index('--token-password') + 1]
    assert args[args.index('--host') + 1] == '127.0.0.1'
    assert '--token' in args and '--headless' in args
else:
    port = int(next(
        a.split('=', 1)[1] for a in args if a.startswith('--ServerApp.port=')
    ))
    token = next(
        a.split('=', 1)[1] for a in args if a.startswith('--IdentityProvider.token=')
    )
    assert '--ServerApp.ip=127.0.0.1' in args
    assert '--ServerApp.port_retries=0' in args and '--no-browser' in args
    assert '--MappingKernelManager.default_kernel_name=qibocal' in args
    kernel = (
        Path(os.environ['JUPYTER_PATH'].split(os.pathsep)[0])
        / 'kernels/qibocal/kernel.json'
    )
    data = json.loads(kernel.read_text())
    assert data['argv'][0] == os.environ['EXPECTED_TARGET']
    assert 'ipykernel_launcher' in data['argv'][2]
    assert 'PYTHONPATH' in data['env']
Path(os.environ['FAKE_PID']).write_text(str(os.getpid()))
print('child stdout log', flush=True)
print('child stderr log', file=sys.stderr, flush=True)
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlsplit(self.path).query)
        ok = query.get('access_token' if marimo else 'token') == [token]
        self.send_response(200 if ok else 403)
        self.end_headers()
    def log_message(self, *args):
        pass
HTTPServer(('127.0.0.1', port), Handler).serve_forever()
"""


@pytest.mark.parametrize("marimo", [False, True])
@pytest.mark.parametrize("shutdown", ["eof", "signal"])
@pytest.mark.parametrize("role", ["access and compute", "compute"])
@pytest.mark.parametrize("runtime_exists", [False, True])
def test_real_transported_script_lifecycle(
    tmp_path, marimo, shutdown, role, runtime_exists
):
    cache = tmp_path / "cache"
    target = tmp_path / "target"
    server = cache / "qibocal/envs/jupyter"
    (target / "bin").mkdir(parents=True)
    if not marimo:
        (server / "bin").mkdir(parents=True)
        (target / "bin/python").symlink_to(sys.executable)
    sites = tmp_path / ("target-sites" if marimo else "server-sites")
    sites.mkdir()
    module = sites / ("marimo" if marimo else "jupyterlab")
    module.mkdir()
    (module / "__init__.py").write_text("")
    (module / "__main__.py").write_text(FAKE_SERVER)
    python = (target if marimo else server) / "bin/python"
    python.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        f"sites = {str(sites)!r}\n"
        "if sys.argv[1:] == ['-m', 'pip', 'install', 'marimo']:\n"
        "    Path(sys.argv[0]).with_name('marimo-installed').touch()\n"
        "elif sys.argv[1] == '-c' and \"find_spec('pip')\" in sys.argv[2]:\n"
        "    print('true')\n"
        "elif sys.argv[1] == '-c':\n"
        "    print(json.dumps([sites]))\n"
        "else:\n"
        "    os.environ['PYTHONPATH'] = sites\n"
        f"    os.execv({sys.executable!r}, [{sys.executable!r}, *sys.argv[1:]])\n"
    )
    python.chmod(0o700)
    source = Path(worker.__file__).read_text()
    script = "WORKER_SOURCE = " + repr(source) + "\n" + source
    pidfile = tmp_path / "server.pid"
    runtime_directory = tmp_path / "runtime"
    if runtime_exists:
        runtime_directory.mkdir()
    env = dict(
        os.environ,
        XDG_CACHE_HOME=str(cache),
        XDG_RUNTIME_DIR=str(runtime_directory),
        FAKE_PID=str(pidfile),
        EXPECTED_TARGET=str(target / "bin/python"),
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-S",
            "-u",
            "-c",
            script,
            json.dumps(
                {
                    "venv": str(target),
                    "workdir": str(tmp_path),
                    "marimo": marimo,
                    "timeout": 10,
                    "_node_role": role,
                }
            ),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        start_new_session=True,
    )
    lines = queue.Queue()
    threading.Thread(
        target=lambda: lines.put(process.stdout.readline()), daemon=True
    ).start()
    try:
        ready_line = lines.get(timeout=12)
        if not ready_line:
            raise AssertionError(process.stderr.read())
        assert ready_line.startswith(worker.READY_PREFIX)
        ready = json.loads(ready_line[len(worker.READY_PREFIX) :])
        assert len(ready["token"]) >= 32
        assert ready["path"] == ("/" if marimo else "/lab")
        assert ready["host"] == socket.gethostname()
        assert pidfile.exists()
        if marimo:
            assert not (cache / "qibocal/envs").exists()
        if shutdown == "eof":
            process.stdin.close()
        else:
            process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=10) == 0
        assert process.stdout.read() == ""
        logs = process.stderr.read()
        assert "child stdout log" in logs and "child stderr log" in logs
        assert ("using the system temporary directory" in logs) is (
            not marimo and not runtime_exists
        )
        node_line = logs.splitlines()[0]
        prefix = worker.EVENT_PREFIX
        assert node_line.startswith(prefix)
        event = json.loads(node_line[len(prefix) :])
        assert event["kind"] == "node"
        assert event["role"] == role
        identity = event["identity"]
        assert identity["hostname"] == ready["host"]
        assert identity["pid"] == process.pid
        assert not list(runtime_directory.glob("qibocal-kernels-*"))
        with pytest.raises(OSError):
            os.kill(int(pidfile.read_text()), 0)
        with pytest.raises(OSError):
            socket.create_connection(("127.0.0.1", ready["port"]), timeout=0.2)
    finally:
        worker.stop_process(process)


def test_setup_timeout_terminates_child():
    runtime = worker.Runtime(0.1)
    try:
        with pytest.raises(worker.WorkerError, match="Timed out"):
            runtime.command([sys.executable, "-c", "import time; time.sleep(30)"])
    finally:
        runtime.close()
    assert runtime.processes[0].poll() is not None


def test_server_dies_before_readiness():
    process = MagicMock()
    process.poll.return_value = 1
    with pytest.raises(worker.WorkerError, match="exited during startup"):
        worker.wait_http(worker.Runtime(1), 1, "token", "/lab", False, [process])
