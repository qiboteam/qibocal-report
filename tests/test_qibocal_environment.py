"""Environment administration and fresh-process plot generation tests."""

import builtins
import json
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from importlib import metadata
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient

from qibocal_report import auth, generation_worker, generator
from qibocal_report import qibocal_environment as environment
from qibocal_report.api import app
from qibocal_report.models import ProtocolDetail, QibocalStatus

_REAL_SUBPROCESS_RUN = subprocess.run


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    monkeypatch.setattr(auth, "_AUTH_ENABLED", True)
    monkeypatch.setattr(environment, "_INSTALL_LOCK", threading.Lock())
    monkeypatch.setattr(environment, "_ENVIRONMENT_LOCK", threading.Lock())
    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(side_effect=AssertionError("Real installs are forbidden")),
    )
    monkeypatch.setattr(
        httpx, "get", Mock(side_effect=AssertionError("Unexpected external request"))
    )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def credentials():
    result = {}
    for role in ("admin", "editor", "viewer"):
        user = auth.create_user(role, "password123", role)
        result[role] = {"Authorization": f"Bearer {auth.create_access_token(user)}"}
    return result


def mock_metadata(monkeypatch, *, version="0.2.7", source="pypi"):
    if version is None:
        mock = Mock(side_effect=metadata.PackageNotFoundError("qibocal"))
    else:
        origin = None
        if source == "git":
            origin = json.dumps(
                {
                    "url": "https://github.com/qiboteam/qibocal.git",
                    "vcs_info": {"vcs": "git", "commit_id": "12345"},
                }
            )
        elif source == "local":
            origin = json.dumps({"url": "file:///local/qibocal"})
        elif source == "invalid":
            origin = "{"
        mock = Mock(
            return_value=SimpleNamespace(
                version=version, read_text=Mock(return_value=origin)
            )
        )
    monkeypatch.setattr(environment.metadata, "distribution", mock)
    return mock


def mock_pypi(monkeypatch, releases=None):
    response = httpx.Response(
        200,
        request=httpx.Request("GET", environment.PYPI_URL),
        json={"releases": releases or {"0.2.7": [{}]}},
    )
    mock = Mock(return_value=response)
    monkeypatch.setattr(httpx, "get", mock)
    return mock


def mock_installer(monkeypatch, *, returncode=0, stderr="", side_effect=None):
    monkeypatch.setattr(environment.util, "find_spec", Mock(return_value=object()))
    mock = Mock(
        return_value=subprocess.CompletedProcess(
            [], returncode, "installer log", stderr
        ),
        side_effect=side_effect,
    )
    monkeypatch.setattr(subprocess, "run", mock)
    return mock


@pytest.mark.parametrize(
    ("version", "source", "expected_source"),
    [
        (None, "pypi", None),
        ("0.2.7", "pypi", "pypi"),
        ("0.2.8.dev1", "git", "git"),
        ("0.2.7", "local", None),
        ("0.2.7", "invalid", None),
    ],
)
def test_status_reads_only_package_metadata(
    monkeypatch, client, credentials, version, source, expected_source
):
    mock_metadata(monkeypatch, version=version, source=source)
    original_import = builtins.__import__

    def no_qibocal_import(name, *args, **kwargs):
        assert name != "qibocal" and not name.startswith("qibocal.")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_qibocal_import)
    response = client.get("/api/qibocal", headers=credentials["viewer"])
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "installed": version is not None,
        "version": version,
        "source": expected_source,
    }


@pytest.mark.parametrize("role", ["viewer", "editor", None])
def test_environment_administration_requires_real_admin(client, credentials, role):
    headers = credentials.get(role, {})
    for method, path, kwargs in (
        ("get", "/api/admin/qibocal/options", {}),
        ("post", "/api/admin/qibocal/install", {"json": {"option": "git"}}),
    ):
        response = getattr(client, method)(path, headers=headers, **kwargs)
        assert response.status_code == (401 if role is None else 403)
        assert response.json()["detail"]
    subprocess.run.assert_not_called()
    httpx.get.assert_not_called()


def test_anonymous_status_requires_viewer(client):
    assert client.get("/api/qibocal").status_code == 401


