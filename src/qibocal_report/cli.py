"""Command Line Interface for qibocal (Issue #9, #10, #11)."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import uvicorn

from qibocal_report import config
from qibocal_report.api import set_report_root
from qibocal_report.logger import get_uvicorn_log_config


@click.group(name="qibocal")
@click.version_option(version="0.1.0", prog_name="qibocal")
def main():
    """Qibocal: Quantum calibration and characterization framework."""


@main.command(name="notebook")
@click.argument("connection", required=False)
@click.option("--ssh", help="SSH options followed by a host or user@host destination.")
@click.option("-q", "--queue", help="SLURM partition on the access node.")
@click.option("--slurm", help="Additional srun options, as a quoted argument string.")
@click.option("-w", "--workdir", help="Working directory on the access node.")
@click.option("--venv", help="Kernel environment name or path on the computing node.")
@click.option(
    "--marimo/--jupyter", default=None, help="Use Marimo instead of JupyterLab."
)
@click.option(
    "--no-interactive/--interactive",
    "-n",
    default=None,
    help="Print the connection URL without opening a browser.",
)
@click.option(
    "--timeout",
    type=click.FloatRange(min=0, min_open=True),
    help="Startup timeout in seconds (default: 300).",
)
def notebook(connection: str | None, **options):
    """Start a local, SSH, or SLURM notebook, optionally using a named CONNECTION."""
    from qibocal_report.notebook import launch, load_options

    launch(load_options(connection, options))


@main.group(name="config")
def config_group():
    """Locate and clean local server configurations."""


@config_group.command(name="path")
def config_path():
    """Print the configuration directory as a plain-text absolute path."""
    click.echo(config.get_config_dir(create=False).resolve())


@config_group.command(name="clean")
@click.option(
    "-f", "--force", is_flag=True, help="Remove configurations without prompting."
)
def config_clean(force: bool):
    """Erase registered servers and authentication data, asking for confirmation."""
    from qibocal_report import auth

    config_dir = config.get_config_dir(create=False)
    paths = dict.fromkeys(
        path.parent.resolve() / path.name
        for path in (
            config.get_config_file(create=False),
            config_dir / "auth.json",
            auth.get_auth_file(create=False),
        )
    )
    existing = [path for path in paths if path.exists() or path.is_symlink()]
    if not existing:
        click.echo("No configuration files to remove.", err=True)
        return

    for path in existing:
        if path.is_dir() and not path.is_symlink():
            raise click.ClickException(
                f"Refusing to remove configuration directory '{path}'."
            )

    if not force:
        click.echo(
            "This erases registered servers, users, invitations, and signing keys:",
            err=True,
        )
        for path in existing:
            click.echo(f"  {path}", err=True)
        click.confirm(
            "Remove these configuration files?", default=False, abort=True, err=True
        )

    for path in existing:
        try:
            path.unlink()
        except OSError as exc:
            raise click.ClickException(f"Could not remove '{path}': {exc}") from exc
        click.echo(f"Removed {path}", err=True)


@main.group(name="report")
def report():
    """Manage and serve Qibocal calibration reports."""


@report.command(name="server")
@click.argument(
    "directory",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option("--host", default="localhost", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
@click.option(
    "--auth/--no-auth",
    default=False,
    help="Enable user authentication and role management.",
)
def server(directory: str, host: str, port: int, auth: bool):
    """Start the FastAPI backend server."""
    dir_path = Path(directory).resolve()
    os.environ["QIBOCAL_ORIGINAL_REPORT_DIR"] = str(dir_path)
    os.environ["QIBOCAL_REPORT_DIR"] = str(dir_path)
    set_report_root(dir_path, is_original=True)

    if auth:
        os.environ["QIBOCAL_AUTH_ENABLED"] = "1"
        from qibocal_report import auth as auth_mod

        auth_mod.set_auth_enabled(True)
        initial_token = auth_mod.create_initial_admin_invite_if_needed()
    else:
        initial_token = None

    url = f"http://{host}:{port}"
    config.add_server(
        url=url,
        name=f"local-{dir_path.name}",
        description=f"Serving reports from {dir_path}",
        avatar="quantum-ring",
    )

    console = Console()
    auth_lines = ""
    if auth:
        auth_lines = (
            f"\n[bold cyan]🔒 Auth & Roles       :[/bold cyan] [green]Enabled[/green]"
        )
        if initial_token:
            auth_lines += (
                f"\n[bold yellow]🔑 Admin Invite Link  :[/bold yellow] "
                f"{url}/#/invite?token={initial_token}"
            )

    console.print(
        Panel.fit(
            f"[bold cyan]📁 Reports Directory :[/bold cyan] {dir_path}\n"
            f"[bold cyan]⚙️  FastAPI Server   :[/bold cyan] {url}\n"
            f"[bold cyan]📖 REST API Docs     :[/bold cyan] {url}/api/docs/swagger"
            f"{auth_lines}\n\n"
            "[dim]Press Ctrl+C to stop the server.[/dim]",
            title="[bold magenta]⚛️  Qibocal Report Server[/bold magenta]",
            border_style="magenta",
        )
    )

    uvicorn.run(
        "qibocal_report.api:app",
        host=host,
        port=port,
        log_config=get_uvicorn_log_config(),
    )


@report.command(name="dev")
@click.argument(
    "directory",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option("--host", default="localhost", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Backend port to listen on.")
@click.option(
    "--frontend-port", default=5173, type=int, help="Frontend Vite dev server port."
)
@click.option(
    "--reload/--no-reload",
    default=True,
    help="Enable auto-reload for backend server.",
)
@click.option(
    "--auth/--no-auth",
    default=False,
    help="Enable user authentication and role management.",
)
def dev(
    directory: str,
    host: str,
    port: int,
    frontend_port: int,
    reload: bool = True,
    auth: bool = False,
):
    """Serve Qibocal reports in developer mode with live Vite HMR."""
    dir_path = Path(directory).resolve()
    os.environ["QIBOCAL_ORIGINAL_REPORT_DIR"] = str(dir_path)
    os.environ["QIBOCAL_REPORT_DIR"] = str(dir_path)
    set_report_root(dir_path, is_original=True)

    if auth:
        os.environ["QIBOCAL_AUTH_ENABLED"] = "1"
        from qibocal_report import auth as auth_mod

        auth_mod.set_auth_enabled(True)
        initial_token = auth_mod.create_initial_admin_invite_if_needed()
    else:
        initial_token = None

    # Locate frontend directory
    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    if not frontend_dir.is_dir() or not (frontend_dir / "package.json").is_file():
        frontend_dir = Path.cwd() / "frontend"

    if not frontend_dir.is_dir() or not (frontend_dir / "package.json").is_file():
        raise click.ClickException(
            f"Frontend directory not found at '{frontend_dir}'. "
            "Developer mode requires the frontend source tree."
        )

    # Determine package manager command
    if shutil.which("pnpm"):
        vite_cmd = ["pnpm", "run", "dev", "--port", str(frontend_port), "--host", host]
    elif shutil.which("npm"):
        vite_cmd = [
            "npm",
            "run",
            "dev",
            "--",
            "--port",
            str(frontend_port),
            "--host",
            host,
        ]
    elif shutil.which("npx"):
        vite_cmd = ["npx", "vite", "--port", str(frontend_port), "--host", host]
    else:
        raise click.ClickException(
            "Could not find 'pnpm' or 'npm' in PATH. "
            "Developer mode requires Node.js and pnpm or npm."
        )

    backend_url = f"http://{host}:{port}"
    frontend_url = f"http://{host}:{frontend_port}"
    os.environ["QIBOCAL_FRONTEND_URL"] = frontend_url

    # Register this server in configuration
    config.add_server(
        url=backend_url,
        name=f"local-{dir_path.name}-dev",
        description=f"Serving reports (dev mode) from {dir_path}",
        avatar="quantum-ring",
    )

    console = Console()
    dev_title = "[bold magenta]⚛️  Qibocal Report (Developer Mode)[/bold magenta]"
    auth_lines = ""
    if auth:
        auth_lines = (
            f"\n[bold cyan]🔒 Auth & Roles       :[/bold cyan] [green]Enabled[/green]"
        )
        if initial_token:
            auth_lines += (
                f"\n[bold yellow]🔑 Admin Invite Link  :[/bold yellow] "
                f"{frontend_url}/#/invite?token={initial_token}"
            )

    panel_content = (
        f"[bold cyan]📁 Reports Directory :[/bold cyan] {dir_path}\n"
        f"[bold cyan]⚡ Vite Dev Frontend :[/bold cyan] {frontend_url}\n"
        f"[bold cyan]⚙️  Backend API       :[/bold cyan] {backend_url}\n"
        f"[bold cyan]📖 REST API Docs     :[/bold cyan] "
        f"{backend_url}/api/docs/swagger"
        f"{auth_lines}\n\n"
        "[dim]Starting Vite development server with Hot Module Replacement...[/dim]\n"
        "[dim]Press Ctrl+C to stop both backend and frontend.[/dim]"
    )
    console.print(Panel.fit(panel_content, title=dev_title, border_style="magenta"))

    env = os.environ.copy()
    env["BACKEND_URL"] = backend_url

    vite_proc = subprocess.Popen(vite_cmd, cwd=frontend_dir, env=env)

    try:
        uvicorn.run(
            "qibocal_report.api:app",
            host=host,
            port=port,
            reload=reload,
            log_config=get_uvicorn_log_config(),
        )
    finally:
        if vite_proc.poll() is None:
            console.print("\n[dim]Stopping Vite development server...[/dim]")
            vite_proc.terminate()
            try:
                vite_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                vite_proc.kill()


@report.command(name="develop", hidden=True)
@click.argument(
    "directory",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option("--host", default="localhost", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Backend port to listen on.")
@click.option(
    "--frontend-port", default=5173, type=int, help="Frontend Vite dev server port."
)
@click.option(
    "--reload/--no-reload",
    default=True,
    help="Enable auto-reload for backend server.",
)
@click.option(
    "--auth/--no-auth",
    default=False,
    help="Enable user authentication and role management.",
)
@click.pass_context
def develop_alias(
    ctx,
    directory: str,
    host: str,
    port: int,
    frontend_port: int,
    reload: bool,
    auth: bool,
):
    """Backward-compatible alias for 'dev'."""
    ctx.forward(dev)


@report.command(name="client")
@click.option("--host", default="127.0.0.1", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload.")
def client(host: str, port: int, reload: bool):
    """Start the client.

    To browse and manage multiple Qibocal report servers.
    """
    url = f"http://{host}:{port}"
    console = Console()
    console.print(
        Panel.fit(
            f"[bold cyan]🌐 Client URL :[/bold cyan] {url}/#/servers\n\n"
            "[dim]Press Ctrl+C to stop the client.[/dim]",
            title="[bold magenta]⚛️  Qibocal Report Client[/bold magenta]",
            border_style="magenta",
        )
    )

    uvicorn.run(
        "qibocal_report.api:app",
        host=host,
        port=port,
        reload=reload,
        log_config=get_uvicorn_log_config(),
    )


@report.command(name="dashboard", hidden=True)
@click.option("--host", default="127.0.0.1", help="Host address to bind to.")
@click.option("--port", default=8000, type=int, help="Port to listen on.")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload.")
@click.pass_context
def dashboard_alias(ctx, host: str, port: int, reload: bool):
    """Backward-compatible alias for 'client'."""
    ctx.forward(client)


@report.command(name="export")
@click.argument(
    "output_dir",
    default="./dist",
    type=click.Path(file_okay=False, dir_okay=True),
)
@click.option(
    "--build/--no-build",
    default=True,
    help="Build frontend from source if frontend directory exists.",
)
@click.option(
    "--base-path",
    default="./",
    help="Base URL path for assets (default: ./ for relative paths).",
)
def export_static(output_dir: str, build: bool, base_path: str):
    """Export static web application for hosting (e.g. GitHub Pages)."""
    out_path = Path(output_dir).resolve()
    console = Console()

    # Locate frontend directory
    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    if not frontend_dir.is_dir() or not (frontend_dir / "package.json").is_file():
        frontend_dir = Path.cwd() / "frontend"

    has_frontend_src = (
        frontend_dir.is_dir() and (frontend_dir / "package.json").is_file()
    )

    built_fresh = False
    if build and has_frontend_src:
        console.print(f"[dim]Building frontend in {frontend_dir}...[/dim]")
        if shutil.which("pnpm"):
            cmd = ["pnpm", "run", "build"]
        elif shutil.which("npm"):
            cmd = ["npm", "run", "build"]
        elif shutil.which("npx"):
            cmd = ["npx", "vite", "build"]
        else:
            raise click.ClickException(
                "Neither pnpm nor npm found in PATH to build frontend."
            )
        env = os.environ.copy()
        env["BASE_PATH"] = base_path
        res = subprocess.run(cmd, cwd=frontend_dir, env=env, check=False)
        if res.returncode != 0:
            raise click.ClickException(
                f"Frontend build failed with exit code {res.returncode}"
            )
        source_dist = frontend_dir / "dist"
        built_fresh = True
    else:
        source_dist = Path(__file__).resolve().parent / "static"
        if not source_dist.is_dir() or not (source_dist / "index.html").is_file():
            if has_frontend_src and (frontend_dir / "dist" / "index.html").is_file():
                source_dist = frontend_dir / "dist"
            else:
                raise click.ClickException(
                    "No static build found in static directory or frontend/dist. "
                    "Run with --build or build the frontend first."
                )

    out_path.mkdir(parents=True, exist_ok=True)
    if out_path != source_dist.resolve():
        for item in source_dist.iterdir():
            dest = out_path / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    (out_path / ".nojekyll").touch(exist_ok=True)
    if (out_path / "index.html").is_file() and not (out_path / "404.html").is_file():
        shutil.copy2(out_path / "index.html", out_path / "404.html")

    src_label = "Fresh build from source" if built_fresh else str(source_dist)
    console.print(
        Panel.fit(
            f"[bold cyan]📁 Export Destination :[/bold cyan] {out_path}\n"
            f"[bold cyan]🌐 Base Asset Path    :[/bold cyan] {base_path}\n"
            f"[bold cyan]📦 Source             :[/bold cyan] {src_label}\n\n"
            "[green]✓ Static export ready for GitHub Pages or static web hosts.[/green]",
            title="[bold magenta]⚛️  Qibocal Report Static Export[/bold magenta]",
            border_style="magenta",
        )
    )


# --- Administrator and Invite Link Management ---
@report.group(name="admin")
def admin_group():
    """Manage server administrators and invitation links."""


@admin_group.command(name="list")
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    default=False,
    help="List all registered users, including non-administrators.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output administrators in JSON format.",
)
def admin_list(show_all: bool, output_json: bool):
    """List registered server administrators."""
    from qibocal_report import auth as auth_mod

    users = auth_mod.list_users() if show_all else auth_mod.list_admins()
    if output_json:
        click.echo(json.dumps(users, indent=2))
        return

    console = Console()
    if not users:
        label = "users" if show_all else "administrators"
        console.print(
            f"[yellow]No registered {label} found in authentication database.[/yellow]"
        )
        console.print(
            "[dim]Hint: Start the server with --auth to generate an initial admin invite link.[/dim]"
        )
        return

    title = "Registered Users" if show_all else "Registered Administrators"
    table = Table(title=f"⚛️  {title}", border_style="magenta")
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("Username", style="bold cyan")
    table.add_column("Role", style="bold")
    table.add_column("User ID", style="dim")
    table.add_column("Created At", style="green")

    for idx, u in enumerate(users, start=1):
        role = u.get("role", "")
        role_styled = (
            f"[bold magenta]{role}[/bold magenta]"
            if role == "admin"
            else f"[bold blue]{role}[/bold blue]"
            if role == "editor"
            else f"[dim]{role}[/dim]"
        )
        created = u.get("created_at", "")
        if created and "T" in created:
            created = created.replace("T", " ")[:19]
        table.add_row(
            str(idx), u.get("username", ""), role_styled, u.get("id", ""), created
        )

    console.print(table)


@admin_group.command(name="invite")
@click.argument("username", required=False, default=None)
@click.option(
    "-u",
    "--username",
    "opt_username",
    default=None,
    help="Administrator username for which to regenerate the invite link.",
)
@click.option(
    "--server-url",
    default=None,
    help="Explicit base URL of the report server (e.g. http://localhost:8000).",
)
@click.option(
    "--host",
    default=None,
    help="Server host to use when constructing the invite link.",
)
@click.option(
    "--port",
    default=None,
    type=int,
    help="Server port to use when constructing the invite link.",
)
@click.option(
    "-e",
    "--expires-in-hours",
    default=168,
    type=int,
    help="Invite link validity in hours (default: 168 = 7 days, 0 for never expires).",
)
@click.option(
    "--interactive/--no-interactive",
    default=None,
    help="Force interactive or non-interactive administrator selection.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output generated invitation details in JSON format.",
)
def admin_invite(
    username: str | None,
    opt_username: str | None,
    server_url: str | None,
    host: str | None,
    port: int | None,
    expires_in_hours: int,
    interactive: bool | None,
    output_json: bool,
):
    """Regenerate an invitation link for a server administrator."""
    from qibocal_report import auth as auth_mod
    from qibocal_report import config

    console = Console()
    target_username = (username or opt_username or "").strip()
    admins = auth_mod.list_admins()
    all_users = auth_mod.list_users()

    is_tty = sys.stdin.isatty() if hasattr(sys.stdin, "isatty") else False
    should_interact = (interactive is True) or (
        interactive is None and is_tty and not target_username
    )

    if not target_username:
        if not all_users and not admins:
            # Fresh instance without any users registered yet
            if not output_json:
                console.print(
                    "[yellow]No registered administrators found in the database.[/yellow]\n"
                    "[dim]Generating an initial administrator invitation token...[/dim]"
                )
            chosen_username = None
        elif should_interact:
            if not admins:
                existing_names = ", ".join(u["username"] for u in all_users) or "None"
                raise click.ClickException(
                    f"No administrators exist in the database. Existing users are: {existing_names}"
                )
            if len(admins) == 1:
                chosen_username = admins[0]["username"]
                if not output_json:
                    console.print(
                        f"[cyan]Found 1 administrator:[/cyan] [bold]{chosen_username}[/bold]"
                    )
            else:
                if not output_json:
                    console.print("[bold cyan]Available Administrators:[/bold cyan]")
                    for idx, a in enumerate(admins, start=1):
                        console.print(
                            f"  [bold magenta][{idx}][/bold magenta] {a['username']} [dim](ID: {a['id']})[/dim]"
                        )
                choice = click.prompt(
                    f"Select administrator [1-{len(admins)}] or enter username",
                    default="1",
                ).strip()
                if choice.isdigit() and 1 <= int(choice) <= len(admins):
                    chosen_username = admins[int(choice) - 1]["username"]
                else:
                    match = next(
                        (
                            a["username"]
                            for a in admins
                            if a["username"].lower() == choice.lower()
                        ),
                        None,
                    )
                    if match:
                        chosen_username = match
                    else:
                        raise click.ClickException(
                            f"Invalid administrator selection '{choice}'."
                        )
        else:
            # Non-interactive and no username passed
            if len(admins) == 1:
                chosen_username = admins[0]["username"]
            elif not admins and not all_users:
                chosen_username = None
            else:
                available = ", ".join(a["username"] for a in admins)
                raise click.ClickException(
                    f"Missing administrator username. Please specify a username or run interactively.\n"
                    f"Available administrators: {available}"
                )
    else:
        # target_username was explicitly given
        user_match = next(
            (
                u
                for u in all_users
                if u["username"].lower() == target_username.lower()
            ),
            None,
        )
        if not user_match:
            available = ", ".join(a["username"] for a in admins) or "None"
            raise click.ClickException(
                f"Administrator user '{target_username}' not found. Available administrators: {available}"
            )
        if user_match.get("role") != "admin":
            raise click.ClickException(
                f"User '{user_match['username']}' has role '{user_match['role']}', not 'admin'."
            )
        chosen_username = user_match["username"]

    # Generate or regenerate the invite token
    try:
        invite_data = auth_mod.regenerate_admin_invite(
            username=chosen_username,
            expires_in_hours=expires_in_hours if expires_in_hours > 0 else None,
        )
    except ValueError as err:
        raise click.ClickException(str(err))

    # Resolve server base URL
    if server_url:
        base_url = server_url.rstrip("/")
    else:
        if host is not None or port is not None:
            h = host or "localhost"
            p = port or 8000
            base_url = f"http://{h}:{p}"
        else:
            servers = config.load_servers()
            if servers and servers[0].get("url"):
                base_url = servers[0]["url"].rstrip("/")
            else:
                base_url = "http://localhost:8000"

    invite_url = f"{base_url}/#/invite?token={invite_data['token']}"
    expires_str = invite_data.get("expires_at") or "Never"

    if output_json:
        result = {
            "username": chosen_username,
            "role": invite_data["role"],
            "token": invite_data["token"],
            "invite_url": invite_url,
            "expires_at": invite_data.get("expires_at"),
            "server_url": base_url,
        }
        click.echo(json.dumps(result, indent=2))
        return

    admin_display = (
        f"[bold green]{chosen_username}[/bold green]"
        if chosen_username
        else "[bold yellow]Initial Admin (Unregistered)[/bold yellow]"
    )
    panel_content = (
        f"[bold cyan]👤 Administrator  :[/bold cyan] {admin_display}\n"
        f"[bold cyan]🔒 Assigned Role  :[/bold cyan] [bold magenta]admin[/bold magenta]\n"
        f"[bold cyan]⏰ Validity       :[/bold cyan] {expires_str}\n"
        f"[bold cyan]🌐 Server Endpoint:[/bold cyan] {base_url}\n\n"
        f"[bold yellow]🔑 Invite Link    :[/bold yellow]\n"
        f"[underline bold]{invite_url}[/underline bold]\n\n"
        "[dim]To restore access:\n"
        "  1. Open the invite link directly in your browser, or\n"
        "  2. Paste it into the connect bar in Server Management (#/servers).[/dim]"
    )
    console.print(
        Panel.fit(
            panel_content,
            title="[bold magenta]⚛️  Qibocal Admin Invite Link[/bold magenta]",
            border_style="magenta",
        )
    )


@report.command(name="invite")
@click.argument("username", required=False, default=None)
@click.option(
    "-u",
    "--username",
    "opt_username",
    default=None,
    help="Administrator username for which to regenerate the invite link.",
)
@click.option(
    "--server-url",
    default=None,
    help="Explicit base URL of the report server (e.g. http://localhost:8000).",
)
@click.option(
    "--host",
    default=None,
    help="Server host to use when constructing the invite link.",
)
@click.option(
    "--port",
    default=None,
    type=int,
    help="Server port to use when constructing the invite link.",
)
@click.option(
    "-e",
    "--expires-in-hours",
    default=168,
    type=int,
    help="Invite link validity in hours (default: 168 = 7 days, 0 for never expires).",
)
@click.option(
    "--interactive/--no-interactive",
    default=None,
    help="Force interactive or non-interactive administrator selection.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output generated invitation details in JSON format.",
)
@click.pass_context
def invite_shortcut(
    ctx,
    username: str | None,
    opt_username: str | None,
    server_url: str | None,
    host: str | None,
    port: int | None,
    expires_in_hours: int,
    interactive: bool | None,
    output_json: bool,
):
    """Regenerate an invitation link for a server administrator."""
    ctx.forward(admin_invite)


@report.command(name="admin-list", hidden=True)
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    default=False,
    help="List all registered users, including non-administrators.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output administrators in JSON format.",
)
@click.pass_context
def admin_list_shortcut(ctx, show_all: bool, output_json: bool):
    """Backward-compatible alias for 'admin list'."""
    ctx.forward(admin_list)
