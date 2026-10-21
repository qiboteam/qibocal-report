"""Administrators and invitations of a server on another machine: made there."""

import json
import subprocess
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from qibocal_report.cli import main
from qibocal_report.remote import server


def test_the_remote_command_line_is_the_environment_s_on_that_machine():
    assert server.remote_qibocal(None) == '"${XDG_CACHE_HOME:-$HOME/.cache}/qibocal/envs/qibocal-report/bin/qibocal"'
    assert server.remote_qibocal("lab") == '"${XDG_CACHE_HOME:-$HOME/.cache}/qibocal/envs/lab/bin/qibocal"'
    assert server.remote_qibocal("~/envs/my env") == '"$HOME"/\'envs/my env/bin/qibocal\''
    assert server.remote_qibocal("/opt/qr/") == "/opt/qr/bin/qibocal"
    with pytest.raises(click.ClickException):
        server.remote_qibocal("bad;name")


def test_an_invitation_for_a_remote_server_is_made_on_its_machine():
    answer = {"username": "chief", "token": "t0k3n", "invite_url": "https://qibo.science/qibocal-report/#/invite?token=t0k3n"}
    with patch.object(server.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(answer), "")) as run:
        result = CliRunner().invoke(main, [
            "report", "admin", "invite", "chief", "--server-url", "http://127.0.0.1:9000",
            "-e", "1", "--json", "--ssh", "-p 2222 me@login", "--venv", "lab",
        ])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["token"] == "t0k3n"
    command = run.call_args.args[0]
    assert command[:3] == ["ssh", "-p", "2222"] and "me@login" in command
    remote = command[-1]
    assert remote.startswith('"${XDG_CACHE_HOME:-$HOME/.cache}/qibocal/envs/lab/bin/qibocal" report admin invite chief')
    assert "--server-url http://127.0.0.1:9000" in remote and "--no-interactive" in remote and remote.endswith("--json")
    assert "--ssh" not in remote, "the remote side makes it in its own users"


def test_the_administrators_of_a_remote_server_are_listed_there_and_failures_said():
    with patch.object(server.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "[]\n", "")) as run:
        result = CliRunner().invoke(main, ["report", "admin", "list", "--all", "--json", "--ssh", "me@login"])
    assert result.exit_code == 0 and result.output == "[]\n"
    assert run.call_args.args[0][-1].endswith("report admin list --all --json")
    with patch.object(server.subprocess, "run", return_value=subprocess.CompletedProcess([], 127, "", "qibocal: not found")):
        failed = CliRunner().invoke(main, ["report", "admin", "list", "--json", "--ssh", "me@login"])
    assert failed.exit_code != 0 and "qibocal: not found" in failed.output