@pytest.mark.parametrize("with_admin_token", [False, True])
def test_open_server_cannot_administer_environment(
    monkeypatch, client, credentials, with_admin_token
):
    monkeypatch.setattr(auth, "_AUTH_ENABLED", False)
    headers = credentials["admin"] if with_admin_token else {}
    mock_metadata(monkeypatch, version=None)
    assert client.get("/api/qibocal").json()["installed"] is False
    assert client.get("/api/admin/qibocal/options", headers=headers).status_code == 403
    assert (
        client.post(
            "/api/admin/qibocal/install", json={"option": "git"}, headers=headers
        ).status_code
        == 403
    )
    subprocess.run.assert_not_called()


def test_current_user_role_not_stale_token_role(client):
    user = auth.create_user("former-admin", "password123", "viewer")
    forged_role_token = auth.create_access_token({**user, "role": "admin"})
    response = client.get(
        "/api/admin/qibocal/options",
        headers={"Authorization": f"Bearer {forged_role_token}"},
    )
    assert response.status_code == 403


def test_options_sort_filter_and_limit_versions(monkeypatch, client, credentials):
    mock_metadata(monkeypatch, version=None)
    monkeypatch.setattr(environment.platform, "python_version", lambda: "3.12.1")
    releases = {
        "0.2.9": [{}],
        "0.2.10": [{}],
        "0.3.0": [{}],
        "0.3.1": [{}],
        "0.9.9": [{}],
        "0.10.0": [{}],
        "0.10.1": [
            {"yanked": True},
            {"requires_python": ">=4"},
            {"requires_python": ">=3.10,<3.13"},
        ],
        "0.11.0": [{"requires_python": ">=3.13"}],
        "0.12.0": [{"yanked": True}],
        "1.0.0rc1": [{}],
        "1.0.0.dev1": [{}],
        "1.0.0+local": [{}],
        "garbage": [{}],
        "1.1.0": [],
        "1.2.0": [{"requires_python": "not a specifier"}],
        "1.3.0": "invalid files",
        "v0.10.0": [{}],
    }
    request = mock_pypi(monkeypatch, releases)
    response = client.get("/api/admin/qibocal/options", headers=credentials["admin"])
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    data = response.json()
    assert data["installed"] is False
    assert data["version"] is None and data["source"] is None
    assert data["pypi_error"] is None
    assert [option["version"] for option in data["options"][:-1]] == [
        "0.10.1",
        "0.10.0",
        "0.9.9",
        "0.3.1",
        "0.3.0",
    ]
    assert data["options"][0] == {
        "id": "pypi:0.10.1",
        "label": "Qibocal 0.10.1 (PyPI)",
        "source": "pypi",
        "version": "0.10.1",
    }
    assert data["options"][-1] == {
        "id": "git",
        "label": "Git repository (latest)",
        "source": "git",
        "version": None,
    }
    request.assert_called_once_with(environment.PYPI_URL, timeout=10.0)


@pytest.mark.parametrize("failure", ["network", "http", "json", "schema"])
def test_pypi_errors_explicitly_preserve_git(monkeypatch, client, credentials, failure):
    mock_metadata(monkeypatch)
    if failure == "network":
        monkeypatch.setattr(
            httpx, "get", Mock(side_effect=httpx.ConnectError("offline"))
        )
    elif failure == "http":
        monkeypatch.setattr(
            httpx,
            "get",
            Mock(
                return_value=httpx.Response(
                    503, request=httpx.Request("GET", environment.PYPI_URL)
                )
            ),
        )
    elif failure == "json":
        monkeypatch.setattr(
            httpx,
            "get",
            Mock(
                return_value=httpx.Response(
                    200,
                    text="not json",
                    request=httpx.Request("GET", environment.PYPI_URL),
                )
            ),
        )
    else:
        monkeypatch.setattr(
            httpx,
            "get",
            Mock(
                return_value=httpx.Response(
                    200,
                    json={"versions": []},
                    request=httpx.Request("GET", environment.PYPI_URL),
                )
            ),
        )
    data = client.get("/api/admin/qibocal/options", headers=credentials["admin"]).json()
    assert data["installed"] is True
    assert data["pypi_error"].startswith("Could not fetch Qibocal versions from PyPI:")
    assert [option["id"] for option in data["options"]] == ["git"]


