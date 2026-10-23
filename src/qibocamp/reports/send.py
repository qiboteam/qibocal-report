"""Reports sent to a server from the command line: what the dashboard does, by hand.

The dashboard uploads a report it downloaded from one server; here it is a
folder on this machine — zipped on the fly, under its own name — or a zip
already made, as a Download gives it. Either goes to `POST /api/uploads`,
the one way a server receives a report, signed in as its policy asks.
"""

import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

import httpx

# A report weighs what its data do: no limit on the transfer itself.
TIMEOUT = httpx.Timeout(30.0, read=None, write=None)


class SendError(Exception):
    """A report not sent, said the way the command line tells it."""


@dataclass(frozen=True)
class Sent:
    id: str
    name: str


def server_address(value: str) -> str:
    """A server's base address, as the dashboard normalises it."""
    clean = value.strip().rstrip("/")
    if not clean.startswith(("http://", "https://")):
        clean = f"http://{clean}"
    return clean


def is_report_folder(path: Path) -> bool:
    """Whether a folder is a report a server takes: one with its `meta.json`."""
    return (path / "meta.json").is_file() or (path / "report" / "meta.json").is_file()


def zip_report(folder: Path, destination: Path) -> Path:
    """The zip of a report folder, under its own name, as a server receives it.

    Written to a file, not memory: a report holds all its data. Links are
    followed, so the archive holds files only, which a server requires.
    """
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                archive.write(path, f"{folder.name}/{path.relative_to(folder).as_posix()}")
    return destination


def failure(response: httpx.Response) -> str:
    """What a refusal means, from its status and the server's own words."""
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None
    meaning = {
        401: "Sign in first: --username, or --token.",
        403: "This account may not upload to this server.",
        409: "A report of that name is already there, and is never overwritten.",
        413: "The report is larger than this server accepts.",
    }.get(response.status_code)
    said = detail if isinstance(detail, str) else response.reason_phrase
    return f"{said} ({response.status_code})" + (f". {meaning}" if meaning and meaning not in said else "")


def sign_in(client: httpx.Client, server: str, username: str, password: str) -> str:
    """A token for `username`, from the server's own sign-in."""
    response = client.post(f"{server}/api/auth/login", json={"username": username, "password": password})
    if response.status_code != 200:
        raise SendError(f"Could not sign in to {server}: {failure(response)}")
    return response.json()["access_token"]


def send_report(
    path: Path,
    server: str,
    *,
    token: str | None = None,
    username: str | None = None,
    password: str | None = None,
    transport: httpx.BaseTransport | None = None,
) -> Sent:
    """Upload the report at `path` — a folder, or the zip of one — to `server`."""
    server = server_address(server)
    path = Path(path).expanduser()
    if path.is_dir():
        if not is_report_folder(path):
            raise SendError(f"{path} is not a report: there is no meta.json in it.")
    elif not (path.is_file() and zipfile.is_zipfile(path)):
        raise SendError(f"{path} is neither a report folder nor a zip archive.")
    with httpx.Client(timeout=TIMEOUT, transport=transport) as client, tempfile.TemporaryDirectory() as scratch:
        try:
            if token is None and username is not None:
                token = sign_in(client, server, username, password or "")
            headers = {"Content-Type": "application/zip"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            # Asked first, as the dashboard does: a refusal costs no transfer.
            capability = client.get(f"{server}/api/uploads", headers=headers)
            if capability.status_code != 200:
                raise SendError(f"{server} does not take uploads: {failure(capability)}")
            if not capability.json().get("accepted"):
                hint = "sign in with --username, or --token" if not token else "this account may not upload there"
                raise SendError(f"{server} does not accept this upload: {hint}.")
            archive = path if path.is_file() else zip_report(path, Path(scratch) / f"{path.name}.zip")
            with open(archive, "rb") as body:
                response = client.post(f"{server}/api/uploads", content=body, headers=headers)
        except httpx.HTTPError as error:
            raise SendError(f"Could not reach {server}: {error}") from error
        if response.status_code != 200:
            raise SendError(f"Not uploaded: {failure(response)}")
        result = response.json()
        return Sent(id=result["id"], name=result["name"])
