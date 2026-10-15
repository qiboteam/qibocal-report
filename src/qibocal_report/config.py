"""Server and configuration management for qibocal-report."""

import json
import os
import random
import uuid
from pathlib import Path
from typing import Any

ADJECTIVES = [
    "zen",
    "clever",
    "brave",
    "quantum",
    "eager",
    "swift",
    "calm",
    "keen",
    "bold",
    "radiant",
    "lucid",
    "serene",
    "agile",
    "stellar",
]

SCIENTISTS = [
    "bohr",
    "curie",
    "feynman",
    "dirac",
    "planck",
    "fermi",
    "bell",
    "schrodinger",
    "einstein",
    "wu",
    "aspect",
    "zeilinger",
    "clauser",
]


def generate_docker_name() -> str:
    """Generate a docker-like human-readable name."""
    return f"{random.choice(ADJECTIVES)}-{random.choice(SCIENTISTS)}"


def get_config_dir(*, create: bool = True) -> Path:
    """Return the configuration directory, optionally creating it."""
    custom_dir = os.environ.get("QIBOCAL_REPORT_CONFIG_DIR")
    if custom_dir:
        path = Path(custom_dir)
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        path = root / "qibocal"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir(*, create: bool = True) -> Path:
    """Return the data directory, optionally creating it.

    Configuration describes servers; data is what they serve. The two follow
    the matching XDG conventions: ``$XDG_CONFIG_HOME`` for the first,
    ``$XDG_DATA_HOME`` (``~/.local/share``) for the second.
    """
    custom_dir = os.environ.get("QIBOCAL_REPORT_DATA_DIR")
    if custom_dir:
        path = Path(custom_dir)
    else:
        root = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
        path = root / "qibocal"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_reports_dir(*, create: bool = True) -> Path:
    """The directory served when none is named, created on first use."""
    path = get_data_dir(create=create) / "reports"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_file(*, create: bool = True) -> Path:
    """Return path to servers.json."""
    return get_config_dir(create=create) / "servers.json"


def get_default_servers() -> list[dict[str, Any]]:
    """Return default initial server list."""
    return [
        {
            "id": "srv-local",
            "name": "local-instance",
            "url": "http://127.0.0.1:8000",
            "description": "Local Qibocal Report Server",
            "avatar": "quantum-ring",
            "is_default": True,
            "created_at": "2024-12-20T10:00:00Z",
        }
    ]


# The format of the configuration files this version reads and writes.
#
# Every file is an object carrying a ``version``: ``servers.json`` keeps its
# entries under ``servers``, ``notebooks.json`` under ``connections``,
# ``auth.json`` and the launcher's preferences next to the version itself. A
# file without a version is one written before versions were, and is read as
# the current format. A file with another version is ignored — read as
# empty, never overwritten — so that an application of one version does not
# destroy what another wrote; the launcher lists such files for a migration
# by hand. There is no automatic migration, on purpose.
CONFIG_VERSION = 1


class IncompatibleConfig(OSError):
    """A configuration file of another version, which must not be replaced."""

    def __init__(self, path: Path, found: int):
        super().__init__(
            f"'{path}' was written by another version of qibocal-report "
            f"(format {found}; this one reads {CONFIG_VERSION}). "
            "It is left as it is until migrated by hand."
        )
        self.path = path
        self.found = found


def declared_version(data: Any) -> int | None:
    """The version a document declares, if it is a versioned object."""
    if isinstance(data, dict):
        version = data.get("version")
        if isinstance(version, int) and not isinstance(version, bool):
            return version
    return None


def is_compatible(data: Any) -> bool:
    """Whether a document is of this version, or of none."""
    version = declared_version(data)
    return version is None or version == CONFIG_VERSION


def _read_document(path: Path) -> Any:
    """The parsed file, ``None`` when absent, unreadable or of another version."""
    try:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
    except (json.JSONDecodeError, OSError):
        return None
    return data if is_compatible(data) else None


