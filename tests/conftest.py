import pytest


@pytest.fixture(autouse=True)
def isolate_test_config(tmp_path_factory, monkeypatch):
    """Ensure all tests use an isolated configuration directory so user configuration is never modified."""
    temp_dir = tmp_path_factory.mktemp("config")
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(temp_dir))
    return temp_dir