@pytest.mark.parametrize("source", ["pypi", "git"])
def test_admin_install_uses_fixed_target_and_server_python(
    monkeypatch, client, credentials, source
):
    mock_metadata(monkeypatch, source=source)
    mock_pypi(monkeypatch)
    run = mock_installer(monkeypatch)
    response = client.post(
        "/api/admin/qibocal/install",
        headers=credentials["admin"],
        json={"option": "git" if source == "git" else "pypi:0.2.7"},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"installed": True, "version": "0.2.7", "source": source}
    args, kwargs = run.call_args
    command = args[0]
    assert command[:4] == [sys.executable, "-m", "pip", "install"]
    assert "--upgrade" in command and "--force-reinstall" in command
    assert command[-1] == (environment.GIT_URL if source == "git" else "qibocal==0.2.7")
    assert kwargs["timeout"] == environment.INSTALL_TIMEOUT
    assert kwargs.get("shell", False) is False


def test_uv_fallback_targets_server_python(monkeypatch, client, credentials):
    mock_metadata(monkeypatch, source="git")
    run = mock_installer(monkeypatch)
    monkeypatch.setattr(environment.util, "find_spec", Mock(return_value=None))
    monkeypatch.setattr(environment.shutil, "which", Mock(return_value="/tools/uv"))
    response = client.post(
        "/api/admin/qibocal/install",
        headers=credentials["admin"],
        json={"option": "git"},
    )
    assert response.status_code == 200
    command = run.call_args.args[0]
    assert command[:5] == ["/tools/uv", "pip", "install", "--python", sys.executable]
    assert "--upgrade" in command
    assert "--reinstall-package" in command and "--refresh-package" in command
    assert command[-1] == environment.GIT_URL


@pytest.mark.parametrize(
    "option",
    [
        "https://example.com/qibocal.whl",
        environment.GIT_URL,
        "git --extra-index-url evil",
        "pypi:0.2.7 --extra-index-url evil",
        "pypi:0.2.6",
        "pypi:1.0.0rc1",
        "pypi:1.0.0",
        "pypi:1.1.0",
    ],
)
def test_install_rejects_unvalidated_targets(monkeypatch, client, credentials, option):
    mock_pypi(
        monkeypatch,
        {
            "0.2.7": [{}],
            "1.0.0rc1": [{}],
            "1.0.0": [{"yanked": True}],
            "1.1.0": [{"requires_python": ">=4"}],
        },
    )
    response = client.post(
        "/api/admin/qibocal/install",
        headers=credentials["admin"],
        json={"option": option},
    )
    assert response.status_code == 400
    assert response.json()["detail"]
    subprocess.run.assert_not_called()


def test_pypi_install_requires_successful_server_validation(
    monkeypatch, client, credentials
):
    monkeypatch.setattr(httpx, "get", Mock(side_effect=httpx.ConnectError("offline")))
    response = client.post(
        "/api/admin/qibocal/install",
        headers=credentials["admin"],
        json={"option": "pypi:0.2.7"},
    )
    assert response.status_code == 502
    assert "offline" in response.json()["detail"]
    subprocess.run.assert_not_called()


def test_git_install_does_not_depend_on_pypi(monkeypatch, client, credentials):
    mock_metadata(monkeypatch, source="git")
    mock_installer(monkeypatch)
    response = client.post(
        "/api/admin/qibocal/install",
        headers=credentials["admin"],
        json={"option": "git"},
    )
    assert response.status_code == 200
    httpx.get.assert_not_called()


def test_install_preserves_existing_report_caches(monkeypatch, tmp_path):
    cached_paths = []
    for report in ("current-report", "unrelated-report"):
        cache = tmp_path / report / "report" / "protocols.json"
        cache.parent.mkdir(parents=True)
        cache.write_text('[{"id": "rabi", "name": "Rabi", "figures": []}]')
        cached_paths.append((cache, cache.read_text()))
    mock_metadata(monkeypatch, source="git")
    mock_installer(monkeypatch)
    assert environment.install_qibocal("git").installed
    assert all(path.read_text() == content for path, content in cached_paths)


def test_metadata_read_failures_have_specific_details(monkeypatch, client, credentials):
    monkeypatch.setattr(
        environment.metadata, "distribution", Mock(side_effect=OSError("access denied"))
    )
    response = client.get("/api/qibocal", headers=credentials["viewer"])
    assert response.status_code == 500
    assert (
        response.json()["detail"]
        == "Could not read Qibocal package metadata: access denied"
    )


