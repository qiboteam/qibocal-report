"""The configuration files: their version, and the servers they register."""

import json

import pytest

from qibocal_report import config


@pytest.fixture
def config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(tmp_path))
    return tmp_path


def test_servers_are_written_versioned_and_read_only_so(config_dir):
    config.save_servers([{"id": "a", "name": "one", "url": "http://localhost:8000"}])
    written = json.loads((config_dir / "servers.json").read_text())
    assert written["version"] == config.CONFIG_VERSION
    assert [s["id"] for s in written["servers"]] == ["a"]
    assert [s["id"] for s in config.load_servers()] == ["a"]

    # A file without a version is not ours: not read, never replaced.
    bare = json.dumps([{"id": "b", "url": "http://x"}])
    (config_dir / "servers.json").write_text(bare)
    assert config.load_servers() == []
    with pytest.raises(config.IncompatibleConfig, match="no format version"):
        config.save_servers([])
    assert (config_dir / "servers.json").read_text() == bare


def test_a_file_of_another_version_is_ignored_and_never_replaced(config_dir):
    path = config_dir / "servers.json"
    foreign = {"version": config.CONFIG_VERSION + 1, "servers": [{"id": "future"}]}
    path.write_text(json.dumps(foreign))

    assert config.load_servers() == [], "nothing of ours in it"
    with pytest.raises(config.IncompatibleConfig, match="another version"):
        config.save_servers([])
    assert json.loads(path.read_text()) == foreign, "left exactly as it was"


def test_registering_by_name_moves_the_entry_to_the_new_address(config_dir):
    config.save_servers([])
    first = config.add_server("http://localhost:41000", name="quiet-curie", description="first")
    moved = config.add_server("http://localhost:42000", name="quiet-curie", description="second")
    assert moved["id"] == first["id"]
    assert moved["url"] == "http://localhost:42000"
    assert moved["description"] == "second"
    assert len(config.load_servers()) == 1, "the same server, not a twin"

    # The address still identifies a server: the same one is returned untouched.
    same = config.add_server("http://localhost:42000", name="another-name")
    assert same["id"] == first["id"]
    assert same["name"] == "quiet-curie"
    # A different name at a different address is a different server.
    other = config.add_server("http://localhost:43000", name="brave-bohr")
    assert other["id"] != first["id"]
    assert len(config.load_servers()) == 2


def test_the_version_is_declared_or_absent():
    assert config.declared_version({"version": 3}) == 3
    assert config.declared_version({"version": True}) is None
    assert config.declared_version([]) is None
    assert config.is_compatible([]) is False
    assert config.is_compatible({}) is False
    assert config.is_compatible({"version": config.CONFIG_VERSION}) is True
    assert config.is_compatible({"version": config.CONFIG_VERSION + 1}) is False
