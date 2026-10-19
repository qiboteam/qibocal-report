import pytest


@pytest.fixture(autouse=True)
def isolate_test_config(tmp_path_factory, monkeypatch):
    """Ensure all tests use an isolated configuration directory so user configuration is never modified."""
    temp_dir = tmp_path_factory.mktemp("config")
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(temp_dir))
    return temp_dir


@pytest.fixture(autouse=True)
def installer_is_pip(monkeypatch):
    """The workers' installer: pip, unless a test chooses uv.

    The workers use uv when they find or install one; the tests would then
    depend on the machine they run on, and a missing uv would be installed.
    """
    from qibocal_report.remote import notebook_worker, report_worker

    for namespace in (notebook_worker._UV, report_worker._shared["_UV"]):
        monkeypatch.setitem(namespace, "path", None)