def test_missing_installer_is_explicit(monkeypatch, client, credentials):
    monkeypatch.setattr(environment.util, "find_spec", Mock(return_value=None))
    monkeypatch.setattr(environment.shutil, "which", Mock(return_value=None))
    response = client.post(
        "/api/admin/qibocal/install",
        headers=credentials["admin"],
        json={"option": "git"},
    )
    assert response.status_code == 503
    assert "No package installer" in response.json()["detail"]
    subprocess.run.assert_not_called()


@pytest.mark.parametrize(
    ("failure", "status", "message"),
    [
        ("exit", 502, "dependency conflict"),
        ("timeout", 504, "timed out"),
        ("start", 503, "not permitted"),
        ("metadata", 500, "metadata is missing"),
        ("version", 500, "does not match"),
        ("invalid-version", 500, "does not match"),
        ("source", 500, "does not match"),
    ],
)
def test_install_failures_and_lock_cleanup(
    monkeypatch, client, credentials, failure, status, message
):
    mock_pypi(monkeypatch)
    mock_metadata(
        monkeypatch,
        version=None
        if failure == "metadata"
        else "0.2.6"
        if failure == "version"
        else "not-a-version"
        if failure == "invalid-version"
        else "0.2.7",
        source="git" if failure == "source" else "pypi",
    )
    side_effect = (
        subprocess.TimeoutExpired(["pip"], 600)
        if failure == "timeout"
        else OSError("not permitted")
        if failure == "start"
        else None
    )
    mock_installer(
        monkeypatch,
        returncode=1 if failure == "exit" else 0,
        stderr="dependency conflict",
        side_effect=side_effect,
    )
    response = client.post(
        "/api/admin/qibocal/install",
        headers=credentials["admin"],
        json={"option": "pypi:0.2.7"},
    )
    assert response.status_code == status
    assert message in response.json()["detail"]
    assert environment._INSTALL_LOCK.acquire(blocking=False)
    environment._INSTALL_LOCK.release()
    assert environment._ENVIRONMENT_LOCK.acquire(blocking=False)
    environment._ENVIRONMENT_LOCK.release()


