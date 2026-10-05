"""Install the repo's plugins through the Claude Code and Codex plugin CLIs."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MARKETPLACE = "kicklabs"
AGENTS = ("claude", "codex")


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: str = ""
    stderr: str = ""


Runner = Callable[[list[str], Path | None], Result]


def system_runner(argv: list[str], cwd: Path | None) -> Result:
    if shutil.which(argv[0]) is None:
        return Result(127, stderr=f"{argv[0]}: not found")
    try:
        done = subprocess.run(
            argv, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600
        )
    except subprocess.TimeoutExpired:
        return Result(124, stderr=f"{' '.join(argv)}: timed out")
    return Result(done.returncode, done.stdout, done.stderr)


@dataclass(frozen=True)
class Step:
    agent: str
    subject: str
    outcome: str

    @property
    def ok(self) -> bool:
        return self.outcome in ("added", "installed", "present", "updated")


def plugin_id(name: str) -> str:
    return f"{name}@{MARKETPLACE}"


def _failed(agent: str, subject: str, result: Result) -> Step:
    if result.returncode == 127:
        return Step(agent, subject, f"skipped: {agent} not found")
    if result.returncode == 0:
        return Step(agent, subject, "failed: unreadable output")
    detail = (result.stderr or result.stdout).strip().splitlines()
    return Step(
        agent, subject, "failed: " + (detail[-1] if detail else f"exit {result.returncode}")
    )


def _parse(result: Result) -> Any:
    try:
        return json.loads(result.stdout)
    except ValueError:
        return None


def _conflict(agent: str, registered: str, source: Path) -> Step:
    outcome = f"failed: registered from {registered}, not {source}; remove it to use the clone"
    return Step(agent, f"marketplace {MARKETPLACE}", outcome)


def _same(path: str | None, source: Path) -> bool:
    return path is not None and Path(path).resolve() == source.resolve()


def _step(agent: str, subject: str, result: Result, success: str) -> Step:
    return (
        Step(agent, subject, success) if not result.returncode else _failed(agent, subject, result)
    )


def ensure(
    agent: str, ids: list[str], source: Path, project: Path | None, run: Runner
) -> list[Step]:
    """Add the marketplace and install each plugin, skipping what is already there."""
    if agent == "claude":
        return _ensure_claude(ids, source, project, run)
    return _ensure_codex(ids, source, run)


def _ensure_claude(ids: list[str], source: Path, project: Path | None, run: Runner) -> list[Step]:
    subject = f"marketplace {MARKETPLACE}"
    listed = run(["claude", "plugin", "marketplace", "list", "--json"], project)
    markets = _parse(listed)
    if listed.returncode or not isinstance(markets, list):
        return [_failed("claude", subject, listed)]
    steps = []
    market = next((m for m in markets if m.get("name") == MARKETPLACE), None)
    if market is None:
        added = run(["claude", "plugin", "marketplace", "add", str(source)], project)
        if added.returncode:
            return [_failed("claude", subject, added)]
        steps.append(Step("claude", subject, "added"))
    elif not _same(market.get("path"), source):
        where = (
            market.get("repo") or market.get("url") or market.get("path") or market.get("source")
        )
        return [_conflict("claude", str(where), source)]

    listed = run(["claude", "plugin", "list", "--json"], project)
    installed = _parse(listed)
    if listed.returncode or not isinstance(installed, list):
        return [*steps, _failed("claude", "plugins", listed)]
    scope = "user" if project is None else "project"
    present = {
        p.get("id")
        for p in installed
        if p.get("scope") == scope and (project is None or p.get("projectPath") == str(project))
    }
    for pid in ids:
        if pid in present:
            steps.append(Step("claude", pid, "present"))
            continue
        done = run(["claude", "plugin", "install", pid, "--scope", scope], project)
        steps.append(_step("claude", pid, done, "installed"))
    return steps


def _ensure_codex(ids: list[str], source: Path, run: Runner) -> list[Step]:
    subject = f"marketplace {MARKETPLACE}"
    listed = run(["codex", "plugin", "marketplace", "list"], None)
    if listed.returncode:
        return [_failed("codex", subject, listed)]
    roots = {
        cols[0]: cols[1]
        for cols in (line.split(None, 1) for line in listed.stdout.splitlines())
        if len(cols) == 2
    }
    steps = []
    if MARKETPLACE not in roots:
        added = run(["codex", "plugin", "marketplace", "add", str(source)], None)
        if added.returncode:
            return [_failed("codex", subject, added)]
        steps.append(Step("codex", subject, "added"))
    elif not _same(roots[MARKETPLACE].strip(), source):
        return [_conflict("codex", roots[MARKETPLACE].strip(), source)]

    listed = run(["codex", "plugin", "list", "--json"], None)
    installed = _parse(listed)
    if listed.returncode or not isinstance(installed, dict):
        return [*steps, _failed("codex", "plugins", listed)]
    present = {p.get("pluginId") for p in installed.get("installed", [])}
    for pid in ids:
        if pid in present:
            steps.append(Step("codex", pid, "present"))
            continue
        done = run(["codex", "plugin", "add", pid], None)
        steps.append(_step("codex", pid, done, "installed"))
    return steps


def update(agent: str, ids: list[str], run: Runner) -> list[Step]:
    """Pick up the pulled clone: Claude re-reads its marketplace; Codex re-copies its cache."""
    steps = []
    for pid in ids:
        if agent == "claude":
            argv = ["claude", "plugin", "update", pid]
        else:
            # `codex plugin marketplace upgrade` only refreshes Git marketplaces; adding again
            # re-copies a local one.
            argv = ["codex", "plugin", "add", pid]
        done = run(argv, None)
        steps.append(_step(agent, pid, done, "updated"))
    return steps