def guard_write(path: Path) -> None:
    """Refuse to replace a file of another version."""
    try:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
    except (json.JSONDecodeError, OSError):
        return
    version = declared_version(data)
    if version is not None and version != CONFIG_VERSION:
        raise IncompatibleConfig(path, version)


def load_servers() -> list[dict[str, Any]]:
    """Load registered servers from config file."""
    config_file = get_config_file()
    if not config_file.exists():
        defaults = get_default_servers()
        save_servers(defaults)
        return defaults
    data = _read_document(config_file)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("servers"), list):
        return data["servers"]
    if data is None and not is_compatible(_read_raw(config_file)):
        # Another version's file: there is nothing of ours in it.
        return []
    return get_default_servers()


def _read_raw(path: Path) -> Any:
    try:
        with open(path, encoding="utf-8") as stream:
            return json.load(stream)
    except (json.JSONDecodeError, OSError):
        return None


def save_servers(servers: list[dict[str, Any]]) -> None:
    """Save servers to config file, in the versioned format."""
    config_file = get_config_file()
    guard_write(config_file)
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump({"version": CONFIG_VERSION, "servers": servers}, f, indent=2)


def add_server(
    url: str,
    name: str | None = None,
    description: str | None = None,
    avatar: str | None = None,
    author_identities: dict[str, list[str]] | None = None,
    protocol_docs: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Register a server, or bring the entry of the same name to its address.

    The address identifies a server that is reachable; the name identifies
    one the launcher starts, which comes up at a new tunnel port each time:
    an entry of the same name moves to the new address instead of a second
    entry appearing next to it.
    """
    servers = load_servers()
    clean_url = url.strip().rstrip("/")
    if not clean_url.startswith(("http://", "https://")):
        clean_url = f"http://{clean_url}"

    # Check if URL already exists
    for s in servers:
        if s.get("url", "").rstrip("/") == clean_url:
            return s

    clean_name = name.strip() if name else ""
    for s in servers:
        if clean_name and s.get("name") == clean_name:
            s["url"] = clean_url
            if description:
                s["description"] = description.strip()
            save_servers(servers)
            return s

    new_server = {
        "id": f"srv-{uuid.uuid4().hex[:8]}",
        "name": name.strip() if name else generate_docker_name(),
        "url": clean_url,
        "description": description.strip() if description else f"Server at {clean_url}",
        "avatar": avatar or "quantum-ring",
        "is_default": len(servers) == 0,
        "created_at": "now",
        "author_identities": author_identities or {},
        "protocol_docs": protocol_docs or {},
    }
    servers.append(new_server)
    save_servers(servers)
    return new_server


def update_server(server_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update a registered server."""
    servers = load_servers()
    for s in servers:
        if s["id"] == server_id:
            for k in [
                "name",
                "url",
                "description",
                "avatar",
                "is_default",
                "author_identities",
                "protocol_docs",
            ]:
                if k in updates and updates[k] is not None:
                    if k == "url":
                        clean_url = str(updates[k]).strip().rstrip("/")
                        if not clean_url.startswith(("http://", "https://")):
                            clean_url = f"http://{clean_url}"
                        s[k] = clean_url
                    else:
                        s[k] = updates[k]
            save_servers(servers)
            return s
    return None


def resolve_author_identity(
    raw_author: str | None,
    author_identities: dict[str, list[str]] | None = None,
) -> str:
    """Resolve an author alias to its canonical identity."""
    if not raw_author:
        return "Unknown"
    if not author_identities:
        return raw_author
    clean = raw_author.strip()
    clean_lower = clean.lower()
    for canonical, aliases in author_identities.items():
        if clean_lower == canonical.strip().lower():
            return canonical
        if any(clean_lower == a.strip().lower() for a in aliases if a):
            return canonical
    return clean


def delete_server(server_id: str) -> bool:
    """Delete a registered server."""
    servers = load_servers()
    initial_len = len(servers)
    servers = [s for s in servers if s["id"] != server_id]
    if len(servers) < initial_len:
        save_servers(servers)
        return True
    return False
