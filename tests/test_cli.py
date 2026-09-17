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
    assert "serve" in result.output
    assert "server" in result.output
    assert "client" in result.output
    assert "dev" in result.output


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


def test_client_command():
    runner = CliRunner()
    with patch("qibocal_report.cli.uvicorn.run") as mock_uvicorn:
        result = runner.invoke(
            main,
            ["report", "client", "--port", "8002"],
        )
        assert result.exit_code == 0
        assert mock_uvicorn.called
