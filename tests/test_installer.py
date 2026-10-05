import json
import os
from pathlib import Path

import pytest
from conftest import FakePluginCli

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


def test_local_install_writes_every_target_path(catalog, home, project, plugin_cli):
    report = installer.install(
        catalog, _req(home, project, ["claude", "codex", "cursor"]), plugin_cli
    )
    expected = [
        project / "AGENTS.md",
        project / "CLAUDE.md",
        project / ".cursor" / "rules" / "devkit.mdc",
        project / ".cursor" / "skills" / "plan" / "SKILL.md",
        project / "AGENTS" / "workflow.md",
        project / "AGENTS" / "project.md",
    ]
    for p in expected:
        assert p.exists(), p
    written = {w.path for w in report.written}
    assert set(expected) <= written
    assert not (project / ".claude" / "skills").exists()
    assert not (project / ".agents").exists()

    manifest = json.loads(installer.manifest_path(home).read_text())
    entry = manifest["installs"][str(project)]
    assert set(map(Path, entry["files"])) >= set(expected)
    assert entry["agents"] == ["claude", "codex", "cursor"]
    assert entry["plugins"] == {"claude": ["kick@kicklabs"], "codex": ["kick@kicklabs"]}
    assert manifest["last"]["scope"] == "local"

    router = managed.extract((project / "AGENTS.md").read_text())
    assert router is not None
    assert "`AGENTS/workflow.md`" in router
    assert "AGENTS/project.md" in router
    assert "`kick-mode`" in router and "`interrogate`" in router
    assert managed.extract((project / "CLAUDE.md").read_text()) == "@AGENTS.md"


def test_plugins_install_through_each_cli(catalog, home, project, plugin_cli):
    installer.install(catalog, _req(home, project, ["claude", "codex"]), plugin_cli)
    source = str(catalog.root)
    assert plugin_cli.ran("claude", "plugin", "marketplace", "add", source) == [project]
    assert plugin_cli.ran("claude", "plugin", "install", "kick@kicklabs", "--scope", "project") == [
        project
    ]
    assert plugin_cli.ran("codex", "plugin", "marketplace", "add", source) == [None]
    assert plugin_cli.ran("codex", "plugin", "add", "kick@kicklabs") == [None]


def test_plugin_install_is_idempotent(catalog, home, project, plugin_cli):
    installer.install(catalog, _req(home, project, ["claude", "codex"]), plugin_cli)
    report = installer.install(catalog, _req(home, project, ["claude", "codex"]), plugin_cli)
    assert {s.outcome for s in report.steps} == {"present"}
    assert len(plugin_cli.ran("claude", "plugin", "marketplace", "add", str(catalog.root))) == 1
    assert len(plugin_cli.ran("codex", "plugin", "add", "kick@kicklabs")) == 1


def test_global_scope_installs_user_plugins(catalog, home, project, plugin_cli):
    installer.install(catalog, _req(home, project, ["claude"], scope="global"), plugin_cli)
    assert plugin_cli.ran("claude", "plugin", "install", "kick@kicklabs", "--scope", "user") == [
        None
    ]


def test_plugins_follow_the_selected_skills(catalog, home, project, plugin_cli):
    req = _req(home, project, ["codex"], skills=("store-orchestrator",))
    installer.install(catalog, req, plugin_cli)
    assert plugin_cli.codex_plugins == {"store@kicklabs"}
    plugin_cli.calls.clear()
    installer.install(catalog, _req(home, project, ["codex"], skills=()), plugin_cli)
    assert plugin_cli.calls == []


def test_missing_or_failing_cli_is_reported_not_fatal(catalog, home, project):
    cli = FakePluginCli(missing=("claude",), failing=("codex plugin add kick@kicklabs",))
    report = installer.install(catalog, _req(home, project, ["claude", "codex"]), cli)
    outcomes = {(s.agent, s.subject): s.outcome for s in report.steps}
    assert outcomes[("claude", "marketplace kicklabs")] == "skipped: claude not found"
    assert outcomes[("codex", "kick@kicklabs")] == "failed: boom"
    assert (project / "AGENTS" / "workflow.md").exists()
    entry = json.loads(installer.manifest_path(home).read_text())["installs"][str(project)]
    assert entry["plugins"] == {}


def test_reinstall_keeps_user_content_and_project_stub(catalog, home, project, plugin_cli):
    (project / "AGENTS.md").write_text("# My notes\n\nkeep me\n")
    installer.install(catalog, _req(home, project, ["codex"]), plugin_cli)
    (project / "AGENTS" / "project.md").write_text("custom\n")
    installer.install(catalog, _req(home, project, ["codex"]), plugin_cli)
    text = (project / "AGENTS.md").read_text()
    assert text.startswith("# My notes\n\nkeep me\n")
    assert text.count(managed.START) == 1
    assert (project / "AGENTS" / "project.md").read_text() == "custom\n"


