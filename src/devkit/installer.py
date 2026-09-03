from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

from devkit import frontmatter, managed, targets
from devkit.catalog import Catalog
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


def _copy_tree(src: Path, dst: Path, report: Report, what: str) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    for p in sorted(dst.rglob("*")):
        if p.is_file():
            report.add(p, what)


def _write(path: Path, text: str, report: Report, what: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    report.add(path, what)


def install(catalog: Catalog, req: Request) -> Report:
    if req.scope == "local" and req.project is None:
        raise ValueError("local scope needs a project path")
    for agent in req.agents:
        if not targets.supports(agent, req.scope):
            raise ValueError(f"{agent} has no file-based {req.scope} scope")

    report = Report()
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

    for skill in req.skills:
        catalog.get("skill", skill)
    for tgt in targets.targets(req.agents, req.scope, req.home, req.project):
        for skill in req.skills:
            item = catalog.get("skill", skill)
            _copy_tree(item.path, tgt.skills_dir / skill, report, f"skills → {tgt.agent}")

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

    _record(req, report)
    return report


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_path(home: Path) -> Path:
    return config_dir(home) / MANIFEST


def read_manifest(home: Path) -> dict:
    path = manifest_path(home)
    if not path.exists():
        return {"installs": {}, "last": None}
    return json.loads(path.read_text())


def _record(req: Request, report: Report) -> None:
    data = read_manifest(req.home)
    entry = data["installs"].get(req.root_key, {"files": {}})
    files = dict(entry.get("files", {}))
    for w in report.written:
        files[str(w.path)] = _sha256(w.path)
    data["installs"][req.root_key] = {
        "scope": req.scope,
        "agents": sorted(set(entry.get("agents", [])) | set(req.agents)),
        "skills": sorted(set(entry.get("skills", [])) | set(req.skills)),
        "stacks": sorted(set(entry.get("stacks", [])) | set(report.stacks)),
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
