"""Install the repo's plugins through the Claude Code and Codex plugin CLIs."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

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
    done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
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
    detail = (result.stderr or result.stdout).strip().splitlines()
    return Step(
        agent, subject, "failed: " + (detail[-1] if detail else f"exit {result.returncode}")
    )


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
    listed = run(["claude", "plugin", "marketplace", "list", "--json"], project)
    if listed.returncode:
        return [_failed("claude", f"marketplace {MARKETPLACE}", listed)]
    steps = []
    if MARKETPLACE not in {m.get("name") for m in json.loads(listed.stdout or "[]")}:
        added = run(["claude", "plugin", "marketplace", "add", str(source)], project)
        if added.returncode:
            return [_failed("claude", f"marketplace {MARKETPLACE}", added)]
        steps.append(Step("claude", f"marketplace {MARKETPLACE}", "added"))

    plugins = run(["claude", "plugin", "list", "--json"], project)
    if plugins.returncode:
        return [*steps, _failed("claude", "plugins", plugins)]
    scope = "user" if project is None else "project"
    present = {
        p.get("id")
        for p in json.loads(plugins.stdout or "[]")
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
    listed = run(["codex", "plugin", "marketplace", "list"], None)
    if listed.returncode:
        return [_failed("codex", f"marketplace {MARKETPLACE}", listed)]
    steps = []
    if not any(line.split()[:1] == [MARKETPLACE] for line in listed.stdout.splitlines()):
        added = run(["codex", "plugin", "marketplace", "add", str(source)], None)
        if added.returncode:
            return [_failed("codex", f"marketplace {MARKETPLACE}", added)]
        steps.append(Step("codex", f"marketplace {MARKETPLACE}", "added"))

    plugins = run(["codex", "plugin", "list", "--json"], None)
    if plugins.returncode:
        return [*steps, _failed("codex", "plugins", plugins)]
    present = {p.get("pluginId") for p in json.loads(plugins.stdout or "{}").get("installed", [])}
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
