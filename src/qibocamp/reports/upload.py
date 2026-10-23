"""Reports received from another server: a zip of one report folder, unpacked here.

The sending side is the dashboard, which downloads the full report from one
server — the same zip as its Download button — and sends it to another. The
archive is checked before anything is written: one top-level folder, which
is a report; no absolute path, no `..`, no link; no more than the limit once
unpacked. It is unpacked beside its destination and moved into place in one
step, so a failed upload leaves nothing behind, and a report already there
is never overwritten.
"""

import os
import shutil
import stat
import uuid
import zipfile
from pathlib import Path, PurePosixPath

# How much a single report may weigh once unpacked; QIBOCAMP_UPLOAD_LIMIT, in bytes.
DEFAULT_LIMIT = 4 * 1024**3


class UploadError(Exception):
    """An upload refused, with the HTTP status that says why."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def upload_limit() -> int:
    try:
        return int(os.environ.get("QIBOCAMP_UPLOAD_LIMIT", DEFAULT_LIMIT))
    except ValueError:
        return DEFAULT_LIMIT


def _top_folder(archive: zipfile.ZipFile) -> str:
    """The one folder the archive holds, after checking every member's path."""
    tops = set()
    for member in archive.infolist():
        name = member.filename
        path = PurePosixPath(name)
        # A drive (`C:`) is unsafe; a colon is not — Qibocal names its folders by the time.
        drive = len(path.parts[0]) == 2 and path.parts[0][1] == ":" if path.parts else False
        if not name or name.startswith("/") or "\\" in name or drive or ".." in path.parts:
            raise UploadError(400, f"The archive holds an unsafe path: {name!r}.")
        if stat.S_ISLNK(member.external_attr >> 16):
            raise UploadError(400, f"The archive holds a link: {name!r}.")
        tops.add(path.parts[0])
    if len(tops) != 1:
        raise UploadError(400, "The archive must hold exactly one report folder.")
    top = tops.pop()
    if top.startswith("."):
        raise UploadError(400, "The report folder cannot be a hidden one.")
    return top


def receive_report(archive_path: Path, root: Path) -> Path:
    """Unpack the report in `archive_path` under `root`, and answer where it went."""
    try:
        archive = zipfile.ZipFile(archive_path)
    except zipfile.BadZipFile as error:
        raise UploadError(400, "The upload is not a zip archive.") from error
    with archive:
        top = _top_folder(archive)
        if sum(member.file_size for member in archive.infolist()) > upload_limit():
            raise UploadError(413, "The report is larger than this server accepts.")
        destination = root / top
        if destination.exists():
            raise UploadError(409, f"A report named {top} is already on this server.")
        staging = root / f".upload-{uuid.uuid4().hex}"
        staging.mkdir(parents=True)
        try:
            archive.extractall(staging)
            unpacked = staging / top
            if not (unpacked / "meta.json").is_file() and not (unpacked / "report" / "meta.json").is_file():
                raise UploadError(400, "The archive holds no report: there is no meta.json in its folder.")
            if destination.exists():
                raise UploadError(409, f"A report named {top} is already on this server.")
            unpacked.rename(destination)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
    return destination
