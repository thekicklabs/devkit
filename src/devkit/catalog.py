from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from devkit import frontmatter

KINDS = ("skill", "stack", "rule", "machine")


@dataclass(frozen=True)
class Item:
    kind: str
    name: str
    description: str
    path: Path
    body: str
    tags: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    files: tuple[Path, ...] = field(default=())

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.name}"


class UnknownItem(KeyError):
    pass


@dataclass
class Catalog:
    root: Path
    items: list[Item]

    def by_kind(self, kind: str) -> list[Item]:
        return [i for i in self.items if i.kind == kind]

    def get(self, kind: str, name: str) -> Item:
        for item in self.items:
            if item.kind == kind and item.name == name:
                return item
        raise UnknownItem(f"{kind} '{name}' not found")

    def find(self, name: str) -> Item:
        """Resolve a bare name against skills then stacks, the two installable kinds."""
        for kind in ("skill", "stack"):
            try:
                return self.get(kind, name)
            except UnknownItem:
                continue
        raise UnknownItem(f"no skill or stack named '{name}'")

    def resolve_stacks(self, names: list[str]) -> list[str]:
        """Expand `requires` transitively; dependencies come before dependents."""
        ordered: list[str] = []

        def visit(name: str, trail: tuple[str, ...]) -> None:
            if name in ordered:
                return
            if name in trail:
                raise ValueError(f"stack requires cycle: {' -> '.join(trail + (name,))}")
            for dep in self.get("stack", name).requires:
                visit(dep, trail + (name,))
            ordered.append(name)

        for name in names:
            visit(name, ())
        return ordered


def load(root: Path) -> Catalog:
    items: list[Item] = []
    items += _skills(root / "skills")
    items += _stacks(root / "stacks")
    items += _rules(root / "rules")
    items += _machine(root / "machine")
    return Catalog(root=root, items=items)


def _as_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(v) for v in value)
    if isinstance(value, str) and value:
        return (value,)
    return ()


def _skills(base: Path) -> list[Item]:
    out = []
    for skill_md in sorted(base.glob("*/SKILL.md")):
        meta, body = frontmatter.split(skill_md.read_text())
        name = str(meta.get("name") or skill_md.parent.name)
        out.append(
            Item(
                kind="skill",
                name=name,
                description=str(meta.get("description", "")),
                path=skill_md.parent,
                body=body,
                tags=_as_tuple(meta.get("tags")),
                files=tuple(sorted(p for p in skill_md.parent.rglob("*") if p.is_file())),
            )
        )
    return out


def _stacks(base: Path) -> list[Item]:
    out = []
    for agents_md in sorted(base.glob("*/AGENTS.md")):
        meta, _ = frontmatter.split(agents_md.read_text())
        files = tuple(sorted(p for p in agents_md.parent.rglob("*.md")))
        body = "\n".join(frontmatter.strip(p.read_text()) for p in files)
        out.append(
            Item(
                kind="stack",
                name=str(meta.get("name") or agents_md.parent.name),
                description=str(meta.get("description", "")),
                path=agents_md.parent,
                body=body,
                tags=_as_tuple(meta.get("tags")),
                requires=_as_tuple(meta.get("requires")),
                files=files,
            )
        )
    return out


_READ_WHEN = re.compile(r"\*\*Read when:\*\*\s*(.+)")


def _rules(base: Path) -> list[Item]:
    out = []
    for md in sorted(base.glob("*.md")):
        text = md.read_text()
        m = _READ_WHEN.search(text)
        out.append(
            Item(
                kind="rule",
                name=md.stem,
                description=m.group(1).strip() if m else "",
                path=md,
                body=text,
                files=(md,),
            )
        )
    return out


_DESC = re.compile(r"^#\s*description:\s*(.+)$", re.MULTILINE)


def _machine(base: Path) -> list[Item]:
    out = []
    for sh in sorted(base.glob("[!_]*.sh")):
        text = sh.read_text()
        m = _DESC.search(text)
        name = re.sub(r"^\d+-", "", sh.stem)
        out.append(
            Item(
                kind="machine",
                name=name,
                description=m.group(1).strip() if m else "",
                path=sh,
                body=text,
                files=(sh,),
            )
        )
    return out