def test_global_install_paths(catalog, home, project, plugin_cli):
    installer.install(catalog, _req(home, project, ["claude", "codex"], scope="global"), plugin_cli)
    for p in (
        home / ".claude" / "CLAUDE.md",
        home / ".codex" / "AGENTS.md",
        home / ".agents" / "AGENTS" / "workflow.md",
    ):
        assert p.exists(), p
    assert not (home / ".claude" / "skills").exists()
    assert not (home / ".agents" / "skills").exists()
    assert not (home / ".agents" / "AGENTS" / "project.md").exists()
    router = managed.extract((home / ".claude" / "CLAUDE.md").read_text())
    assert router is not None
    assert "~/.agents/AGENTS/workflow.md" in router
    assert "This project" not in router


def test_cursor_global_is_skills_only(catalog, home, project, plugin_cli):
    report = installer.install(catalog, _req(home, project, ["cursor"], scope="global"), plugin_cli)
    assert (home / ".cursor" / "skills" / "plan" / "SKILL.md").exists()
    assert not (home / ".agents" / "skills").exists()
    assert not any(w.what.startswith("router") for w in report.written)
    assert plugin_cli.calls == []


def test_stack_requires_are_installed_and_routed(catalog, home, project, plugin_cli):
    names = {s.name for s in catalog.by_kind("stack")}
    if "fastapi" not in names:
        pytest.skip("stacks not written yet")
    report = installer.install(
        catalog, _req(home, project, ["codex"], stacks=["fastapi"]), plugin_cli
    )
    assert report.stacks == ["python", "fastapi"]
    assert (project / "AGENTS" / "python" / "AGENTS.md").exists()
    assert (project / "AGENTS" / "fastapi" / "AGENTS.md").exists()
    assert not (project / "AGENTS" / "fastapi" / "AGENTS.md").read_text().startswith("---")
    router = managed.extract((project / "AGENTS.md").read_text())
    assert router is not None
    assert "`AGENTS/python/AGENTS.md`" in router
    assert "`AGENTS/fastapi/AGENTS.md`" in router


def test_refresh_restores_recorded_installs_and_reports_changes(catalog, home, project, plugin_cli):
    installer.install(catalog, _req(home, project, ["cursor"]), plugin_cli)
    installer.install(catalog, _req(home, project, ["codex"], scope="global"), plugin_cli)
    tampered = project / ".cursor" / "skills" / "plan" / "SKILL.md"
    tampered.write_text("edited by hand\n")
    deleted = home / ".agents" / "AGENTS" / "workflow.md"
    deleted.unlink()

    outcomes = {o.root: o for o in installer.refresh(catalog, home, plugin_cli)}

    local, global_ = outcomes[str(project)], outcomes["global"]
    assert local.changed == [tampered]
    assert local.unchanged > 0
    assert global_.changed == [deleted]
    assert (
        tampered.read_text() == catalog.get("skill", "plan").path.joinpath("SKILL.md").read_text()
    )
    assert deleted.exists()


def test_refresh_skips_missing_project_and_reports_unknown_items(
    catalog, home, project, plugin_cli
):
    installer.install(catalog, _req(home, project, ["cursor"]), plugin_cli)
    manifest = json.loads(installer.manifest_path(home).read_text())
    manifest["installs"]["/nowhere/gone"] = {"scope": "local", "agents": ["claude"], "files": {}}
    manifest["installs"][str(project)]["skills"].append("renamed-away")
    installer.manifest_path(home).write_text(json.dumps(manifest))

    outcomes = {o.root: o for o in installer.refresh(catalog, home, plugin_cli)}

    assert outcomes["/nowhere/gone"].skipped == "project directory missing"
    assert outcomes["/nowhere/gone"].error is None
    assert "renamed-away" in (outcomes[str(project)].error or "")


def test_update_plugins_refreshes_every_recorded_plugin(catalog, home, project, plugin_cli):
    installer.install(catalog, _req(home, project, ["claude", "codex"]), plugin_cli)
    installer.install(
        catalog, _req(home, project, ["codex"], scope="global", skills=("store-orchestrator",)),
        plugin_cli,
    )  # fmt: skip
    plugin_cli.calls.clear()
    steps = installer.update_plugins(home, plugin_cli)
    assert [(s.agent, s.subject, s.outcome) for s in steps] == [
        ("claude", "kick@kicklabs", "updated"),
        ("codex", "kick@kicklabs", "updated"),
        ("codex", "store@kicklabs", "updated"),
    ]
    assert plugin_cli.ran("claude", "plugin", "update", "kick@kicklabs") == [None]
    assert plugin_cli.ran("codex", "plugin", "add", "store@kicklabs") == [None]


def _legacy_global(home: Path) -> dict[str, str]:
    """What an earlier devkit wrote: a real copy in ~/.agents/skills, Claude links to it."""
    copy = home / ".agents" / "skills" / "plan"
    (copy / "references").mkdir(parents=True)
    (copy / "SKILL.md").write_text("old plan\n")
    (copy / "references" / "note.md").write_text("note\n")
    edited = home / ".agents" / "skills" / "tdd" / "SKILL.md"
    edited.parent.mkdir()
    edited.write_text("old tdd\n")
    link = home / ".claude" / "skills" / "plan"
    link.parent.mkdir(parents=True)
    link.symlink_to("../../.agents/skills/plan", target_is_directory=True)
    files = {
        str(copy / "SKILL.md"): installer._fingerprint(copy / "SKILL.md"),
        str(copy / "references" / "note.md"): installer._fingerprint(
            copy / "references" / "note.md"
        ),
        str(edited): installer._fingerprint(edited),
        str(link): installer._fingerprint(link),
    }
    edited.write_text("old tdd, edited by the user\n")
    return files


