"""Command Line Interface for qibocal-report (Issue #9, #10, #11)."""

import os
import sys
from pathlib import Path
import click
import uvicorn

from qibocal_report import config
from qibocal_report.api import app, set_report_root


@click.group()
@click.version_option(version="0.1.0", prog_name="qibocal-report")
def main():
    """qibocal-report: Modern web app and server for Qibocal calibration reports."""
    pass


@main.command()
@click.argument("directory", default=".", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--host", default="127.0.0.1", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload for development.")
def serve(directory: str, host: str, port: int, reload: bool):
    """
    Serve Qibocal reports from DIRECTORY.
    Spawns both backend server and frontend web application (Issue #9, #10, #11).
    """
    dir_path = Path(directory).resolve()
    set_report_root(dir_path)
    os.environ["QIBOCAL_REPORT_DIR"] = str(dir_path)

    url = f"http://{host}:{port}"
    # Register this server in configuration
    config.add_server(
        url=url,
        name=f"local-{dir_path.name}",
        description=f"Serving reports from {dir_path}",
        avatar="quantum-ring"
    )

    click.secho("\n⚛️  Qibocal Report Server", fg="magenta", bold=True)
    click.echo(f"📁 Reports Directory : {dir_path}")
    click.echo(f"🌐 Web Application   : {url}")
    click.echo(f"📖 REST API Docs     : {url}/api/docs/swagger\n")
    click.echo("Press Ctrl+C to stop the server.\n")

    uvicorn.run("qibocal_report.api:app", host=host, port=port, reload=reload)


@main.command()
@click.option("--host", default="127.0.0.1", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload.")
def dashboard(host: str, port: int, reload: bool):
    """
    Start the dashboard to browse and manage multiple Qibocal report servers (Issue #11, #4).
    """
    url = f"http://{host}:{port}"
    click.secho("\n⚛️  Qibocal Report Dashboard", fg="magenta", bold=True)
    click.echo(f"🌐 Dashboard URL  : {url}/#/servers")
    click.echo("Press Ctrl+C to stop the server.\n")

    uvicorn.run("qibocal_report.api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
