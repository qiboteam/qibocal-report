"""qibocal-agent installed where the application keeps it."""

import click
import pytest
from click.testing import CliRunner

from qibocamp.cli import main
from qibocamp.remote import agents
from qibocamp.remote import notebook_worker as worker


class Recorder:
    """The worker's runtime, recording the commands instead of running them."""

    def __init__(self, timeout):
        self.commands = []
        Recorder.last = self

    def command(self, command, capture=False):
        self.commands.append([str(part) for part in command])
        if command[:2] == ["uv", "venv"] or command[1:3] == ["-m", "venv"]:
            python = agents.tools_directory() / "bin" / "python"
            python.parent.mkdir(parents=True, exist_ok=True)
            python.write_text("")

    def close(self):
        pass


@pytest.fixture
def cache(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setattr(worker, "Runtime", Recorder)
    return tmp_path


def test_the_tools_live_in_qibocal_agent_s_own_folder(cache):
    assert agents.tools_directory() == cache / "qibocal" / "agents" / "tools"


def test_an_environment_is_made_with_uv_then_the_version_replaces_what_was_there(cache, monkeypatch):
    monkeypatch.setattr(worker, "find_uv", lambda runtime: "uv")
    executable = agents.install_tools("v0.2.0")
    first, second = Recorder.last.commands
    assert first[:4] == ["uv", "venv", "--seed", "--python"] and first[4] == agents.TOOLS_PYTHON
    assert second[-1] == "qibocal-agent[agent] @ git+https://github.com/qiboteam/qibocal-mcp-servers@v0.2.0#subdirectory=packages/agent"
    assert "--reinstall-package" in second
    assert executable == cache / "qibocal" / "agents" / "tools" / "bin" / "qibocal-agent"
    assert (cache / "qibocal/agents/tools" / agents.TOOLS_MARKER).read_text().strip() == second[-1]
    # Present already: only installed again.
    agents.install_tools("main")
    assert len(Recorder.last.commands) == 1 and Recorder.last.commands[0][-1].endswith("@main#subdirectory=packages/agent")


def test_without_uv_this_python_must_be_one_the_tools_take(cache, monkeypatch):
    monkeypatch.setattr(worker, "find_uv", lambda runtime: None)
    monkeypatch.setattr(agents.sys, "version_info", (3, 10, 0))
    with pytest.raises(click.ClickException, match="3.12 or 3.13"):
        agents.install_tools()
    monkeypatch.setattr(agents.sys, "version_info", (3, 12, 1))
    agents.install_tools()
    venv, forced, filled = Recorder.last.commands
    assert venv[1:3] == ["-m", "venv"] and "--force-reinstall" in forced and "--force-reinstall" not in filled


def test_a_version_is_a_ref_and_the_command_prints_the_path(cache, monkeypatch):
    monkeypatch.setattr(worker, "find_uv", lambda runtime: "uv")
    with pytest.raises(click.ClickException, match="Invalid version"):
        agents.install_tools("main; rm -rf ~")
    result = CliRunner().invoke(main, ["agents", "install", "--ref", "main"])
    assert result.exit_code == 0, result.output
    assert result.output.strip().endswith("qibocal/agents/tools/bin/qibocal-agent")
