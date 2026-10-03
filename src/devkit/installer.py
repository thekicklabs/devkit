from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

from devkit import frontmatter, managed, plugins, targets
from devkit.catalog import Catalog, UnknownItem
from devkit.paths import config_dir

MANIFEST = "installs.json"


@dataclass
class Request:
    scope: str
    agents: list[str]
    skills: list[str]
    stacks: list[str]
    home: Path
    project: Path | None = None

    @property
    def root_key(self) -> str:
        return "global" if self.scope == "global" else str(self.project)


@dataclass
class Written:
    path: Path
    what: str


@dataclass
class Report:
    written: list[Written] = field(default_factory=list)
    stacks: list[str] = field(default_factory=list)
    steps: list[plugins.Step] = field(default_factory=list)
    pruned: list[Path] = field(default_factory=list)
    kept: list[Path] = field(default_factory=list)

    def add(self, path: Path, what: str) -> None:
        self.written.append(Written(path, what))


def _template(name: str) -> str:
    return resources.files("devkit").joinpath("templates").joinpath(name).read_text()


def render_router(catalog: Catalog, req: Request, stacks: list[str]) -> str:
    link = targets.rules_link(req.scope)
    rows = []
    for name in stacks:
        item = catalog.get("stack", name)
        meta, _ = frontmatter.split((item.path / "AGENTS.md").read_text())
        route = str(meta.get("route") or item.description or name)
        rows.append(f"| {route} | `{link}{name}/AGENTS.md` |")
    if not rows:
        rows.append("| — | no stacks installed; `devkit install --stack <name>` |")
    project = ""
    if req.scope == "local":
        project = (
            "\n## This project\n\n"
            f"`{link}project.md` — layout, environment, product rules, deliberate departures. "
            "Read it; it outranks the stack defaults."
        )
    return (
        _template("AGENTS.md.tmpl")
        .replace("{{RULES_DIR}}", link)
        .replace("{{STACKS}}", "\n".join(rows))
        .replace("{{PROJECT}}", project)
        .rstrip()
        + "\n"
    )


def _clear(path: Path) -> None:
    if path.is_symlink():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def _copy_tree(src: Path, dst: Path, report: Report, what: str) -> None:
    _clear(dst)
    shutil.copytree(src, dst)
    for p in sorted(dst.rglob("*")):
        if p.is_file():
            report.add(p, what)