def test_concurrent_install_conflicts_and_generation_waits(
    monkeypatch, client, credentials, tmp_path
):
    mock_metadata(monkeypatch, source="git")
    monkeypatch.setattr(environment.util, "find_spec", Mock(return_value=object()))
    installation_started = threading.Event()
    release_installation = threading.Event()
    generation_started = threading.Event()

    def run(command, **kwargs):
        if command[1:3] == ["-m", "pip"]:
            installation_started.set()
            assert release_installation.wait(5)
        else:
            generation_started.set()
            Path(command[-1]).write_text(
                json.dumps(
                    {
                        "protocols": [{"id": "rabi", "name": "Rabi", "figures": []}],
                        "error": None,
                        "error_code": None,
                    }
                )
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    with ThreadPoolExecutor(max_workers=2) as executor:
        install = executor.submit(
            client.post,
            "/api/admin/qibocal/install",
            headers=credentials["admin"],
            json={"option": "git"},
        )
        try:
            assert installation_started.wait(5)
            conflict = client.post(
                "/api/admin/qibocal/install",
                headers=credentials["admin"],
                json={"option": "git"},
            )
            assert conflict.status_code == 409
            assert "already in progress" in conflict.json()["detail"]
            generation = executor.submit(
                generator._generate_qibocal_protocols, tmp_path
            )
            assert not generation_started.wait(0.1)
        finally:
            release_installation.set()
        assert install.result(timeout=5).status_code == 200
        protocols, error = generation.result(timeout=5)
        assert protocols[0].id == "rabi" and error is None
        assert generation_started.is_set()


def test_install_waits_for_active_generation(monkeypatch):
    mock_metadata(monkeypatch, source="git")
    installer_called = threading.Event()
    waiting_for_environment = threading.Event()

    def run(*args, **kwargs):
        installer_called.set()
        return subprocess.CompletedProcess([], 0, "", "")

    mock_installer(monkeypatch, side_effect=run)
    original_command = environment._installer_command

    def command(target):
        result = original_command(target)
        waiting_for_environment.set()
        return result

    monkeypatch.setattr(environment, "_installer_command", command)
    with ThreadPoolExecutor(max_workers=1) as executor:
        with environment.generation_environment():
            install = executor.submit(environment.install_qibocal, "git")
            assert waiting_for_environment.wait(5)
            assert not installer_called.wait(0.1)
        assert install.result(timeout=5).installed is True


def test_generation_uses_result_file_not_qibocal_logs(monkeypatch, tmp_path):
    def run(command, **kwargs):
        assert command[:3] == [sys.executable, "-m", "qibocal_report.generation_worker"]
        assert command[-2] == str(tmp_path.resolve())
        assert kwargs["timeout"] == environment.GENERATION_TIMEOUT
        assert kwargs.get("shell", False) is False
        Path(command[-1]).write_text(
            json.dumps(
                {
                    "protocols": [
                        {"id": "rabi", "name": "Rabi", "figures": [{"data": []}]}
                    ],
                    "error": None,
                    "error_code": None,
                }
            )
        )
        return subprocess.CompletedProcess(command, 0, "Qibocal logs, not JSON", "")

    monkeypatch.setattr(subprocess, "run", run)
    protocols, error = generator._generate_qibocal_protocols(tmp_path)
    assert error is None and protocols[0].id == "rabi"
    assert not list(tmp_path.glob(".qibocal-generation-*"))


@pytest.mark.parametrize("failure", ["timeout", "exit", "no-result", "bad-result"])
def test_worker_failures_are_informative_and_cleaned(monkeypatch, tmp_path, failure):
    def run(command, **kwargs):
        if failure == "timeout":
            Path(command[-1]).write_text("partial")
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        if failure == "bad-result":
            Path(command[-1]).write_text("log instead of JSON")
        return subprocess.CompletedProcess(
            command, 1 if failure == "exit" else 0, "", "dependency failure"
        )

    monkeypatch.setattr(subprocess, "run", run)
    protocols = generator.generate_report_on_the_fly(tmp_path)
    assert protocols[0].status == "error"
    assert protocols[0].error
    assert protocols[0].error_code is None
    assert "not installed" not in protocols[0].error
    assert not list(tmp_path.glob(".qibocal-generation-*"))


@pytest.mark.parametrize(
    ("missing_name", "installed", "expected_code"),
    [
        ("qibocal", False, "qibocal_not_installed"),
        ("qibocal", True, None),
        ("qibolab", True, None),
        ("API", True, None),
    ],
)
def test_native_import_errors_only_label_real_absence(
    monkeypatch, tmp_path, missing_name, installed, expected_code
):
    original_import = builtins.__import__

    def import_qibocal(name, *args, **kwargs):
        if name.startswith("qibocal."):
            if missing_name == "API":
                raise ImportError("cannot import name Output")
            raise ModuleNotFoundError(
                f"No module named '{missing_name}'", name=missing_name
            )
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_qibocal)
    monkeypatch.setattr(
        generator,
        "get_qibocal_status",
        lambda: QibocalStatus(
            installed=installed, version="0.2.7" if installed else None
        ),
    )
    protocols, error = generator._generate_qibocal_protocols_native(tmp_path)
    assert protocols is None
    assert getattr(error, "error_code", None) == expected_code
    if expected_code:
        assert "Qibocal is not installed" in error
    else:
        assert "Error importing Qibocal or its dependencies" in error
        assert "not installed" not in error


def test_missing_code_survives_worker_and_protocol_serialization(monkeypatch, tmp_path):
    def run(command, **kwargs):
        Path(command[-1]).write_text(
            json.dumps(
                {
                    "protocols": None,
                    "error": "Qibocal is not installed in the environment.",
                    "error_code": "qibocal_not_installed",
                }
            )
        )
        return subprocess.CompletedProcess(command, 0, "many logs", "")

    monkeypatch.setattr(subprocess, "run", run)
    detail = generator.generate_report_on_the_fly(tmp_path)[0]
    assert detail.status == "error"
    assert detail.model_dump()["error_code"] == "qibocal_not_installed"


def test_legacy_mocked_generator_entrypoint_remains_compatible(monkeypatch, tmp_path):
    monkeypatch.setattr(
        generator,
        "_generate_qibocal_protocols",
        lambda path: (None, "Qibocal is not installed in the environment."),
    )
    protocol = generator.generate_report_on_the_fly(tmp_path)[0]
    assert "Qibocal is not installed" in protocol.error
    assert protocol.error_code is None


