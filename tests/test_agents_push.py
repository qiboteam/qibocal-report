"""Agent configurations pushed to another machine's agents.json."""

import json
import os
import subprocess
import sys
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from qibocal_report.cli import main
from qibocal_report.remote import agents

# Patching `agents.subprocess.run` patches the module: the real one, kept.
REAL_RUN = subprocess.run


def run_merge_here(tmp_path):
    """Run the remote merge script with this Python, as ssh would run it there."""
    def run(command, **kwargs):
        import shlex
        python, flag, script, request = shlex.split(command[-1])
        assert (python, flag) == ("python3", "-c")
        env = {**os.environ, "QIBOCAL_AGENTS_CONFIG_DIR": str(tmp_path)}
        return REAL_RUN([sys.executable, "-c", script, request], capture_output=True, text=True, env=env, check=False)
    return run


def test_pushed_entries_merge_into_the_remote_file_and_leave_the_rest(tmp_path):
    (tmp_path / "agents.json").write_text(json.dumps({
        "agents": {"default": {"platform": "keep"}, "theirs": {"platform": "a"}, "old": {"platform": "b"}},
    }))
    with patch.object(agents.subprocess, "run", side_effect=run_merge_here(tmp_path)):
        answer = agents.push("me@login", {"lab": {"platform": "qw5q", "partition": "qpu"}}, remove=["old"])
    document = json.loads((tmp_path / "agents.json").read_text())
    assert document["agents"] == {
        "default": {"platform": "keep"}, "theirs": {"platform": "a"}, "lab": {"platform": "qw5q", "partition": "qpu"},
    }, "the configurations not pushed are left as they are"
    assert answer["agents"] == ["default", "lab", "theirs"]
    assert "version" not in document, "qibocal-agent refuses unknown keys"


def test_a_file_that_is_not_json_is_left_alone(tmp_path):
    (tmp_path / "agents.json").write_text("{broken")
    with patch.object(agents.subprocess, "run", side_effect=run_merge_here(tmp_path)):
        with pytest.raises(click.ClickException, match="not valid JSON"):
            agents.push("me@login", {"lab": {"platform": "x"}})
    assert (tmp_path / "agents.json").read_text() == "{broken"


def test_names_are_checked_and_the_command_takes_json():
    with pytest.raises(click.ClickException, match="Invalid agent name"):
        agents.push("me@login", {"bad name": {}})
    for reserved in ("agent", "agents"):
        with pytest.raises(click.ClickException, match="Invalid agent name"):
            agents.push("me@login", {reserved: {}})
    with patch.object(agents, "push", return_value={"path": "p", "agents": ["lab"]}) as push:
        result = CliRunner().invoke(main, ["agents", "push", "me@login", "--agents", '{"lab": {"platform": "x"}}', "--remove", "old"])
    assert result.exit_code == 0, result.output
    assert push.call_args.args == ("me@login", {"lab": {"platform": "x"}}, ["old"])
    bad = CliRunner().invoke(main, ["agents", "push", "me@login", "--agents", "[1]"])
    assert bad.exit_code != 0
