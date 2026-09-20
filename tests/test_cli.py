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
