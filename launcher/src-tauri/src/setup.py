"""Create the launcher's own Qibocamp environment, or bring it up to date.

Run by the launcher as ``python setup.py '<json>'`` with the environment
``path``, the ``packages`` to put in it, whether to ``upgrade`` them, and a
``timeout`` in seconds. The notebook worker that ships with qibocamp
already knows how to create and fill an environment — with uv, installed
once under the cache when there is none, or with venv and pip — so it is
written next to this file and executed from here, the way the report worker
uses it on a remote host — nothing is installed to run this.
"""

import json
import os
import sys
from pathlib import Path


def main():
    options = json.loads(sys.argv[1])
    path = Path(options["path"])
    packages = list(options.get("packages") or ["qibocamp"])
    upgrade = bool(options.get("upgrade"))

    worker = Path(__file__).with_name("notebook_worker.py")
    shared = {"__name__": "qibocamp.remote.notebook_worker"}
    exec(compile(worker.read_text(encoding="utf-8"), str(worker), "exec"), shared)  # noqa: S102
    # Progress as plain lines: the launcher shows the output as it comes.
    shared["event"] = lambda kind, **details: print(details.get("message", kind), flush=True)
    WorkerError = shared["WorkerError"]
    runtime = shared["Runtime"](float(options.get("timeout") or 1800))

    try:
        if os.name == "nt":
            python = path / "Scripts" / "python.exe"
            executable = path / "Scripts" / "qibocamp.exe"
            if not python.is_file():
                print(f"Creating environment: {path}", flush=True)
                path.parent.mkdir(parents=True, exist_ok=True)
                runtime.command([sys.executable, "-m", "venv", str(path)])
        else:
            python = Path(shared["ensure_environment"](runtime, path))
            executable = path / "bin" / "qibocamp"

        marker = path / "qibocamp.json"
        try:
            held = json.loads(marker.read_text(encoding="utf-8")).get("package")
        except (OSError, ValueError, AttributeError):
            held = None

        # uv when it can be had, pip otherwise: the worker decides.
        def install(**flags):
            return shared["install_command"](runtime, str(python), packages, **flags)

        if not executable.is_file():
            print(f"Installing {', '.join(packages)} in: {path}", flush=True)
            runtime.command(install(upgrade=True))
        elif upgrade or held != packages[0]:
            # A branch or commit archive carries the same version number as
            # the one installed, so pip would call it satisfied and change
            # nothing: the package itself is put back by force, on its own,
            # and the dependencies brought up to date after it.
            print(f"Replacing {held or 'what is installed'} with {', '.join(packages)} in: {path}", flush=True)
            runtime.command(install(upgrade=True, reinstall=True, no_deps=True))
            runtime.command(install(upgrade=True))
        if not executable.is_file():
            raise WorkerError(
                f"{path} has no qibocamp after installing {', '.join(packages)}; "
                "check the version chosen in the developer options"
            )
        # Which requirement the environment holds, for the launcher to show.
        marker.write_text(
            json.dumps({"package": packages[0], "packages": packages}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"qibocamp is ready: {executable}", flush=True)
    except (WorkerError, OSError) as error:
        print(f"Setup failed: {error}", file=sys.stderr, flush=True)
        return 1
    except shared["Stopped"]:
        return 1
    finally:
        runtime.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
