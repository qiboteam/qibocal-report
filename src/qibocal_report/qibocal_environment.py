"""Inspect and administer Qibocal in the running server's Python environment."""

import codecs
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as ReaderTimeoutError
from contextlib import contextmanager
from importlib import metadata, util

import httpx
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from qibocal_report.logger import log_output
from qibocal_report.models import QibocalOption, QibocalOptions, QibocalStatus

PYPI_URL = "https://pypi.org/pypi/qibocal/json"
GIT_URL = "git+https://github.com/qiboteam/qibocal.git"
INSTALL_TIMEOUT = 600
GENERATION_TIMEOUT = 300
_INSTALL_LOCK = threading.Lock()
_ENVIRONMENT_LOCK = threading.Lock()
INSTALL_OUTPUT_CHUNK_BYTES = 4096
INSTALL_FAILURE_TAIL = 2000


class EnvironmentOperationError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@contextmanager
def generation_environment():
    """Keep package files stable for the lifetime of a generation subprocess."""
    if not _ENVIRONMENT_LOCK.acquire(timeout=INSTALL_TIMEOUT + GENERATION_TIMEOUT + 30):
        raise EnvironmentOperationError(
            409, "The Qibocal environment is busy; try plot generation again."
        )
    try:
        yield
    finally:
        _ENVIRONMENT_LOCK.release()


def _read_status() -> QibocalStatus:
    try:
        distribution = metadata.distribution("qibocal")
        version = distribution.version or None
        direct_url = distribution.read_text("direct_url.json")
    except metadata.PackageNotFoundError:
        return QibocalStatus(installed=False)
    except (OSError, ValueError) as error:
        raise EnvironmentOperationError(
            500, f"Could not read Qibocal package metadata: {error}"
        ) from error

    source = "pypi"
    if direct_url:
        try:
            origin = json.loads(direct_url)
            source = (
                "git"
                if isinstance(origin, dict)
                and isinstance(origin.get("vcs_info"), dict)
                and origin["vcs_info"].get("vcs") == "git"
                else None
            )
        except (ValueError, TypeError):
            source = None
    return QibocalStatus(installed=True, version=version, source=source)


def get_qibocal_status() -> QibocalStatus:
    """Read distribution metadata without importing Qibocal or its dependencies."""
    with generation_environment():
        return _read_status()


def _compatible_file(file: object, python_version: Version) -> bool:
    if not isinstance(file, dict) or file.get("yanked"):
        return False
    requires_python = file.get("requires_python")
    if not requires_python:
        return True
    try:
        return SpecifierSet(requires_python).contains(python_version, prereleases=True)
    except (InvalidSpecifier, TypeError):
        return False


