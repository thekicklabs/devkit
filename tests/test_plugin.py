import json
from pathlib import Path

import pytest

from devkit import frontmatter

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MARKET = ROOT / ".claude-plugin" / "marketplace.json"
CODEX_MARKET = ROOT / ".agents" / "plugins" / "marketplace.json"


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def _plugin_dirs() -> list[Path]:
    return sorted(p.parent.parent for p in ROOT.glob("plugins/*/.claude-plugin/plugin.json"))


def test_marketplaces_list_the_same_plugins():
    claude = _json(CLAUDE_MARKET)
    codex = _json(CODEX_MARKET)
    assert claude["name"] == codex["name"] == "kicklabs"
    claude_sources = {p["name"]: p["source"] for p in claude["plugins"]}
    codex_sources = {p["name"]: p["source"]["path"] for p in codex["plugins"]}
    assert claude_sources == codex_sources
    assert {(ROOT / s).resolve() for s in claude_sources.values()} == set(_plugin_dirs())


def test_marketplace_entries_leave_version_to_the_manifest():
    for market in (CLAUDE_MARKET, CODEX_MARKET):
        assert all("version" not in p for p in _json(market)["plugins"]), market


@pytest.mark.parametrize("plugin", _plugin_dirs(), ids=lambda p: p.name)
def test_runtime_manifests_agree(plugin: Path):
    claude = _json(plugin / ".claude-plugin" / "plugin.json")
    codex = _json(plugin / ".codex-plugin" / "plugin.json")
    assert claude["name"] == codex["name"] == plugin.name
    assert claude["version"] == codex["version"]
    assert (plugin / codex["skills"]).is_dir()
    assert "agents" not in claude, "an agents list hides agents/ from discovery"
    for manifest in (claude, codex):
        hooks = manifest.get("hooks")
        if isinstance(hooks, str):
            assert (plugin / hooks).is_file(), hooks


@pytest.mark.parametrize("plugin", _plugin_dirs(), ids=lambda p: p.name)
def test_agents_are_discoverable(plugin: Path):
    names = []
    for agent in sorted((plugin / "agents").glob("*.md")):
        meta, _ = frontmatter.split(agent.read_text())
        assert meta.get("name") == agent.stem, agent
        assert meta.get("description"), agent
        names.append(agent.stem)
    assert len(names) == len(set(names))
