import re
from pathlib import Path

import pytest

KICK = Path(__file__).resolve().parents[1] / "plugins" / "kick"
PROVENANCE = {"NOTICE.md", "LICENSE-pstack", "LICENSE-cursor-team-kit"}

BANNED = {
    "poteto": r"poteto",
    "pstack:": r"pstack:",
    "Bugbot": r"(?i)bugbot",
    "origin pr": r"\borigin pr\b",
    "gt ": r"\bgt ",
}


def _content() -> list[Path]:
    return sorted(p for p in KICK.rglob("*") if p.is_file() and p.name not in PROVENANCE)


@pytest.mark.parametrize("token", sorted(BANNED))
def test_no_banned_tokens(token: str):
    pattern = re.compile(BANNED[token])
    hits = [
        f"{p.relative_to(KICK)}:{n}"
        for p in _content()
        for n, line in enumerate(p.read_text().splitlines(), 1)
        if pattern.search(line)
    ]
    assert not hits, hits
