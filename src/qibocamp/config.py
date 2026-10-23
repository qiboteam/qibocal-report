"""Server and configuration management for qibocamp."""

import json
import os
import random
import tempfile
import uuid
from datetime import datetime, timezone
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
    custom_dir = os.environ.get("QIBOCAMP_CONFIG_DIR")
    if custom_dir:
        path = Path(custom_dir)
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        path = root / "qibocamp"
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir(*, create: bool = True) -> Path:
    """Return the data directory, optionally creating it.

    Configuration describes servers; data is what they serve. The two follow
    the matching XDG conventions: ``$XDG_CONFIG_HOME`` for the first,
    ``$XDG_DATA_HOME`` (``~/.local/share``) for the second.
    """
    custom_dir = os.environ.get("QIBOCAMP_DATA_DIR")
    if custom_dir:
        path = Path(custom_dir)
    else:
        root = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
        path = root / "qibocamp"
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


# The format of the configuration files this version reads and writes.
#
# Every file is an object carrying a ``version``: ``servers.json`` keeps its
# entries under ``servers``, ``notebooks.json`` under ``connections``,
# ``auth.json`` and the launcher's preferences next to the version itself. A
# file without a version, or with another one, is not ours: it is ignored —
# read as empty, never overwritten — so that an application of one version
# does not destroy what another wrote; the launcher lists such files for a
# migration by hand. There is no automatic migration, on purpose.
CONFIG_VERSION = 1


class IncompatibleConfig(OSError):
    """A configuration file of another version, which must not be replaced."""

    def __init__(self, path: Path, found: int | None):
        declared = f"format {found}" if found is not None else "no format version"
        super().__init__(
            f"'{path}' was written by another version of qibocamp "
            f"({declared}; this one reads {CONFIG_VERSION}). "
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
    """Whether a document is of this version."""
    return declared_version(data) == CONFIG_VERSION


def _read_document(path: Path) -> Any:
    """The parsed file, ``None`` when absent, unreadable or of another version."""
    try:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
    except (json.JSONDecodeError, OSError):
        return None
    return data if is_compatible(data) else None


def guard_write(path: Path) -> None:
    """Refuse to replace a file of another version, or of none."""
    try:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
    except (json.JSONDecodeError, OSError):
        return
    if not is_compatible(data):
        raise IncompatibleConfig(path, declared_version(data))


def write_document(path: Path, document: Any, *, private: bool = False) -> None:
    """Replace a configuration file in one step, never leaving it half written.

    `private` keeps it to its owner — 0600, in a folder made 0700 — for the
    signing keys of `auth.json`.
    """
    path.parent.mkdir(mode=0o700 if private else 0o777, parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        if private:
            os.chmod(temporary, 0o600)
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(document, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def load_servers() -> list[dict[str, Any]]:
    """The registered servers; none when there is no file of ours."""
    data = _read_document(get_config_file())
    if isinstance(data, dict) and isinstance(data.get("servers"), list):
        return data["servers"]
    return []


def save_servers(servers: list[dict[str, Any]]) -> None:
    """Save servers to config file, in the versioned format."""
    config_file = get_config_file()
    guard_write(config_file)
    write_document(config_file, {"version": CONFIG_VERSION, "servers": servers})


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
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
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


# --- The dashboard, which no server serves itself ---------------------------
# The server is headless: the dashboard that reads it is the one deployed from
# the frontend package, or the one the desktop launcher embeds. A link that
# needs a page — an invitation — points at the deployed one, which takes the
# server to address in its query.
DASHBOARD_URL = os.environ.get(
    "QIBOCAMP_DASHBOARD_URL", "https://qibo.science/qibocamp"
).rstrip("/")


def allowed_origins() -> list[str]:
    """The pages that may call a server from a browser, besides this machine's.

    The deployed dashboard and the desktop launcher's, plus any listed,
    comma-separated, in `QIBOCAMP_ALLOWED_ORIGINS` — another deployment of the
    dashboard, say. Any other page is refused: on a server without
    authentication every caller is an administrator, so an arbitrary site
    open in the same browser must not be one.
    """
    from urllib.parse import urlsplit

    dashboard = urlsplit(DASHBOARD_URL)
    origins = [
        f"{dashboard.scheme}://{dashboard.netloc}",
        # The launcher's webview: macOS and Linux, then Windows.
        "tauri://localhost",
        "http://tauri.localhost",
        "https://tauri.localhost",
    ]
    extra = os.environ.get("QIBOCAMP_ALLOWED_ORIGINS", "")
    origins += [origin.strip().rstrip("/") for origin in extra.split(",") if origin.strip()]
    return list(dict.fromkeys(origins))


# Pages served from this machine: the development servers of the dashboard and the launcher.
LOCAL_ORIGIN = r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?"


def origin_allowed(origin: str, own: str) -> bool:
    """Whether a page of `origin` may change something on the server at `own`."""
    import re

    origin = origin.rstrip("/")
    return origin == own.rstrip("/") or origin in allowed_origins() or re.fullmatch(LOCAL_ORIGIN, origin) is not None


def invite_link(server_url: str, token: str, dashboard: str | None = None) -> str:
    """The link an invitation is sent as: the dashboard, told the server and the token."""
    from urllib.parse import urlencode

    page = (dashboard or DASHBOARD_URL).rstrip("/")
    query = urlencode({"token": token, "server": server_url.rstrip("/")})
    return f"{page}/#/invite?{query}"