def _pypi_options() -> tuple[list[QibocalOption], str | None]:
    try:
        response = httpx.get(PYPI_URL, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or not isinstance(data.get("releases"), dict):
            raise TypeError("PyPI returned an invalid release listing")
        python_version = Version(platform.python_version())
        versions: set[Version] = set()
        for version_text, files in data["releases"].items():
            try:
                version = Version(version_text)
            except (InvalidVersion, TypeError):
                continue
            if version.is_prerelease or version.is_devrelease or version.local:
                continue
            if isinstance(files, list) and any(
                _compatible_file(file, python_version) for file in files
            ):
                versions.add(version)
        return [
            QibocalOption(
                id=f"pypi:{version}",
                label=f"Qibocal {version} (PyPI)",
                source="pypi",
                version=str(version),
            )
            for version in sorted(versions, reverse=True)[:5]
        ], None
    except (httpx.HTTPError, ValueError, TypeError) as error:
        return [], f"Could not fetch Qibocal versions from PyPI: {error}"


def get_qibocal_options() -> QibocalOptions:
    status = get_qibocal_status()
    options, error = _pypi_options()
    options.append(
        QibocalOption(
            id="git", label="Git repository (latest)", source="git", version=None
        )
    )
    return QibocalOptions(**status.model_dump(), options=options, pypi_error=error)


def _installation_target(option: str) -> tuple[str, str, str | None]:
    if option == "git":
        return GIT_URL, "git", None
    if not option.startswith("pypi:"):
        raise EnvironmentOperationError(400, "Invalid Qibocal installation option.")
    try:
        Version(option.removeprefix("pypi:"))
    except InvalidVersion as error:
        raise EnvironmentOperationError(
            400, "Invalid Qibocal installation option."
        ) from error
    options, pypi_error = _pypi_options()
    if pypi_error:
        raise EnvironmentOperationError(502, pypi_error)
    selected = next((item for item in options if item.id == option), None)
    if selected is None:
        raise EnvironmentOperationError(
            400,
            "Choose one of the recent compatible Qibocal versions "
            "offered by the server.",
        )
    return f"qibocal=={selected.version}", "pypi", selected.version


def _installer_command(target: str) -> list[str]:
    if util.find_spec("pip") is not None:
        return [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--force-reinstall",
            "--disable-pip-version-check",
            "--no-input",
            "--index-url",
            "https://pypi.org/simple",
            target,
        ]
    uv = shutil.which("uv")
    if uv:
        return [
            uv,
            "pip",
            "install",
            "--python",
            sys.executable,
            "--upgrade",
            "--reinstall-package",
            "qibocal",
            "--refresh-package",
            "qibocal",
            "--index-url",
            "https://pypi.org/simple",
            target,
        ]
    raise EnvironmentOperationError(
        503,
        "No package installer is available: install pip in the server's Python "
        "environment or make uv available on the server PATH.",
    )


def _kill_installer(process: subprocess.Popen) -> None:
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        process.kill()


def _run_installer(
    command: list[str], progress: Callable[[str], None]
) -> tuple[int, str]:
    env = os.environ.copy()
    env.update(
        PYTHONUNBUFFERED="1",
        FORCE_COLOR="1",
        CLICOLOR_FORCE="1",
        UV_COLOR="always",
        PIP_PROGRESS_BAR="off",
    )
    env.pop("NO_COLOR", None)
    env.pop("ANSI_COLORS_DISABLED", None)
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            env=env,
            start_new_session=os.name == "posix",
        )
    except OSError as error:
        raise EnvironmentOperationError(
            503, f"Could not start the Qibocal package installer: {error}"
        ) from error

    completed = False
    tail = ""
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    deadline = time.monotonic() + INSTALL_TIMEOUT
    reader: ThreadPoolExecutor | None = None

    def emit(text: str) -> None:
        nonlocal tail
        if text:
            tail = (tail + text)[-INSTALL_FAILURE_TAIL:]
            progress(text)

    try:
        if process.stdout is None:
            raise RuntimeError("The Qibocal installer output pipe is missing.")
        reader = ThreadPoolExecutor(max_workers=1, thread_name_prefix="qibocal-output")
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, INSTALL_TIMEOUT)
            # At most one bounded read is outstanding; a pipe read cannot prevent
            # the installer worker from enforcing its deadline.
            pending = reader.submit(process.stdout.read, INSTALL_OUTPUT_CHUNK_BYTES)
            try:
                chunk = pending.result(timeout=remaining)
            except ReaderTimeoutError as error:
                raise subprocess.TimeoutExpired(command, INSTALL_TIMEOUT) from error
            if not chunk:
                break
            emit(decoder.decode(chunk))
        emit(decoder.decode(b"", final=True))
        returncode = process.wait(timeout=max(0, deadline - time.monotonic()))
        completed = True
        return returncode, tail
    except subprocess.TimeoutExpired as error:
        raise EnvironmentOperationError(
            504, f"Qibocal installation timed out after {INSTALL_TIMEOUT} seconds."
        ) from error
    finally:
        try:
            if not completed:
                _kill_installer(process)
            process.wait()
        finally:
            try:
                if process.stdout is not None:
                    process.stdout.close()
            finally:
                if reader is not None:
                    reader.shutdown(wait=True, cancel_futures=True)


def install_qibocal(
    option: str, progress: Callable[[str], None] | None = None
) -> QibocalStatus:
    """Install a validated official target, optionally reporting live ANSI output."""
    if not _INSTALL_LOCK.acquire(blocking=False):
        raise EnvironmentOperationError(
            409, "A Qibocal installation is already in progress."
        )
    environment_acquired = False
    try:
        target, source, version = _installation_target(option)
        command = _installer_command(target)
        environment_acquired = _ENVIRONMENT_LOCK.acquire(
            timeout=GENERATION_TIMEOUT + 30
        )
        if not environment_acquired:
            raise EnvironmentOperationError(
                409, "Qibocal plot generation is still running; try installation again."
            )

        def emit(text: str) -> None:
            log_output(text)
            if progress is not None:
                progress(text)

        # The first event follows validation and lock acquisition, so streaming
        # callers can still return ordinary HTTP errors for rejected requests.
        emit(f"\x1b[36mInstalling {target}...\x1b[0m\n")
        returncode, tail = _run_installer(command, emit)
        if returncode:
            output = tail.strip() or "No installer output."
            raise EnvironmentOperationError(
                502,
                f"Qibocal installation failed (exit {returncode}): {output}",
            )
        status = _read_status()
        if not status.installed or not status.version:
            raise EnvironmentOperationError(
                500, "The installer finished, but Qibocal package metadata is missing."
            )
        try:
            version_matches = version is None or Version(status.version) == Version(
                version
            )
        except InvalidVersion:
            version_matches = False
        if status.source != source or not version_matches:
            raise EnvironmentOperationError(
                500,
                "The installer finished, but Qibocal metadata does not match "
                "the requested installation.",
            )
        return status
    finally:
        if environment_acquired:
            _ENVIRONMENT_LOCK.release()
        _INSTALL_LOCK.release()
