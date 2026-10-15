"""The web interface and the command line name servers from the same lists."""

import re
from pathlib import Path

from qibocal_report import config

NAMES_JS = Path(__file__).resolve().parent.parent / "frontend" / "src" / "utils" / "names.js"


def javascript_list(name: str) -> list[str]:
    source = NAMES_JS.read_text(encoding="utf-8")
    match = re.search(rf"export const {name} = \[(.*?)\]", source, re.S)
    assert match, f"{name} not found in {NAMES_JS}"
    return re.findall(r"'([^']+)'", match.group(1))


def test_the_frontend_lists_match_the_command_line_ones():
    assert javascript_list("ADJECTIVES") == config.ADJECTIVES
    assert javascript_list("SCIENTISTS") == config.SCIENTISTS