def _write(path: Path, text: str, report: Report, what: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    report.add(path, what)


def install(catalog: Catalog, req: Request, run: plugins.Runner | None = None) -> Report:
    if req.scope == "local" and req.project is None:
        raise ValueError("local scope needs a project path")
    report = Report()
    entry = read_manifest(req.home)["installs"].get(req.root_key, {})
    stacks = catalog.resolve_stacks(req.stacks)
    report.stacks = stacks

    rules_dir = targets.rules_dir(req.scope, req.home, req.project)
    rules_dir.mkdir(parents=True, exist_ok=True)
    for rule in catalog.by_kind("rule"):
        _write(rules_dir / rule.path.name, rule.body, report, "rules")
    for name in stacks:
        item = catalog.get("stack", name)
        dst = rules_dir / name
        _copy_tree(item.path, dst, report, f"stack {name}")
        agents_md = dst / "AGENTS.md"
        agents_md.write_text(frontmatter.strip(agents_md.read_text()))

    for tgt in targets.targets(req.agents, req.scope, req.home, req.project):
        if tgt.skills_dir is None:
            continue
        for skill in req.skills:
            item = catalog.get("skill", skill)
            _copy_tree(item.path, tgt.skills_dir / skill, report, f"skills ({tgt.agent})")

    ids = sorted({plugins.plugin_id(catalog.get("skill", s).plugin) for s in req.skills})
    for agent in (a for a in req.agents if a in plugins.AGENTS):
        if ids:
            report.steps += plugins.ensure(
                agent, ids, catalog.root, req.project, run or plugins.system_runner
            )

    router = render_router(catalog, req, stacks)
    seen: set[Path] = set()
    for tgt in targets.targets(req.agents, req.scope, req.home, req.project):
        for r in tgt.routers:
            if r.path in seen:
                continue
            seen.add(r.path)
            existing = r.path.read_text() if r.path.exists() else ""
            if r.style == "inline":
                _write(r.path, managed.upsert(existing, router), report, "router")
            elif r.style == "import":
                _write(
                    r.path,
                    managed.upsert(existing, _template("CLAUDE.md.local")),
                    report,
                    "router (imports AGENTS.md)",
                )
            else:
                _write(r.path, _template("cursor.mdc"), report, "router (cursor rule)")

    if req.scope == "local":
        stub = rules_dir / "project.md"
        if not stub.exists():
            _write(stub, _template("project.md"), report, "project stub (created once)")

    # Old copies stay until the plugin that replaces them is in place.
    if all(step.ok for step in report.steps):
        _prune(req, entry, report)
    _record(req, entry, report)
    return report


def _owned(req: Request, agents: list[str]) -> list[Path]:
    owned = [targets.rules_dir(req.scope, req.home, req.project)]
    for tgt in targets.targets(agents, req.scope, req.home, req.project):
        if tgt.skills_dir is not None:
            owned.append(tgt.skills_dir)
        owned += [r.path for r in tgt.routers]
    return owned


def _prune(req: Request, entry: dict, report: Report) -> None:
    """Delete recorded files devkit no longer writes anywhere, unless edited or behind a link."""
    written = {w.path for w in report.written}
    owned = _owned(req, sorted(set(entry.get("agents", [])) | set(req.agents)))
    stop = req.home if req.project is None else req.project
    for raw, recorded in entry.get("files", {}).items():
        path = Path(raw)
        if path in written or any(path == o or o in path.parents for o in owned):
            continue
        if not path.is_symlink() and not path.is_file():
            continue
        linked = any(p.is_symlink() for p in path.parents if stop in p.parents)
        if linked or _fingerprint(path) != recorded:
            report.kept.append(path)
            continue
        path.unlink()
        report.pruned.append(path)
        parent = path.parent
        while parent != stop and stop in parent.parents and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent


def _fingerprint(path: Path) -> str:
    if path.is_symlink():
        return "link:" + os.readlink(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_path(home: Path) -> Path:
    return config_dir(home) / MANIFEST


def read_manifest(home: Path) -> dict:
    path = manifest_path(home)
    if not path.exists():
        return {"installs": {}, "last": None}
    return json.loads(path.read_text())


def _record(req: Request, entry: dict, report: Report) -> None:
    data = read_manifest(req.home)
    dropped = {str(p) for p in report.pruned + report.kept}
    files = {k: v for k, v in entry.get("files", {}).items() if k not in dropped}
    for w in report.written:
        files[str(w.path)] = _fingerprint(w.path)
    installed = {agent: set(ids) for agent, ids in entry.get("plugins", {}).items()}
    for step in report.steps:
        if step.ok and "@" in step.subject:
            installed.setdefault(step.agent, set()).add(step.subject)
    data["installs"][req.root_key] = {
        "scope": req.scope,
        "agents": sorted(set(entry.get("agents", [])) | set(req.agents)),
        "skills": sorted(set(entry.get("skills", [])) | set(req.skills)),
        "stacks": sorted(set(entry.get("stacks", [])) | set(report.stacks)),
        "plugins": {agent: sorted(ids) for agent, ids in sorted(installed.items())},
        "files": files,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    data["last"] = {
        "scope": req.scope,
        "agents": list(req.agents),
        "project": None if req.project is None else str(req.project),
    }
    path = manifest_path(req.home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


@dataclass
class Outcome:
    root: str
    scope: str
    changed: list[Path] = field(default_factory=list)
    unchanged: int = 0
    pruned: list[Path] = field(default_factory=list)
    kept: list[Path] = field(default_factory=list)
    steps: list[plugins.Step] = field(default_factory=list)
    skipped: str | None = None
    error: str | None = None


def refresh(catalog: Catalog, home: Path, run: plugins.Runner | None = None) -> list[Outcome]:
    """Re-copy every install the manifest records, from the current catalog."""
    outcomes: list[Outcome] = []
    for root, entry in read_manifest(home)["installs"].items():
        scope = entry["scope"]
        project = None if scope == "global" else Path(root)
        outcome = Outcome(root=root, scope=scope)
        outcomes.append(outcome)
        if project is not None and not project.is_dir():
            outcome.skipped = "project directory missing"
            continue
        req = Request(
            scope=scope,
            agents=list(entry.get("agents", [])),
            skills=list(entry.get("skills", [])),
            stacks=list(entry.get("stacks", [])),
            home=home,
            project=project,
        )
        before = {
            f: _fingerprint(Path(f))
            for f in entry.get("files", {})
            if Path(f).is_symlink() or Path(f).is_file()
        }
        try:
            report = install(catalog, req, run)
        except (UnknownItem, ValueError) as e:
            outcome.error = str(e)
            continue
        outcome.pruned, outcome.kept, outcome.steps = report.pruned, report.kept, report.steps
        for w in report.written:
            if before.get(str(w.path)) == _fingerprint(w.path):
                outcome.unchanged += 1
            else:
                outcome.changed.append(w.path)
    return outcomes


def update_plugins(home: Path, run: plugins.Runner | None = None) -> list[plugins.Step]:
    """Have each runtime pick up the pulled clone for every plugin a recorded install added."""
    recorded: dict[str, set[str]] = {}
    for entry in read_manifest(home)["installs"].values():
        for agent, ids in entry.get("plugins", {}).items():
            recorded.setdefault(agent, set()).update(ids)
    steps = []
    for agent, ids in sorted(recorded.items()):
        steps += plugins.update(agent, sorted(ids), run or plugins.system_runner)
    return steps
