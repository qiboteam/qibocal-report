from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from qibocal_report.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "report" in result.output


def test_report_help():
    runner = CliRunner()
    result = runner.invoke(main, ["report", "--help"])
    assert result.exit_code == 0
    assert "server" in result.output
    assert "client" in result.output
    assert "dev" in result.output
    assert "export" in result.output


def test_dev_command(tmp_path):
    runner = CliRunner()
    sample_dir = tmp_path / "sample"
    sample_dir.mkdir()

    mock_proc = MagicMock()
    mock_proc.poll.return_value = None

    with (
        patch(
            "qibocal_report.cli.subprocess.Popen", return_value=mock_proc
        ) as mock_popen,
        patch("qibocal_report.cli.uvicorn.run") as mock_uvicorn,
    ):
        result = runner.invoke(
            main,
            [
                "report",
                "dev",
                str(sample_dir),
                "--port",
                "8080",
                "--frontend-port",
                "5174",
            ],
        )
        assert result.exit_code == 0
        assert mock_popen.called
        assert mock_uvicorn.called
        assert "log_config" in mock_uvicorn.call_args.kwargs
        mock_proc.terminate.assert_called_once()


def test_server_command(tmp_path):
    runner = CliRunner()
    sample_dir = tmp_path / "sample"
    sample_dir.mkdir()

    with patch("qibocal_report.cli.uvicorn.run") as mock_uvicorn:
        result = runner.invoke(
            main,
            ["report", "server", str(sample_dir), "--port", "8001"],
        )
        assert result.exit_code == 0
        assert mock_uvicorn.called
        assert "log_config" in mock_uvicorn.call_args.kwargs


def test_client_command():
    runner = CliRunner()
    with patch("qibocal_report.cli.uvicorn.run") as mock_uvicorn:
        result = runner.invoke(
            main,
            ["report", "client", "--port", "8002"],
        )
        assert result.exit_code == 0
        assert mock_uvicorn.called
        assert "log_config" in mock_uvicorn.call_args.kwargs


def test_request_logging_configuration():
    import logging

    from uvicorn.logging import AccessFormatter

    from qibocal_report.logger import get_uvicorn_log_config

    cfg = get_uvicorn_log_config()
    access_fmt = cfg["formatters"]["access"]["fmt"]
    datefmt = cfg["formatters"]["access"]["datefmt"]

    # IP address of the server/client must be omitted
    assert "%(client_addr)s" not in access_fmt
    # Time must be in human-readable format (hours, minutes, seconds)
    assert "%(asctime)s" in access_fmt
    assert datefmt == "%H:%M:%S"

    formatter = AccessFormatter(fmt=access_fmt, datefmt=datefmt)
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='%s - "%s %s HTTP/%s" %s',
        args=("127.0.0.1:54321", "GET", "/api/reports", "1.1", 200),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "127.0.0.1" not in formatted
    assert "GET /api/reports HTTP/1.1" in formatted
    assert "200" in formatted


def test_export_command(tmp_path):
    runner = CliRunner()
    export_dest = tmp_path / "exported_site"

    result = runner.invoke(
        main,
        ["report", "export", str(export_dest), "--no-build"],
    )
    assert result.exit_code == 0
    assert (export_dest / "index.html").is_file()
    assert (export_dest / "404.html").is_file()
    assert (export_dest / ".nojekyll").is_file()


def test_export_command_with_build(tmp_path):
    runner = CliRunner()
    export_dest = tmp_path / "built_site"

    mock_res = MagicMock()
    mock_res.returncode = 0

    with patch("qibocal_report.cli.subprocess.run", return_value=mock_res) as mock_run:
        result = runner.invoke(
            main,
            [
                "report",
                "export",
                str(export_dest),
                "--build",
                "--base-path",
                "/qibocal-report/",
            ],
        )
        assert result.exit_code == 0
        assert mock_run.called
        assert (export_dest / ".nojekyll").is_file()


def test_cli_server_registration_isolation(tmp_path):
    """Test that CLI commands register servers in the isolated config directory and unregister cleanly."""
    from qibocal_report import config

    runner = CliRunner()
    sample_dir = tmp_path / "isolated_sample"
    sample_dir.mkdir()

    with patch("qibocal_report.cli.uvicorn.run"):
        result = runner.invoke(
            main,
            ["report", "server", str(sample_dir), "--port", "8999"],
        )
        assert result.exit_code == 0

    # Verify server was registered in the isolated config
    servers = config.load_servers()
    registered = [s for s in servers if "8999" in s["url"]]
    assert len(registered) == 1

    # Verify unregistering removes it cleanly
    assert config.delete_server(registered[0]["id"]) is True
    post_delete_servers = config.load_servers()
    assert not any(s["id"] == registered[0]["id"] for s in post_delete_servers)


