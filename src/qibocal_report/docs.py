"""Documentation catalog and markdown content resolver."""

import sysconfig
from pathlib import Path

from fastapi import HTTPException

DOCS_NAVIGATION = [
    {
        "section": "Overview",
        "path": "index",
        "items": [
            {
                "id": "index",
                "path": "index",
                "title": "Overview & Ecosystem",
                "description": (
                    "Introduction to Qibo ecosystem, projects, and qibocal-report"
                    " architecture"
                ),
            }
        ],
    },
    {
        "section": "User Guide",
        "path": "user-guide",
        "items": [
            {
                "id": "user-guide/quickstart",
                "path": "user-guide/quickstart",
                "title": "Getting Started & Quickstart",
                "description": (
                    "Installation, CLI commands, and report directory structure"
                ),
            },
            {
                "id": "user-guide/dashboard",
                "path": "user-guide/dashboard",
                "title": "Dashboard & Server Management",
                "description": (
                    "Managing servers, search, smart facets, dual views, and bulk"
                    " actions"
                ),
            },
            {
                "id": "user-guide/reports",
                "path": "user-guide/reports",
                "title": "Reports, Protocols & Exports",
                "description": (
                    "Interactive charts, protocol timings, downloads, and PDF printing"
                ),
            },
        ],
    },
    {
        "section": "Developer & Architecture",
        "path": "developer",
        "items": [
            {
                "id": "developer/architecture",
                "path": "developer/architecture",
                "title": "System Architecture",
                "description": (
                    "FastAPI backend, Vue 3 SPA frontend, and execution modes"
                ),
            },
            {
                "id": "developer/workflow",
                "path": "developer/workflow",
                "title": "Development Workflow",
                "description": (
                    "devenv environment, live Vite HMR, testing, and packaging"
                ),
            },
            {
                "id": "developer/design-system",
                "path": "developer/design-system",
                "title": "Design System & Aesthetics",
                "description": (
                    "BackMarket design palette, typography, and print media CSS"
                ),
            },
        ],
    },
    {
        "section": "Reference",
        "path": "reference",
        "items": [
            {
                "id": "reference/cli",
                "path": "reference/cli",
                "title": "CLI Reference",
                "description": (
                    "Complete command line options and environment variables"
                ),
            },
            {
                "id": "reference/api",
                "path": "reference/api",
                "title": "REST API & WebSockets",
                "description": (
                    "REST endpoints specification, schemas, and WebSocket events"
                ),
            },
        ],
    },
]


def resolve_docs_content(doc_name: str) -> str:
    """Serve plain markdown documentation content (sections/subpages or legacy)."""
    clean_name = doc_name.strip("/").removesuffix(".md")
    if not clean_name:
        clean_name = "index"

    roots = [
        Path(__file__).resolve().parents[2] / "docs",
        Path.cwd() / "docs",
        Path(sysconfig.get_path("purelib")) / "docs",
        Path(sysconfig.get_path("purelib")),
        Path(sysconfig.get_path("data")) / "docs",
        Path(sysconfig.get_path("data")),
    ]

    targets = [
        f"{clean_name}/index.md",
        f"{clean_name}.md",
    ]

    for root in roots:
        for target in targets:
            p = root / target
            if p.is_file():
                return p.read_text(encoding="utf-8")

    # Fallback: if doc_name matches a section path, generate minimal Table of Contents
    for sec in DOCS_NAVIGATION:
        if sec.get("path") == clean_name and sec.get("items"):
            lines = [
                f"# {sec['section']}",
                "",
            ]
            for item in sec["items"]:
                lines.append(f"- [{item['title']}]({item['path']})")
            lines.append("")
            return "\n".join(lines)

    raise HTTPException(status_code=404, detail=f"Documentation '{doc_name}' not found")
