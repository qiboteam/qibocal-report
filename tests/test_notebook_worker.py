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
    "server, marimo", [(False, False), (True, False), (True, True)]
)
def test_new_environment_commands(tmp_path, server, marimo):
    runtime = MagicMock()
    path = tmp_path / "environment"

    def command(arguments):
        if arguments[1:3] == ["-m", "venv"]:
            (path / "bin").mkdir(parents=True)
            python = path / "bin/python"
            python.write_text("#!/bin/sh\n")
            python.chmod(0o700)

    runtime.command.side_effect = command
    assert worker.ensure_environment(runtime, path, server, marimo) == str(
        path / "bin/python"
    )
    creation = runtime.command.call_args_list[0].args[0]
    assert ("--without-pip" in creation) is (not server)
    if server:
        packages = ["marimo"] if marimo else ["jupyterlab", "ipykernel"]
        assert runtime.command.call_args_list[1].args[0] == [
            str(path / "bin/python"),
            "-m",
            "pip",
            "install",
            *packages,
        ]
    else:
        assert runtime.command.call_count == 1


def test_existing_environment_never_modified(tmp_path):
    path = tmp_path / "environment"
    (path / "bin").mkdir(parents=True)
    (path / "bin/python").symlink_to(sys.executable)
    runtime = MagicMock()
    worker.ensure_environment(runtime, path, server=True)
    runtime.command.assert_not_called()
    (path / "bin/python").unlink()
    with pytest.raises(worker.WorkerError, match="repair it manually"):
        worker.ensure_environment(runtime, path, server=True)
    runtime.command.assert_not_called()


def test_existing_missing_dependencies_actionable():
    runtime = MagicMock()
    runtime.command.side_effect = worker.WorkerError("import failed")
    with pytest.raises(
        worker.WorkerError, match="python -m pip install jupyterlab ipykernel"
    ):
        worker.server_sites(runtime, "/env/bin/python", False)
    assert runtime.command.call_count == 1


def test_failed_install_is_not_implicitly_retried(tmp_path):
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
        worker.ensure_environment(runtime, path, server=True)
    runtime.command.reset_mock()
    python = worker.ensure_environment(runtime, path, server=True)
    runtime.command.assert_not_called()
    runtime.command.side_effect = worker.WorkerError("missing dependency")
    with pytest.raises(worker.WorkerError, match="Repair the server environment"):
        worker.server_sites(runtime, python, False)


def test_overlapping_environments_fail_without_creation(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    with (
        patch.object(worker, "monitor_stdin"),
        patch.object(worker, "ensure_environment") as ensure,
        pytest.raises(worker.WorkerError, match="must be separate"),
    ):
        worker.run({"venv": "notebook-jupyter"})
    ensure.assert_not_called()


def test_symlinked_overlapping_environments_fail_without_creation(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    server_path = tmp_path / "qibocal/envs/notebook-jupyter"
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


@pytest.mark.parametrize(
    "venv", ["./qibocal/envs", "./qibocal/envs/notebook-jupyter/nested"]
)
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


@pytest.mark.parametrize("marimo", [False, True])
def test_slurm_composition_and_readiness(tmp_path, monkeypatch, capsys, marimo):
    runtime = worker.Runtime(5)
    process = MagicMock()
    process.poll.return_value = None
    tunnel = MagicMock()
    tunnel.poll.return_value = None
    messages = queue.Queue()
    messages.put("scheduler progress\n")
    messages.put(
        worker.READY_PREFIX
        + json.dumps(
            {
                "host": "compute-1",
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
        patch.object(
            runtime, "spawn", side_effect=[(process, messages), (tunnel, queue.Queue())]
        ) as spawn,
        patch.object(runtime, "close") as close,
        patch.object(worker, "monitor_stdin"),
        patch.object(worker, "free_port", return_value=9100),
        patch.object(worker, "wait_http") as wait,
        patch.object(worker, "announce", side_effect=announce_and_stop),
    ):
        worker.run(
            {
                "queue": "chip",
                "slurm": "--mem=4G",
                "workdir": "./work",
                "marimo": marimo,
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
    assert nested["workdir"] == str(tmp_path / "work")
    assert spawn.call_args_list[1].args[0] == [
        "ssh",
        "-N",
        "-T",
        "-o",
        "ExitOnForwardFailure=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "ServerAliveInterval=30",
        "-o",
        "ServerAliveCountMax=3",
        "-L",
        "127.0.0.1:9100:127.0.0.1:8100",
        "compute-1",
    ]
    wait.assert_called_once()
    close.assert_called_once()
    output = capsys.readouterr()
    assert output.out.count(worker.READY_PREFIX) == 1
    assert "scheduler progress" in output.err
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
        {"host": "node", "port": True, "token": "a", "path": "/lab"},
        {"host": "node", "port": 123, "token": "", "path": "/lab"},
        {"host": "node", "port": 123, "token": "a", "path": "//evil"},
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
def test_real_transported_script_lifecycle(tmp_path, marimo, shutdown):
    cache = tmp_path / "cache"
    target = tmp_path / "target"
    server = (
        cache / "qibocal/envs" / ("notebook-marimo" if marimo else "notebook-jupyter")
    )
    (target / "bin").mkdir(parents=True)
    (server / "bin").mkdir(parents=True)
    (target / "bin/python").symlink_to(sys.executable)
    sites = tmp_path / "server-sites"
    sites.mkdir()
    module = sites / ("marimo" if marimo else "jupyterlab")
    module.mkdir()
    (module / "__init__.py").write_text("")
    (module / "__main__.py").write_text(FAKE_SERVER)
    python = server / "bin/python"
    python.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        f"sites = {str(sites)!r}\n"
        "if sys.argv[1] == '-c':\n"
        "    print(json.dumps([sites]))\n"
        "else:\n"
        "    os.environ['PYTHONPATH'] = sites\n"
        f"    os.execv({sys.executable!r}, [{sys.executable!r}, *sys.argv[1:]])\n"
    )
    python.chmod(0o700)
    source = Path(worker.__file__).read_text()
    script = "WORKER_SOURCE = " + repr(source) + "\n" + source
    pidfile = tmp_path / "server.pid"
    env = dict(
        os.environ,
        XDG_CACHE_HOME=str(cache),
        FAKE_PID=str(pidfile),
        EXPECTED_TARGET=str(target / "bin/python"),
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-u",
            "-c",
            script,
            json.dumps(
                {
                    "venv": str(target),
                    "workdir": str(tmp_path),
                    "marimo": marimo,
                    "timeout": 10,
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
        if shutdown == "eof":
            process.stdin.close()
        else:
            process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=10) == 0
        assert process.stdout.read() == ""
        logs = process.stderr.read()
        assert "child stdout log" in logs and "child stderr log" in logs
        assert not list(tmp_path.glob(".qibocal-kernels-*"))
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
