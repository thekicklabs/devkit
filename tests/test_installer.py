import json
from pathlib import Path

import pytest

from devkit import installer, managed


def _req(home, project, agents, scope="local", skills=("plan",), stacks=()):
    return installer.Request(
        scope=scope,
        agents=list(agents),
        skills=list(skills),
        stacks=list(stacks),
        home=home,
        project=project if scope == "local" else None,
    )


def test_local_install_writes_every_target_path(catalog, home, project):
    report = installer.install(catalog, _req(home, project, ["claude", "codex", "cursor"]))
    expected = [
        project / "AGENTS.md",
        project / "CLAUDE.md",
        project / ".cursor" / "rules" / "devkit.mdc",
        project / ".claude" / "skills" / "plan" / "SKILL.md",
        project / ".agents" / "skills" / "plan" / "SKILL.md",
        project / ".cursor" / "skills" / "plan" / "SKILL.md",
        project / "AGENTS" / "workflow.md",
        project / "AGENTS" / "project.md",
    ]
    for p in expected:
        assert p.exists(), p
    written = {w.path for w in report.written}
    assert set(expected) <= written

    manifest = json.loads(installer.manifest_path(home).read_text())
    entry = manifest["installs"][str(project)]
    assert set(map(Path, entry["files"])) >= set(expected)
    assert entry["agents"] == ["claude", "codex", "cursor"]
    assert manifest["last"]["scope"] == "local"

    router = managed.extract((project / "AGENTS.md").read_text())
    assert router is not None
    assert "`AGENTS/workflow.md`" in router
    assert "AGENTS/project.md" in router
    assert managed.extract((project / "CLAUDE.md").read_text()) == "@AGENTS.md"


def test_reinstall_keeps_user_content_and_project_stub(catalog, home, project):
    (project / "AGENTS.md").write_text("# My notes\n\nkeep me\n")
    installer.install(catalog, _req(home, project, ["codex"]))
    (project / "AGENTS" / "project.md").write_text("custom\n")
    installer.install(catalog, _req(home, project, ["codex"]))
    text = (project / "AGENTS.md").read_text()
    assert text.startswith("# My notes\n\nkeep me\n")
    assert text.count(managed.START) == 1
    assert (project / "AGENTS" / "project.md").read_text() == "custom\n"


def test_global_install_paths(catalog, home, project):
    installer.install(catalog, _req(home, project, ["claude", "codex"], scope="global"))
    for p in (
        home / ".claude" / "CLAUDE.md",
        home / ".codex" / "AGENTS.md",
        home / ".claude" / "skills" / "plan" / "SKILL.md",
        home / ".agents" / "skills" / "plan" / "SKILL.md",
        home / ".agents" / "AGENTS" / "workflow.md",
    ):
        assert p.exists(), p
    assert not (home / ".agents" / "AGENTS" / "project.md").exists()
    router = managed.extract((home / ".claude" / "CLAUDE.md").read_text())
    assert router is not None
    assert "~/.agents/AGENTS/workflow.md" in router
    assert "This project" not in router


def test_cursor_has_no_global_scope(catalog, home, project):
    with pytest.raises(ValueError):
        installer.install(catalog, _req(home, project, ["cursor"], scope="global"))


def test_stack_requires_are_installed_and_routed(catalog, home, project):
    names = {s.name for s in catalog.by_kind("stack")}
    if "fastapi" not in names:
        pytest.skip("stacks not written yet")
    report = installer.install(catalog, _req(home, project, ["codex"], stacks=["fastapi"]))
    assert report.stacks == ["python", "fastapi"]
    assert (project / "AGENTS" / "python" / "AGENTS.md").exists()
    assert (project / "AGENTS" / "fastapi" / "AGENTS.md").exists()
    assert not (project / "AGENTS" / "fastapi" / "AGENTS.md").read_text().startswith("---")
    router = managed.extract((project / "AGENTS.md").read_text())
    assert router is not None
    assert "`AGENTS/python/AGENTS.md`" in router
    assert "`AGENTS/fastapi/AGENTS.md`" in router


def test_refresh_restores_recorded_installs_and_reports_changes(catalog, home, project):
    installer.install(catalog, _req(home, project, ["claude"]))
    installer.install(catalog, _req(home, project, ["codex"], scope="global"))
    tampered = project / ".claude" / "skills" / "plan" / "SKILL.md"
    tampered.write_text("edited by hand\n")
    deleted = home / ".agents" / "AGENTS" / "workflow.md"
    deleted.unlink()

    outcomes = {o.root: o for o in installer.refresh(catalog, home)}

    local, global_ = outcomes[str(project)], outcomes["global"]
    assert local.changed == [tampered]
    assert local.unchanged > 0
    assert global_.changed == [deleted]
    assert (
        tampered.read_text() == catalog.get("skill", "plan").path.joinpath("SKILL.md").read_text()
    )
    assert deleted.exists()


def test_refresh_skips_missing_project_and_reports_unknown_items(catalog, home, project):
    installer.install(catalog, _req(home, project, ["claude"]))
    manifest = json.loads(installer.manifest_path(home).read_text())
    manifest["installs"]["/nowhere/gone"] = {"scope": "local", "agents": ["claude"], "files": {}}
    manifest["installs"][str(project)]["skills"].append("renamed-away")
    installer.manifest_path(home).write_text(json.dumps(manifest))

    outcomes = {o.root: o for o in installer.refresh(catalog, home)}

    assert outcomes["/nowhere/gone"].skipped == "project directory missing"
    assert outcomes["/nowhere/gone"].error is None
    assert "renamed-away" in (outcomes[str(project)].error or "")
