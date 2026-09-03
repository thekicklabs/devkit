"""Where each agent expects skills and its router, per scope. Pure data; nothing is written here."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

AGENTS = ("claude", "codex", "cursor")
SCOPES = ("global", "local")

# inline: the rendered router lives inside a managed block in this file.
# import: the managed block only imports ./AGENTS.md (Claude's `@file` syntax).
# mdc:    Cursor rule file, written whole, pointing the agent at ./AGENTS.md.
ROUTER_STYLES = ("inline", "import", "mdc")


@dataclass(frozen=True)
class Router:
    path: Path
    style: str


@dataclass(frozen=True)
class Target:
    agent: str
    scope: str
    skills_dir: Path
    routers: tuple[Router, ...]


def rules_dir(scope: str, home: Path, project: Path | None) -> Path:
    if scope == "global":
        return home / ".agents" / "AGENTS"
    assert project is not None
    return project / "AGENTS"


def rules_link(scope: str) -> str:
    """Prefix used in rendered links; global links must resolve from any cwd."""
    return "~/.agents/AGENTS/" if scope == "global" else "AGENTS/"


def supports(agent: str, scope: str) -> bool:
    return not (agent == "cursor" and scope == "global")


def target(agent: str, scope: str, home: Path, project: Path | None) -> Target:
    if not supports(agent, scope):
        raise ValueError(f"{agent} has no file-based {scope} scope")
    if scope == "global":
        if agent == "claude":
            return Target(
                agent,
                scope,
                home / ".claude" / "skills",
                (Router(home / ".claude" / "CLAUDE.md", "inline"),),
            )
        if agent == "codex":
            return Target(
                agent,
                scope,
                home / ".agents" / "skills",
                (Router(home / ".codex" / "AGENTS.md", "inline"),),
            )
    assert project is not None
    shared = Router(project / "AGENTS.md", "inline")
    if agent == "claude":
        return Target(
            agent,
            scope,
            project / ".claude" / "skills",
            (shared, Router(project / "CLAUDE.md", "import")),
        )
    if agent == "codex":
        return Target(agent, scope, project / ".agents" / "skills", (shared,))
    return Target(
        agent,
        scope,
        project / ".cursor" / "skills",
        (shared, Router(project / ".cursor" / "rules" / "devkit.mdc", "mdc")),
    )


def targets(agents: list[str], scope: str, home: Path, project: Path | None) -> list[Target]:
    return [target(a, scope, home, project) for a in agents]
