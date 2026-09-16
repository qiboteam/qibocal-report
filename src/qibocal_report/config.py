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


def get_config_dir() -> Path:
    """Return the configuration directory."""
    custom_dir = os.environ.get("QIBOCAL_REPORT_CONFIG_DIR")
    if custom_dir:
        path = Path(custom_dir)
    else:
        path = Path.home() / ".config" / "qibocal-report"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_file() -> Path:
    """Return path to servers.json."""
    return get_config_dir() / "servers.json"


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


def load_servers() -> list[dict[str, Any]]:
    """Load registered servers from config file."""
    config_file = get_config_file()
    if not config_file.exists():
        defaults = get_default_servers()
        save_servers(defaults)
        return defaults
    try:
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "servers" in data:
                return data["servers"]
    except (json.JSONDecodeError, OSError):
        pass
    return get_default_servers()


def save_servers(servers: list[dict[str, Any]]) -> None:
    """Save servers to config file."""
    config_file = get_config_file()
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(servers, f, indent=2)


def add_server(
    url: str,
    name: str | None = None,
    description: str | None = None,
    avatar: str | None = None,
) -> dict[str, Any]:
    """Register a new server."""
    servers = load_servers()
    clean_url = url.strip().rstrip("/")

    # Check if URL already exists
    for s in servers:
        if s.get("url", "").rstrip("/") == clean_url:
            return s

    new_server = {
        "id": f"srv-{uuid.uuid4().hex[:8]}",
        "name": name.strip() if name else generate_docker_name(),
        "url": clean_url,
        "description": description.strip() if description else f"Server at {clean_url}",
        "avatar": avatar or "quantum-ring",
        "is_default": len(servers) == 0,
        "created_at": "now",
    }
    servers.append(new_server)
    save_servers(servers)
    return new_server


def update_server(server_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update a registered server."""
    servers = load_servers()
    for s in servers:
        if s["id"] == server_id:
            for k in ["name", "url", "description", "avatar", "is_default"]:
                if k in updates and updates[k] is not None:
                    if k == "url":
                        s[k] = updates[k].strip().rstrip("/")
                    else:
                        s[k] = updates[k]
            save_servers(servers)
            return s
    return None


def delete_server(server_id: str) -> bool:
    """Delete a registered server."""
    servers = load_servers()
    initial_len = len(servers)
    servers = [s for s in servers if s["id"] != server_id]
    if len(servers) < initial_len:
        save_servers(servers)
        return True
    return False