def test_all_native_errors_preserved_without_false_absence(monkeypatch, tmp_path):
    detail = ProtocolDetail(
        id="rabi",
        name="Rabi",
        status="error",
        error="Fit data is incompatible",
        html="<p>Partial results</p>",
    )
    monkeypatch.setattr(
        generator, "_generate_qibocal_protocols", lambda path: ([detail], None)
    )
    assert generator.generate_report_on_the_fly(tmp_path) == [detail]
    assert not generator.has_cached_report(tmp_path)


def test_empty_native_results_do_not_claim_qibocal_absence(monkeypatch, tmp_path):
    monkeypatch.setattr(
        generator, "_generate_qibocal_protocols", lambda path: ([], None)
    )
    protocol = generator.generate_report_on_the_fly(tmp_path)[0]
    assert "not installed" not in protocol.error
    assert protocol.error_code is None


@pytest.mark.parametrize("targets", [[], [0], [0, 1]])
def test_native_target_errors_preserve_details_and_partial_output(
    monkeypatch, tmp_path, targets
):
    task = SimpleNamespace(operation_name="rabi", targets=targets)
    completed = SimpleNamespace(task=task)
    output_module = ModuleType("qibocal.auto.output")
    output_module.Output = SimpleNamespace(
        load=lambda path: SimpleNamespace(history={"rabi": completed})
    )
    report_module = ModuleType("qibocal.cli.report")

    def figures(completed, target):
        if target == 1:
            return [{"data": [], "layout": {}}], "<p>Target 1 succeeded</p>"
        raise RuntimeError("fitting did not converge")

    report_module.generate_figures_and_report = figures
    monkeypatch.setitem(sys.modules, "qibocal.auto.output", output_module)
    monkeypatch.setitem(sys.modules, "qibocal.cli.report", report_module)
    protocols, error = generator._generate_qibocal_protocols_native(tmp_path)
    assert error is None
    assert protocols[0].status == "error"
    assert "fitting did not converge" in protocols[0].error
    assert protocols[0].error_code is None
    assert bool(protocols[0].figures) == (targets == [0, 1])


def test_worker_serializes_array_like_values_and_logs(monkeypatch, tmp_path, capsys):
    class ArrayLike:
        def tolist(self):
            return [1, 2]

    def native(path):
        print("Qibocal emitted a log")
        return [
            ProtocolDetail(
                id="rabi", name="Rabi", figures=[{"data": [{"x": ArrayLike()}]}]
            )
        ], None

    result = tmp_path / "worker-result.json"
    monkeypatch.setattr(generation_worker, "_generate_qibocal_protocols_native", native)
    monkeypatch.setattr(sys, "argv", ["worker", str(tmp_path), str(result)])
    generation_worker.main()
    assert "Qibocal emitted a log" in capsys.readouterr().out
    payload = json.loads(result.read_text())
    assert payload["protocols"][0]["figures"][0]["data"][0]["x"] == [1, 2]


def test_fresh_worker_uses_changed_version_not_stale_parent_module(
    monkeypatch, tmp_path
):
    package = tmp_path / "packages" / "qibocal"
    for subpackage in ("", "auto", "cli"):
        directory = package / subpackage
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").write_text("")
    (package / "auto" / "output.py").write_text(
        "from types import SimpleNamespace\n"
        "class Output:\n"
        "    @staticmethod\n"
        "    def load(path):\n"
        "        task = SimpleNamespace(operation_name='rabi', targets=[])\n"
        "        return SimpleNamespace(history={'rabi': SimpleNamespace(task=task)})\n"
    )
    (package / "cli" / "report.py").write_text(
        "from qibocal import __version__\n"
        "def generate_figures_and_report(completed, target):\n"
        "    print('Qibocal worker log')\n"
        "    return [], '<p>' + __version__ + '</p>'\n"
    )
    stale = ModuleType("qibocal")
    stale.__version__ = "stale"
    monkeypatch.setitem(sys.modules, "qibocal", stale)
    monkeypatch.setattr(subprocess, "run", _REAL_SUBPROCESS_RUN)
    monkeypatch.setenv("PYTHONPATH", str(package.parent))
    for version in ("1.0", "2.0.1"):
        (package / "__init__.py").write_text(f"__version__ = '{version}'\n")
        protocols, error = generator._generate_qibocal_protocols(tmp_path)
        assert error is None
        assert protocols and protocols[0].status == "success"
        assert protocols[0].html == f"<p>{version}</p>"
    assert sys.modules["qibocal"] is stale
    assert not list(tmp_path.glob(".qibocal-generation-*"))
