"""Qibocal-compatible, append-only session and protocol comment histories."""

import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from qibocal_report.models import Note, ProtocolDetail

_NOTES = TypeAdapter(list[Note])


class NotesError(ValueError):
    """A stored history cannot be safely read or written."""


@contextmanager
def _notes_lock(path: Path):
    with path.open("a") as lock:
        if sys.platform == "win32":
            import msvcrt

            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)


def load_notes(directory: Path) -> list[Note]:
    path = directory / "notes.json"
    if path.is_symlink():
        raise NotesError("Notes files must not be symbolic links")
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return []
    except OSError as error:
        raise NotesError(f"Could not read notes: {error}") from error
    try:
        return _NOTES.validate_json(raw)
    except ValidationError as error:
        raise NotesError(f"Invalid notes in {path.name}: {error}") from error


def append_note(directory: Path, content: str, author: str | None) -> list[Note]:
    """Serialize server writers and atomically replace only the notes file."""
    note = Note(content=content, timestamp=datetime.now(timezone.utc), author=author)
    lock_path = directory / ".notes.lock"
    if lock_path.is_symlink():
        raise NotesError("Notes locks must not be symbolic links")
    temporary = directory / f".notes-{uuid.uuid4().hex}.json"
    try:
        with _notes_lock(lock_path):
            notes = load_notes(directory)
            notes.append(note)
            temporary.write_bytes(_NOTES.dump_json(notes, indent=4))
            temporary.replace(directory / "notes.json")
            return notes
    except OSError as error:
        raise NotesError(f"Could not save notes: {error}") from error
    finally:
        temporary.unlink(missing_ok=True)


def protocol_notes_directory(report_dir: Path, protocol_id: str) -> Path | None:
    """Resolve exact iterations first; legacy aliases must be unambiguous."""
    if (
        not protocol_id
        or "/" in protocol_id
        or "\\" in protocol_id
        or protocol_id in (".", "..")
    ):
        return None
    parent = report_dir / "data"
    if not parent.is_dir() or parent.is_symlink():
        return None
    exact = parent / protocol_id
    if exact.is_dir() and not exact.is_symlink():
        return exact
    candidates = {
        parent / protocol_id.replace("-", "_"),
        parent / protocol_id.replace("_", "-"),
    }
    aliases = [
        candidate
        for candidate in candidates
        if candidate.is_dir() and not candidate.is_symlink()
    ]
    if aliases:
        return aliases[0] if len(aliases) == 1 else None
    matches = [
        child
        for child in parent.iterdir()
        if child.is_dir()
        and not child.is_symlink()
        and child.name.startswith(f"{protocol_id}-")
        and child.name[len(protocol_id) + 1 :].isdigit()
    ]
    return matches[0] if len(matches) == 1 else None


def attach_protocol_notes(
    report_dir: Path, protocols: list[ProtocolDetail]
) -> list[ProtocolDetail]:
    """Overlay source histories, never snapshots embedded in a plot cache."""
    for protocol in protocols:
        directory = protocol_notes_directory(report_dir, protocol.id)
        protocol.notes = load_notes(directory) if directory else []
    return protocols
