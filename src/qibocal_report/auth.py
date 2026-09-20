"""Authentication, user roles, and invitation token management for qibocal-report."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import uuid

import jwt

from qibocal_report import config
from qibocal_report.models import UserRole

_AUTH_ENABLED: bool | None = None


def is_auth_enabled() -> bool:
    """Check whether authentication and role enforcement is active."""
    global _AUTH_ENABLED
    if _AUTH_ENABLED is not None:
        return _AUTH_ENABLED
    env_val = os.environ.get("QIBOCAL_AUTH_ENABLED", "").strip().lower()
    return env_val in ("1", "true", "yes", "on", "enable", "enabled")


def set_auth_enabled(val: bool | None) -> None:
    """Manually override authentication activation."""
    global _AUTH_ENABLED
    _AUTH_ENABLED = val


def get_auth_file() -> Path:
    """Return path to auth.json file."""
    custom = os.environ.get("QIBOCAL_AUTH_FILE")
    if custom:
        p = Path(custom)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    return config.get_config_dir() / "auth.json"


def load_auth_data() -> dict:
    """Load users and invitations from auth file."""
    fpath = get_auth_file()
    if not fpath.exists():
        initial = {
            "secret_key": secrets.token_hex(32),
            "users": [],
            "invites": [],
        }
        save_auth_data(initial)
        return initial
    try:
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("users", [])
                data.setdefault("invites", [])
                if not data.get("secret_key"):
                    data["secret_key"] = secrets.token_hex(32)
                    save_auth_data(data)
                return data
    except (json.JSONDecodeError, OSError):
        pass
    fallback = {
        "secret_key": secrets.token_hex(32),
        "users": [],
        "invites": [],
    }
    return fallback


def save_auth_data(data: dict) -> None:
    """Persist users and invitations to auth file."""
    fpath = get_auth_file()
    fpath.parent.mkdir(parents=True, exist_ok=True)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# --- Password Hashing & Verification ---
def hash_password(password: str) -> str:
    """Hash password with PBKDF2-HMAC-SHA256 and unique random salt."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    )
    return f"{salt}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored salt and PBKDF2 hash."""
    if not hashed or "$" not in hashed:
        return False
    salt, key_hex = hashed.split("$", 1)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    )
    return secrets.compare_digest(dk.hex(), key_hex)


# --- JWT Access Tokens ---
def get_jwt_secret() -> str:
    """Get secret key for signing JWTs."""
    data = load_auth_data()
    return data.get("secret_key") or "insecure-default-key"


