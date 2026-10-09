"""Unit and integration tests for user roles, authentication, and permissions (Issue #4)."""

import io
import json
from pathlib import Path
from urllib.parse import quote
import zipfile
import pytest
from fastapi.testclient import TestClient

from qibocal_report import auth
from qibocal_report.api import app, set_report_root
from qibocal_report.models import UserRole


@pytest.fixture
def auth_env(tmp_path, monkeypatch):
    """Setup isolated auth environment with auth enabled."""
    auth_dir = tmp_path / "auth_config"
    auth_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(auth_dir))
    monkeypatch.setenv("QIBOCAL_AUTH_ENABLED", "1")
    auth.set_auth_enabled(True)

    # Setup sample reports dir
    sample_src = Path(__file__).parent.parent / "sample_data"
    test_reports = tmp_path / "sample_data"
    import shutil

    shutil.copytree(sample_src, test_reports, ignore=shutil.ignore_patterns("*.zip"))
    set_report_root(test_reports, is_original=True)

    yield test_reports

    auth.set_auth_enabled(None)
    monkeypatch.delenv("QIBOCAL_AUTH_ENABLED", raising=False)


@pytest.mark.parametrize("enabled", [True, False])
def test_download_authentication_and_cross_origin_filenames(auth_env, enabled):
    auth.set_auth_enabled(enabled)
    viewer = auth.create_user("download_viewer", "password", UserRole.VIEWER.value)
    token = auth.create_access_token(viewer)
    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "https://report-client.example",
    }
    report_id = "21:47:29_[3]_pi-pulse"
    protocol_id = next((auth_env / report_id / "data").iterdir()).name
    prefix = f"/api/reports/{quote(report_id, safe='')}"

    archive_dir = auth_env / ".archive" / "download-test"
    archive_dir.mkdir(parents=True)
    (archive_dir / "metadata.json").write_text(
        json.dumps({"name": "Calibration \u03b1", "zip_filename": "calibration.zip"}),
        encoding="utf-8",
    )
    with zipfile.ZipFile(archive_dir / "calibration.zip", "w") as archive:
        archive.writestr("meta.json", "{}")

    paths = [
        f"{prefix}/download/full",
        f"{prefix}/download/new-platform",
        f"{prefix}/download/old-platform",
        f"{prefix}/download/data/{quote(protocol_id, safe='')}",
        f"{prefix}/meta.json",
        "/api/archives/download-test/download",
    ]
    with TestClient(app) as client:
        for path in paths:
            anonymous = client.get(path)
            assert anonymous.status_code == (401 if enabled else 200)
            if enabled:
                assert anonymous.json() == {"detail": "Authentication required"}
                assert anonymous.headers["WWW-Authenticate"] == "Bearer"

            response = client.get(path, headers=headers)
            assert response.status_code == 200
            assert response.headers["Access-Control-Expose-Headers"] == "Content-Disposition"
            if path.endswith("/meta.json"):
                assert response.headers["Content-Type"] == "application/json"
                assert response.headers["Content-Disposition"] == "inline"
                assert "platform" in response.json()
            else:
                assert response.headers["Content-Type"] == "application/zip"
                assert "attachment;" in response.headers["Content-Disposition"]
                with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                    assert archive.namelist()
                    assert archive.testzip() is None
                if path == "/api/archives/download-test/download":
                    assert "filename*=utf-8''Calibration%20%CE%B1.zip" in response.headers[
                        "Content-Disposition"
                    ]
                else:
                    assert 'filename="21-47-29_' in response.headers["Content-Disposition"]

        preflight = client.options(
            f"{prefix}/download/full",
            headers={
                "Origin": headers["Origin"],
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert preflight.status_code == 200
        assert "authorization" in preflight.headers["Access-Control-Allow-Headers"].lower()


def test_password_hashing():
    pw = "supersecret123"
    hashed = auth.hash_password(pw)
    assert hashed != pw
    assert auth.verify_password(pw, hashed) is True
    assert auth.verify_password("wrongpassword", hashed) is False
    assert auth.verify_password("", hashed) is False
    assert auth.verify_password(pw, "invalid$format$") is False


@pytest.mark.parametrize(
    ("enabled", "role", "absolute"),
    [
        (False, None, True),
        (True, "admin", True),
        (True, "editor", False),
        (True, "viewer", False),
    ],
)
def test_report_upload_path_visibility(auth_env, enabled, role, absolute):
    auth.set_auth_enabled(enabled)
    report_id = "21:47:29_[3]_pi-pulse"
    nested = auth_env / "nested folder"
    nested.mkdir()
    (auth_env / report_id).rename(nested / report_id)
    headers = {}
    if role:
        user = auth.create_user(f"path_{role}", "password", role)
        headers["Authorization"] = f"Bearer {auth.create_access_token(user)}"
    client = TestClient(app)

    for root, relative in [
        (auth_env, f"nested folder/{report_id}"),
        (nested, report_id),
    ]:
        set_report_root(root)
        response = client.get(
            f"/api/reports/{quote(relative, safe='')}/path", headers=headers
        )
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json() == {
            "path": str(nested / report_id) if absolute else relative,
            "is_absolute": absolute,
        }


def test_report_upload_path_requires_auth_and_current_role(auth_env):
    client = TestClient(app)
    report_id = "21:47:29_[3]_pi-pulse"
    url = f"/api/reports/{quote(report_id, safe='')}/path"
    for headers in [{}, {"Authorization": "Bearer invalid"}]:
        response = client.get(url, headers=headers)
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"

    auth.create_user("remaining_admin", "password", "admin")
    user = auth.create_user("path_admin", "password", "admin")
    headers = {"Authorization": f"Bearer {auth.create_access_token(user)}"}
    assert client.get(url, headers=headers).json()["is_absolute"] is True
    auth.update_user_role(user["id"], "viewer")
    assert client.get(url, headers=headers).json() == {
        "path": report_id,
        "is_absolute": False,
    }


def test_report_upload_path_rejects_missing_and_outside_reports(auth_env, tmp_path):
    auth.set_auth_enabled(False)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "meta.json").write_text("{}", encoding="utf-8")
    (auth_env / "external-link").symlink_to(outside, target_is_directory=True)
    client = TestClient(app)
    for report_id in [
        "missing",
        "../outside",
        str(outside),
        "external-link",
    ]:
        response = client.get(f"/api/reports/{quote(report_id, safe='')}/path")
        assert response.status_code == 404
        assert response.json() == {"detail": "Report not found"}


def test_auth_data_crud(auth_env):
    # Initial state
    users = auth.list_users()
    assert len(users) == 0

    # Initial admin invite
    token = auth.create_initial_admin_invite_if_needed()
    assert token is not None
    inv = auth.get_invite(token)
    assert inv["role"] == UserRole.ADMIN.value

    # Register admin
    admin = auth.create_user("alice_admin", "password123", UserRole.ADMIN.value)
    assert admin["username"] == "alice_admin"
    assert admin["role"] == UserRole.ADMIN.value

    # Duplicate username check
    with pytest.raises(ValueError, match="already taken"):
        auth.create_user("alice_admin", "anotherpass", UserRole.VIEWER.value)

    # Cannot delete or demote only admin
    with pytest.raises(ValueError, match="only remaining administrator"):
        auth.delete_user(admin["id"])

    with pytest.raises(ValueError, match="only remaining administrator"):
        auth.update_user_role(admin["id"], UserRole.VIEWER.value)

    # Register second admin
    admin2 = auth.create_user("bob_admin", "password123", UserRole.ADMIN.value)
    # Now demoting one is allowed
    demoted = auth.update_user_role(admin2["id"], UserRole.EDITOR.value)
    assert demoted["role"] == UserRole.EDITOR.value


def test_invitation_tokens(auth_env):
    # Create invite
    inv = auth.create_invite(
        role=UserRole.VIEWER.value, expires_in_hours=1, max_uses=1, created_by="test"
    )
    valid, reason, obj = auth.validate_invite(inv["token"])
    assert valid is True
    assert obj["role"] == UserRole.VIEWER.value

    # Use invite
    used = auth.use_invite(inv["token"])
    assert used["used_count"] == 1

    # Single-use invite is removed/invalid after use
    valid_after, reason_after, _ = auth.validate_invite(inv["token"])
    assert valid_after is False

    # Multi-use invite
    multi_inv = auth.create_invite(
        role=UserRole.EDITOR.value, expires_in_hours=None, max_uses=2
    )
    auth.use_invite(multi_inv["token"])
    valid, _, _ = auth.validate_invite(multi_inv["token"])
    assert valid is True
    auth.use_invite(multi_inv["token"])
    valid, _, _ = auth.validate_invite(multi_inv["token"])
    assert valid is False


def test_api_auth_flow(auth_env):
    client = TestClient(app)

    # 1. Check status
    res = client.get("/api/auth/status")
    assert res.status_code == 200
    assert res.json()["auth_enabled"] is True

    # 2. Unauthenticated request to reports should fail with 401
    res = client.get("/api/reports")
    assert res.status_code == 401

    # 3. Initial admin invite
    invite_token = auth.create_initial_admin_invite_if_needed()
    res = client.get(f"/api/auth/invite/{invite_token}")
    assert res.status_code == 200
    assert res.json()["valid"] is True
    assert res.json()["role"] == "admin"

    # 4. Register admin
    res = client.post(
        "/api/auth/register",
        json={
            "invite_token": invite_token,
            "username": "superadmin",
            "password": "adminpassword",
        },
    )
    assert res.status_code == 200
    admin_data = res.json()
    admin_token = admin_data["access_token"]
    assert admin_data["user"]["role"] == "admin"

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 5. Admin creates an invite for Editor and Viewer
    res = client.post(
        "/api/admin/invites",
        json={"role": "viewer", "expires_in_hours": 24, "max_uses": 1},
        headers=admin_headers,
    )
    assert res.status_code == 200
    viewer_invite = res.json()["token"]

    res = client.post(
        "/api/admin/invites",
        json={"role": "editor", "expires_in_hours": 24, "max_uses": 1},
        headers=admin_headers,
    )
    assert res.status_code == 200
    editor_invite = res.json()["token"]

    # 6. Register Viewer and Editor
    res = client.post(
        "/api/auth/register",
        json={
            "invite_token": viewer_invite,
            "username": "viewer_user",
            "password": "viewerpass",
        },
    )
    assert res.status_code == 200
    viewer_token = res.json()["access_token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    res = client.post(
        "/api/auth/register",
        json={
            "invite_token": editor_invite,
            "username": "editor_user",
            "password": "editorpass",
        },
    )
    assert res.status_code == 200
    editor_token = res.json()["access_token"]
    editor_headers = {"Authorization": f"Bearer {editor_token}"}

    # 7. Check /api/auth/me
    res = client.get("/api/auth/me", headers=viewer_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "viewer"

    # 8. Test Viewer permissions:
    # Read is allowed
    res = client.get("/api/reports", headers=viewer_headers)
    assert res.status_code == 200
    reports = res.json()
    assert len(reports) > 0
    test_report_id = reports[0]["id"]

    res = client.get("/api/reports/stats", headers=viewer_headers)
    assert res.status_code == 200

    res = client.get("/api/server/directory", headers=viewer_headers)
    assert res.status_code == 200

    # Modifications are FORBIDDEN for Viewer (403)
    res = client.post(
        "/api/reports/bulk-action",
        json={"action": "label", "report_ids": [test_report_id], "label": "test"},
        headers=viewer_headers,
    )
    assert res.status_code == 403

    res = client.put(
        f"/api/reports/{test_report_id}/author",
        json={"author": "New Author"},
        headers=viewer_headers,
    )
    assert res.status_code == 403

    res = client.delete(f"/api/reports/{test_report_id}", headers=viewer_headers)
    assert res.status_code == 403

    res = client.post(
        f"/api/reports/{test_report_id}/regenerate",
        headers=viewer_headers,
    )
    assert res.status_code == 403

    res = client.post(
        "/api/server/directory",
        json={"path": ""},
        headers=viewer_headers,
    )
    assert res.status_code == 403

    res = client.get("/api/admin/users", headers=viewer_headers)
    assert res.status_code == 403

    # 9. Test Editor permissions:
    # Editor can perform modifications
    res = client.post(
        "/api/reports/bulk-action",
        json={"action": "label", "report_ids": [test_report_id], "label": "editor_tag"},
        headers=editor_headers,
    )
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Editor CANNOT access admin endpoints
    res = client.get("/api/admin/users", headers=editor_headers)
    assert res.status_code == 403

    res = client.post(
        "/api/admin/invites",
        json={"role": "viewer"},
        headers=editor_headers,
    )
    assert res.status_code == 403

    # 10. Test Admin permissions:
    res = client.get("/api/admin/users", headers=admin_headers)
    assert res.status_code == 200
    user_list = res.json()
    assert len(user_list) == 3

    # Admin promotes viewer to editor
    viewer_user_id = [u["id"] for u in user_list if u["username"] == "viewer_user"][0]
    res = client.put(
        f"/api/admin/users/{viewer_user_id}/role",
        json={"role": "editor"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["role"] == "editor"

    # Admin gets config overview
    res = client.get("/api/admin/config", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["users_count"] == 3

    # Revoke an active invite
    inv_to_revoke = client.post(
        "/api/admin/invites",
        json={"role": "viewer"},
        headers=admin_headers,
    ).json()["token"]
    res = client.delete(f"/api/admin/invites/{inv_to_revoke}", headers=admin_headers)
    assert res.status_code in (200, 204)

    # Delete user
    res = client.delete(f"/api/admin/users/{viewer_user_id}", headers=admin_headers)
    assert res.status_code in (200, 204)
    res = client.get("/api/admin/users", headers=admin_headers)
    assert len(res.json()) == 2


def test_archive_permissions(auth_env):
    """Test that Viewers cannot create/restore/delete archives, but Editors can."""
    client = TestClient(app)

    # Initial admin
    token = auth.create_initial_admin_invite_if_needed()
    res = client.post(
        "/api/auth/register",
        json={"invite_token": token, "username": "admin_u", "password": "password"},
    )
    admin_token = res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create Editor and Viewer invites
    v_inv = client.post(
        "/api/admin/invites",
        json={"role": "viewer"},
        headers=admin_headers,
    ).json()["token"]
    e_inv = client.post(
        "/api/admin/invites",
        json={"role": "editor"},
        headers=admin_headers,
    ).json()["token"]

    viewer_token = client.post(
        "/api/auth/register",
        json={"invite_token": v_inv, "username": "view_u", "password": "password"},
    ).json()["access_token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    editor_token = client.post(
        "/api/auth/register",
        json={"invite_token": e_inv, "username": "edit_u", "password": "password"},
    ).json()["access_token"]
    editor_headers = {"Authorization": f"Bearer {editor_token}"}

    # Viewer can read archives list and reports
    res = client.get("/api/reports", headers=viewer_headers)
    assert res.status_code == 200
    reports = res.json()
    assert len(reports) > 0
    test_id = reports[0]["id"]

    res = client.get("/api/archives", headers=viewer_headers)
    assert res.status_code == 200

    # Viewer CANNOT create archive (403)
    res = client.post(
        "/api/archives",
        json={"name": "test_archive", "report_ids": [test_id]},
        headers=viewer_headers,
    )
    assert res.status_code == 403

    # Editor CAN create archive
    res = client.post(
        "/api/archives",
        json={"name": "test_archive", "report_ids": [test_id]},
        headers=editor_headers,
    )
    assert res.status_code == 200
    arc_id = res.json()["id"]

    # Viewer CANNOT restore or delete archive (403)
    res = client.post(f"/api/archives/{arc_id}/restore", headers=viewer_headers)
    assert res.status_code == 403

    res = client.delete(f"/api/archives/{arc_id}", headers=viewer_headers)
    assert res.status_code == 403

    # Editor CAN delete archive
    res = client.delete(f"/api/archives/{arc_id}", headers=editor_headers)
    assert res.status_code == 200


def test_auth_disabled_backward_compatibility(tmp_path, monkeypatch):
    """When auth is disabled (default), all endpoints are accessible without token."""
    monkeypatch.delenv("QIBOCAL_AUTH_ENABLED", raising=False)
    auth.set_auth_enabled(False)

    sample_src = Path(__file__).parent.parent / "sample_data"
    test_reports = tmp_path / "sample_data_noauth"
    import shutil

    shutil.copytree(sample_src, test_reports, ignore=shutil.ignore_patterns("*.zip"))
    set_report_root(test_reports, is_original=True)

    client = TestClient(app)

    # Status check
    res = client.get("/api/auth/status")
    assert res.status_code == 200
    assert res.json()["auth_enabled"] is False

    # Unauthenticated read succeeds
    res = client.get("/api/reports")
    assert res.status_code == 200
    reports = res.json()
    assert len(reports) > 0
    test_id = reports[0]["id"]

    # Unauthenticated modification succeeds without error
    res = client.put(f"/api/reports/{test_id}/author", json={"author": "Open Author"})
    assert res.status_code == 200


def test_unauthenticated_restrictions_and_public_docs(auth_env):
    """Verify that unauthenticated users can access documentation but cannot access internal pages/servers."""
    client = TestClient(app)

    # 1. Documentation must be completely public without authentication
    res_nav = client.get("/api/docs-nav")
    assert res_nav.status_code == 200
    nav_sections = [item["section"] for item in res_nav.json()]
    assert "Overview" in nav_sections
    assert "Admin Guide" in nav_sections

    # Admin guide docs must be accessible
    res_admin_idx = client.get("/api/docs-content/admin-guide/index")
    assert res_admin_idx.status_code == 200
    assert "Server Administration" in res_admin_idx.text

    res_roles = client.get("/api/docs-content/admin-guide/roles")
    assert res_roles.status_code == 200
    assert "Viewer" in res_roles.text
    assert "Editor" in res_roles.text
    assert "Admin" in res_roles.text

    res_invites = client.get("/api/docs-content/admin-guide/invitations")
    assert res_invites.status_code == 200
    assert "Invitation" in res_invites.text

    # 2. Server list returns empty when unauthenticated on auth-enabled instance
    res_srv = client.get("/api/servers")
    assert res_srv.status_code == 200
    assert res_srv.json() == []

    # 3. Health check hides internal path details and reports count
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["reports_count"] == 0
    assert health_data["root_dir"] == ""

    # 4. Internal endpoints return 401 Unauthorized
    assert client.get("/api/reports").status_code == 401
    assert client.get("/api/archives").status_code == 401
    assert client.get("/api/reports/stats").status_code == 401
    assert client.get("/api/admin/users").status_code == 401
    assert client.get("/api/admin/invites").status_code == 401

    # 5. Once registered, authenticated user can access internal endpoints
    admin_token = auth.create_initial_admin_invite_if_needed()
    reg_res = client.post(
        "/api/auth/register",
        json={"invite_token": admin_token, "username": "valid_user", "password": "securepassword"},
    )
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Authenticated user sees servers
    res_srv_auth = client.get("/api/servers", headers=headers)
    assert res_srv_auth.status_code == 200
    assert len(res_srv_auth.json()) > 0

    # Authenticated user sees reports count in health
    res_health_auth = client.get("/api/health", headers=headers)
    assert res_health_auth.status_code == 200
    assert res_health_auth.json()["reports_count"] > 0

    # Authenticated user can access reports
    res_reports = client.get("/api/reports", headers=headers)
    assert res_reports.status_code == 200


def test_regenerate_admin_invite_and_reclaim(auth_env):
    client = TestClient(app)

    # Initially no users: regenerate_admin_invite without username generates initial invite
    initial_inv = auth.regenerate_admin_invite()
    assert initial_inv["role"] == UserRole.ADMIN.value
    assert initial_inv["target_username"] is None

    # Register admin
    res = client.post(
        "/api/auth/register",
        json={
            "invite_token": initial_inv["token"],
            "username": "lab_admin",
            "password": "initial_password",
        },
    )
    assert res.status_code == 200

    # Also register a viewer
    viewer_inv = auth.create_invite(role="viewer")
    res_viewer = client.post(
        "/api/auth/register",
        json={
            "invite_token": viewer_inv["token"],
            "username": "viewer_user",
            "password": "viewer_password",
        },
    )
    assert res_viewer.status_code == 200

    # Test list_admins
    admins = auth.list_admins()
    assert len(admins) == 1
    assert admins[0]["username"] == "lab_admin"

    # Regenerate invite for non-existent admin should raise ValueError
    with pytest.raises(ValueError, match="not found"):
        auth.regenerate_admin_invite("nonexistent")

    # Regenerate invite for non-admin user should raise ValueError
    with pytest.raises(ValueError, match="not an administrator"):
        auth.regenerate_admin_invite("viewer_user")

    # Regenerate invite for lab_admin
    regen_inv = auth.regenerate_admin_invite("lab_admin", expires_in_hours=24)
    assert regen_inv["role"] == "admin"
    assert regen_inv["target_username"] == "lab_admin"
    token = regen_inv["token"]

    # Validating invite via API should expose target_username
    res_check = client.get(f"/api/auth/invite/{token}")
    assert res_check.status_code == 200
    check_data = res_check.json()
    assert check_data["valid"] is True
    assert check_data["role"] == "admin"
    assert check_data["target_username"] == "lab_admin"

    # Trying to claim with mismatched username should fail
    res_wrong = client.post(
        "/api/auth/register",
        json={
            "invite_token": token,
            "username": "different_user",
            "password": "new_password_123",
        },
    )
    assert res_wrong.status_code == 400
    assert "reserved for 'lab_admin'" in res_wrong.json()["detail"]

    # Reclaim access with matching username and new password
    res_reclaim = client.post(
        "/api/auth/register",
        json={
            "invite_token": token,
            "username": "lab_admin",
            "password": "new_password_123",
        },
    )
    assert res_reclaim.status_code == 200
    reclaim_data = res_reclaim.json()
    assert reclaim_data["user"]["username"] == "lab_admin"
    assert reclaim_data["user"]["role"] == "admin"
    assert "access_token" in reclaim_data

    # Token should be consumed now
    res_check_after = client.get(f"/api/auth/invite/{token}")
    assert res_check_after.json()["valid"] is False

    # Sign in with new password works
    res_login = client.post(
        "/api/auth/login",
        json={"username": "lab_admin", "password": "new_password_123"},
    )
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()

    # Old password no longer works
    res_old_login = client.post(
        "/api/auth/login",
        json={"username": "lab_admin", "password": "initial_password"},
    )
    assert res_old_login.status_code == 401


def test_password_reset_endpoint(auth_env):
    """Test that password reset tokens can be validated and show the target username."""
    client = TestClient(app)

    # Create a user first
    auth.create_user("alice", "password123", UserRole.ADMIN.value)

    # Create a password reset token for the user
    user = auth.get_user_by_username("alice")
    reset = auth.create_password_reset(user["id"], created_by="admin")
    reset_token = reset["token"]

    # Validate the password reset token via the new endpoint
    res = client.get(f"/api/auth/password-reset/{reset_token}")
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["target_username"] == "alice"
    assert data["role"] == "admin"
    assert data["token"] == reset_token
    assert data["expires_at"] is not None

    # Invalid token should return invalid response
    res_invalid = client.get("/api/auth/password-reset/invalid-token")
    assert res_invalid.status_code == 200
    data_invalid = res_invalid.json()
    assert data_invalid["valid"] is False
    assert "not found or has expired" in data_invalid["detail"]

    # Register endpoint should work with password reset token
    # (same as invite tokens with target_username)
    res_register = client.post(
        "/api/auth/register",
        json={
            "invite_token": reset_token,
            "username": "alice",
            "password": "newpassword123",
        },
    )
    assert res_register.status_code == 200
    register_data = res_register.json()
    assert register_data["user"]["username"] == "alice"
    assert "access_token" in register_data

    # Password should be updated
    res_login = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "newpassword123"},
    )
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()

    # Old password should not work
    res_old_login = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "password123"},
    )
    assert res_old_login.status_code == 401