def test_admin_list_empty(tmp_path, monkeypatch):
    import json
    cfg_dir = tmp_path / "cli_cfg_empty"
    cfg_dir.mkdir()
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(cfg_dir))

    runner = CliRunner()
    res = runner.invoke(main, ["report", "admin", "list"])
    assert res.exit_code == 0
    assert "No registered administrators found" in res.output

    res_json = runner.invoke(main, ["report", "admin", "list", "--json"])
    assert res_json.exit_code == 0
    assert json.loads(res_json.output) == []


def test_admin_list_with_users(tmp_path, monkeypatch):
    import json
    from qibocal_report import auth

    cfg_dir = tmp_path / "cli_cfg_users"
    cfg_dir.mkdir()
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(cfg_dir))

    auth.create_user("alice_admin", "pass123", "admin")
    auth.create_user("bob_editor", "pass123", "editor")

    runner = CliRunner()

    # Default list only shows admins
    res = runner.invoke(main, ["report", "admin", "list"])
    assert res.exit_code == 0
    assert "alice_admin" in res.output
    assert "bob_editor" not in res.output

    # --all shows all users
    res_all = runner.invoke(main, ["report", "admin", "list", "--all"])
    assert res_all.exit_code == 0
    assert "alice_admin" in res_all.output
    assert "bob_editor" in res_all.output

    # --json outputs valid JSON
    res_json = runner.invoke(main, ["report", "admin", "list", "--json"])
    assert res_json.exit_code == 0
    admins_data = json.loads(res_json.output)
    assert len(admins_data) == 1
    assert admins_data[0]["username"] == "alice_admin"

    # Backward compatible alias
    res_alias = runner.invoke(main, ["report", "admin-list"])
    assert res_alias.exit_code == 0
    assert "alice_admin" in res_alias.output


def test_admin_invite_non_interactive(tmp_path, monkeypatch):
    import json
    from qibocal_report import auth

    cfg_dir = tmp_path / "cli_cfg_invite_nonint"
    cfg_dir.mkdir()
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(cfg_dir))

    auth.create_user("chief_admin", "adminpass", "admin")

    runner = CliRunner()

    # Positional argument with explicit server-url
    res = runner.invoke(
        main,
        [
            "report",
            "admin",
            "invite",
            "chief_admin",
            "--server-url",
            "http://192.168.1.50:9000",
        ],
    )
    assert res.exit_code == 0
    assert "chief_admin" in res.output
    assert "http://192.168.1.50:9000/#/invite?token=" in res.output

    # Option --username and --json
    res_json = runner.invoke(
        main,
        [
            "report",
            "admin",
            "invite",
            "-u",
            "chief_admin",
            "--host",
            "localhost",
            "--port",
            "8080",
            "--json",
        ],
    )
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["username"] == "chief_admin"
    assert data["role"] == "admin"
    assert "token" in data
    assert "http://localhost:8080/#/invite?token=" in data["invite_url"]


def test_admin_invite_interactive_and_shortcuts(tmp_path, monkeypatch):
    from qibocal_report import auth

    cfg_dir = tmp_path / "cli_cfg_invite_int"
    cfg_dir.mkdir()
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(cfg_dir))

    auth.create_user("admin1", "pass123", "admin")
    auth.create_user("admin2", "pass123", "admin")
    auth.create_user("user_viewer", "pass123", "viewer")

    runner = CliRunner()

    # Interactive prompt choosing 2
    res_int = runner.invoke(
        main,
        ["report", "admin", "invite", "--interactive"],
        input="2\n",
    )
    assert res_int.exit_code == 0
    assert "admin2" in res_int.output
    assert "/#/invite?token=" in res_int.output

    # Report direct shortcut `qibocal report invite <username>`
    res_shortcut = runner.invoke(
        main,
        ["report", "invite", "admin1", "--json"],
    )
    assert res_shortcut.exit_code == 0
    import json
    data = json.loads(res_shortcut.output)
    assert data["username"] == "admin1"

    # Nonexistent user fails
    res_nonexistent = runner.invoke(
        main,
        ["report", "admin", "invite", "ghost_user"],
    )
    assert res_nonexistent.exit_code != 0
    assert "not found" in res_nonexistent.output

    # Non-admin user fails
    res_viewer = runner.invoke(
        main,
        ["report", "admin", "invite", "user_viewer"],
    )
    assert res_viewer.exit_code != 0
    assert "not 'admin'" in res_viewer.output


def test_admin_invite_empty_instance(tmp_path, monkeypatch):
    import json
    cfg_dir = tmp_path / "cli_cfg_empty_instance"
    cfg_dir.mkdir()
    monkeypatch.setenv("QIBOCAL_REPORT_CONFIG_DIR", str(cfg_dir))

    runner = CliRunner()
    res = runner.invoke(main, ["report", "admin", "invite", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["username"] is None
    assert data["role"] == "admin"
    assert "/#/invite?token=" in data["invite_url"]