def create_access_token(user: dict, expires_delta: timedelta | None = None) -> str:
    """Generate a signed JWT for the specified user."""
    secret = get_jwt_secret()
    now = datetime.now(timezone.utc)
    exp = now + (expires_delta or timedelta(days=7))
    payload = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token."""
    try:
        secret = get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None


# --- User Management ---
def list_users() -> list[dict]:
    """List all registered users without sensitive password hashes."""
    data = load_auth_data()
    result = []
    for u in data.get("users", []):
        result.append(
            {
                "id": u["id"],
                "username": u["username"],
                "role": u["role"],
                "created_at": u.get("created_at", ""),
            }
        )
    return result


def get_user_by_id(user_id: str) -> dict | None:
    """Get user by unique ID."""
    data = load_auth_data()
    for u in data.get("users", []):
        if u["id"] == user_id:
            return u
    return None


def get_user_by_username(username: str) -> dict | None:
    """Get user by username (case-insensitive lookup)."""
    data = load_auth_data()
    clean = username.strip().lower()
    for u in data.get("users", []):
        if u["username"].strip().lower() == clean:
            return u
    return None


def create_user(username: str, password: str, role: str) -> dict:
    """Create and persist a new user."""
    clean_username = username.strip()
    if not clean_username:
        raise ValueError("Username cannot be empty")
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters long")

    valid_roles = {UserRole.VIEWER.value, UserRole.EDITOR.value, UserRole.ADMIN.value}
    norm_role = role.strip().lower()
    if norm_role not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. Must be one of {valid_roles}")

    data = load_auth_data()
    for u in data.get("users", []):
        if u["username"].strip().lower() == clean_username.lower():
            raise ValueError(f"Username '{clean_username}' is already taken")

    new_user = {
        "id": f"usr-{uuid.uuid4().hex[:10]}",
        "username": clean_username,
        "password_hash": hash_password(password),
        "role": norm_role,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    data.setdefault("users", []).append(new_user)
    save_auth_data(data)
    return {
        "id": new_user["id"],
        "username": new_user["username"],
        "role": new_user["role"],
        "created_at": new_user["created_at"],
    }


def update_user_role(user_id: str, new_role: str) -> dict:
    """Update role for an existing user."""
    valid_roles = {UserRole.VIEWER.value, UserRole.EDITOR.value, UserRole.ADMIN.value}
    norm_role = new_role.strip().lower()
    if norm_role not in valid_roles:
        raise ValueError(f"Invalid role '{new_role}'. Must be one of {valid_roles}")

    data = load_auth_data()
    users = data.get("users", [])
    target = None
    for u in users:
        if u["id"] == user_id:
            target = u
            break

    if not target:
        raise ValueError("User not found")

    # Prevent demoting the only admin
    if target["role"] == UserRole.ADMIN.value and norm_role != UserRole.ADMIN.value:
        admin_count = sum(1 for u in users if u["role"] == UserRole.ADMIN.value)
        if admin_count <= 1:
            raise ValueError("Cannot demote the only remaining administrator")

    target["role"] = norm_role
    save_auth_data(data)
    return {
        "id": target["id"],
        "username": target["username"],
        "role": target["role"],
        "created_at": target.get("created_at", ""),
    }


def delete_user(user_id: str) -> bool:
    """Delete a user account."""
    data = load_auth_data()
    users = data.get("users", [])
    target = None
    for u in users:
        if u["id"] == user_id:
            target = u
            break

    if not target:
        return False

    # Prevent deleting the only admin
    if target["role"] == UserRole.ADMIN.value:
        admin_count = sum(1 for u in users if u["role"] == UserRole.ADMIN.value)
        if admin_count <= 1:
            raise ValueError("Cannot delete the only remaining administrator")

    data["users"] = [u for u in users if u["id"] != user_id]
    save_auth_data(data)
    return True


def authenticate_user(username: str, password: str) -> dict | None:
    """Verify username and password, returning user dict if valid."""
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": user.get("created_at", ""),
    }


# --- Invitation Management ---
def list_invites() -> list[dict]:
    """List all pending/valid invitation tokens."""
    data = load_auth_data()
    now = datetime.now(timezone.utc)
    valid_invites = []
    for inv in data.get("invites", []):
        if inv.get("expires_at"):
            try:
                exp = datetime.fromisoformat(inv["expires_at"])
                if now > exp:
                    continue
            except (ValueError, TypeError):
                pass
        valid_invites.append(inv)
    return valid_invites


def get_invite(token: str) -> dict | None:
    """Find invite by token."""
    data = load_auth_data()
    for inv in data.get("invites", []):
        if inv["token"] == token:
            return inv
    return None


def validate_invite(token: str) -> tuple[bool, str, dict | None]:
    """Check if invite token exists and has not expired or exceeded max uses."""
    clean_token = token.strip()
    if not clean_token:
        return False, "Token is empty", None

    inv = get_invite(clean_token)
    if not inv:
        return False, "Invitation token not found", None

    if inv.get("expires_at"):
        try:
            exp = datetime.fromisoformat(inv["expires_at"])
            if datetime.now(timezone.utc) > exp:
                return False, "Invitation token has expired", None
        except (ValueError, TypeError):
            pass

    max_uses = inv.get("max_uses")
    used = inv.get("used_count", 0)
    if max_uses is not None and used >= max_uses:
        return False, "Invitation token has already been fully used", None

    return True, "Valid", inv


def create_invite(
    role: str = "viewer",
    expires_in_hours: int | None = 168,
    max_uses: int | None = None,
    created_by: str = "admin",
) -> dict:
    """Generate a new invitation token."""
    valid_roles = {UserRole.VIEWER.value, UserRole.EDITOR.value, UserRole.ADMIN.value}
    norm_role = role.strip().lower()
    if norm_role not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. Must be one of {valid_roles}")

    token = secrets.token_urlsafe(24)
    now = datetime.now(timezone.utc)
    expires_at = (
        (now + timedelta(hours=expires_in_hours)).isoformat()
        if expires_in_hours is not None
        else None
    )

    invite = {
        "token": token,
        "role": norm_role,
        "expires_at": expires_at,
        "created_at": now.isoformat(),
        "created_by": created_by,
        "used_count": 0,
        "max_uses": max_uses,
    }

    data = load_auth_data()
    data.setdefault("invites", []).append(invite)
    save_auth_data(data)
    return invite


def use_invite(token: str) -> dict | None:
    """Record usage of an invitation token."""
    data = load_auth_data()
    invites = data.get("invites", [])
    target = None
    for inv in invites:
        if inv["token"] == token:
            target = inv
            break

    if not target:
        return None

    target["used_count"] = target.get("used_count", 0) + 1
    # If single-use or reached max uses, remove it
    max_uses = target.get("max_uses")
    if max_uses is not None and target["used_count"] >= max_uses:
        data["invites"] = [i for i in invites if i["token"] != token]

    save_auth_data(data)
    return target


def delete_invite(token: str) -> bool:
    """Revoke/delete an invitation token."""
    data = load_auth_data()
    invites = data.get("invites", [])
    initial_len = len(invites)
    data["invites"] = [i for i in invites if i["token"] != token]
    if len(data["invites"]) < initial_len:
        save_auth_data(data)
        return True
    return False


def create_initial_admin_invite_if_needed() -> str | None:
    """If auth is enabled and no users exist, ensure an initial admin invite is present."""
    data = load_auth_data()
    if data.get("users"):
        return None

    # Check for existing valid admin invite
    for inv in data.get("invites", []):
        if inv.get("role") == UserRole.ADMIN.value:
            valid, _, _ = validate_invite(inv["token"])
            if valid:
                return inv["token"]

    # Generate an initial admin invite with 30 days or unlimited expiration
    invite = create_invite(
        role=UserRole.ADMIN.value,
        expires_in_hours=720,  # 30 days
        max_uses=1,
        created_by="system",
    )
    return invite["token"]
