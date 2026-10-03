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
    "fable": r"(?i)fable",
    "astra": r"(?i)astra",
    "xhigh": r"xhigh",
    "@max": r"@max",
    "haiku": r"(?i)haiku",
    "readonly: true": r"readonly`?:\s*`?true",
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


LINK = re.compile(r"\]\(([^)\s]+)\)")
SKILL_MENTION = re.compile(
    r"`/?([a-z][a-z0-9-]*)` skill\b|\*\*([a-z][a-z0-9-]*)\*\* skill\b|`/([a-z][a-z0-9-]*)`"
)
NAMESPACED = re.compile(r"\bkick:([a-z][a-z0-9-]*)")
BUILT_IN = {"run", "loop", "verify", "hooks"}


def _markdown() -> list[Path]:
    return [p for p in _content() if p.suffix == ".md"]


def _slug(heading: str) -> str:
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def _anchors(path: Path) -> set[str]:
    return {
        _slug(line.lstrip("#"))
        for line in path.read_text().splitlines()
        if re.match(r"#{1,6} ", line)
    }


def _skills() -> set[str]:
    return {p.parent.name for p in KICK.glob("skills/*/SKILL.md")}


def _agents() -> set[str]:
    return {p.stem for p in KICK.glob("agents/*.md")}


def test_relative_links_resolve():
    broken = []
    for md in _markdown():
        for target in LINK.findall(md.read_text()):
            if re.match(r"[a-z]+:", target):
                continue
            path, _, anchor = target.partition("#")
            dest = (md.parent / path).resolve() if path else md
            if not dest.exists():
                broken.append(f"{md.relative_to(KICK)} -> {target}")
            elif anchor and dest.suffix == ".md" and anchor not in _anchors(dest):
                broken.append(f"{md.relative_to(KICK)} -> {target} (no anchor)")
    assert not broken, broken


def test_skill_mentions_resolve():
    known = _skills() | BUILT_IN
    unknown = []
    for md in _markdown():
        text = md.read_text()
        for groups in SKILL_MENTION.findall(text):
            name = next(g for g in groups if g)
            if name not in known:
                unknown.append(f"{md.relative_to(KICK)}: {name}")
        for name in NAMESPACED.findall(text):
            if name not in _skills() | _agents():
                unknown.append(f"{md.relative_to(KICK)}: kick:{name}")
    assert not unknown, unknown


def test_route_table_targets_exist():
    router = (KICK / "skills" / "kick-mode" / "SKILL.md").read_text()
    table = router.split("## Route", 1)[1].split("\n## ", 1)[0]
    rows = [line.rsplit("|", 2)[1] for line in table.splitlines() if line.startswith("| ")]
    named = {n for cell in rows for n in re.findall(r"`([a-z][a-z0-9-]*)`", cell)}
    assert named, "route table has no skill names"
    assert named <= _skills(), named - _skills()