def test_install_prunes_recorded_copies_devkit_no_longer_writes(catalog, home, plugin_cli):
    files = _legacy_global(home)
    foreign = home / ".agents" / "skills" / "find-skills" / "SKILL.md"
    foreign.parent.mkdir()
    foreign.write_text("not devkit's\n")
    manifest = {
        "installs": {
            "global": {
                "scope": "global",
                "agents": ["claude", "codex"],
                "skills": ["plan", "tdd"],
                "stacks": [],
                "files": files,
            }
        },
        "last": None,
    }
    installer.manifest_path(home).parent.mkdir(parents=True)
    installer.manifest_path(home).write_text(json.dumps(manifest))

    outcomes = {o.root: o for o in installer.refresh(catalog, home, plugin_cli)}

    pruned = outcomes["global"].pruned
    assert sorted(map(str, pruned)) == sorted(k for k in files if "tdd" not in k)
    assert not (home / ".agents" / "skills" / "plan").exists()
    assert not (home / ".claude" / "skills").exists()
    assert outcomes["global"].kept == [home / ".agents" / "skills" / "tdd" / "SKILL.md"]
    assert (home / ".agents" / "skills" / "tdd" / "SKILL.md").exists()
    assert foreign.exists()
    recorded = json.loads(installer.manifest_path(home).read_text())["installs"]["global"]
    assert not any(".agents/skills" in f or ".claude/skills" in f for f in recorded["files"])


def test_partial_install_keeps_other_current_copies(catalog, home, project, plugin_cli):
    installer.install(catalog, _req(home, project, ["cursor"], skills=("plan", "tdd")), plugin_cli)
    report = installer.install(
        catalog, _req(home, project, ["cursor"], skills=("tdd",)), plugin_cli
    )
    assert report.pruned == [] and report.kept == []
    assert (project / ".cursor" / "skills" / "plan" / "SKILL.md").exists()
    assert os.path.isdir(project / ".cursor" / "skills" / "tdd")


def _write_manifest(home: Path, files: dict[str, str], agents=("claude", "codex")) -> None:
    manifest = {
        "installs": {
            "global": {
                "scope": "global",
                "agents": list(agents),
                "skills": ["plan", "tdd"],
                "stacks": [],
                "files": files,
            }
        },
        "last": None,
    }
    installer.manifest_path(home).parent.mkdir(parents=True, exist_ok=True)
    installer.manifest_path(home).write_text(json.dumps(manifest))


@pytest.mark.parametrize(
    "cli",
    [FakePluginCli(missing=("codex",)), FakePluginCli(failing=("codex plugin add kick@kicklabs",))],
    ids=["missing", "failing"],
)
def test_old_copies_stay_until_the_plugin_is_in_place(catalog, home, cli):
    files = _legacy_global(home)
    _write_manifest(home, files)

    (outcome,) = installer.refresh(catalog, home, cli)

    assert outcome.pruned == []
    assert (home / ".agents" / "skills" / "plan" / "SKILL.md").exists()
    assert (home / ".claude" / "skills" / "plan").is_symlink()
    recorded = json.loads(installer.manifest_path(home).read_text())["installs"]["global"]
    assert set(files) <= set(recorded["files"])


def test_prune_never_follows_a_linked_directory(catalog, home, plugin_cli, tmp_path):
    elsewhere = tmp_path / "elsewhere" / "plan"
    elsewhere.mkdir(parents=True)
    (elsewhere / "SKILL.md").write_text("old plan\n")
    recorded = home / ".agents" / "skills" / "plan" / "SKILL.md"
    recorded.parent.parent.mkdir(parents=True)
    recorded.parent.symlink_to(elsewhere, target_is_directory=True)
    _write_manifest(home, {str(recorded): installer._fingerprint(recorded)})

    (outcome,) = installer.refresh(catalog, home, plugin_cli)

    assert outcome.pruned == [] and outcome.kept == [recorded]
    assert (elsewhere / "SKILL.md").exists()


def test_a_marketplace_from_another_source_is_a_conflict(catalog, home, project, plugin_cli):
    plugin_cli.markets["codex"]["kicklabs"] = "/somewhere/else"
    report = installer.install(catalog, _req(home, project, ["codex"]), plugin_cli)
    (step,) = report.steps
    assert step.outcome.startswith("failed: registered from /somewhere/else")
    assert plugin_cli.ran("codex", "plugin", "add", "kick@kicklabs") == []


def test_unreadable_cli_output_is_a_failed_step(catalog, home, project):
    cli = FakePluginCli(garbled=("claude plugin list --json",))
    report = installer.install(catalog, _req(home, project, ["claude"]), cli)
    assert report.steps[-1].outcome == "failed: unreadable output"
