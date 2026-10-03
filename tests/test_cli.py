from pathlib import Path

import pytest
from typer.testing import CliRunner

from devkit import managed, plugins
from devkit.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def fake_plugin_cli(monkeypatch, plugin_cli):
    monkeypatch.setattr(plugins, "system_runner", plugin_cli)
    return plugin_cli


def _invoke(home: Path, *args: str):
    result = runner.invoke(app, list(args), env={"DEVKIT_HOME_DIR": str(home)})
    assert result.exit_code == 0, result.output
    return result


def _install(home: Path, project: Path, *args: str):
    return _invoke(home, "install", "--local", "--path", str(project), "--agent", "codex", *args)


def test_partial_install_keeps_stack_rows_in_router(home, project, plugin_cli):
    _install(home, project, "--stack", "python", "--skill", "plan")
    _install(home, project, "tdd")
    router = managed.extract((project / "AGENTS.md").read_text())
    assert router is not None
    assert "`AGENTS/python/AGENTS.md`" in router
    assert plugin_cli.codex_plugins == {"kick@kicklabs"}
    assert not (project / ".agents" / "skills").exists()


def test_install_and_update_report_plugin_steps(home, project, plugin_cli):
    out = _install(home, project, "--skill", "plan").output
    assert "kick@kicklabs: installed" in out
    out = _invoke(home, "update", "--no-pull").output
    assert "plugin (codex) kick@kicklabs: updated" in out
    assert plugin_cli.ran("codex", "plugin", "add", "kick@kicklabs") == [None, None]


def test_update_reports_a_failed_plugin_and_exits_nonzero(home, project, plugin_cli):
    _install(home, project, "--skill", "plan")
    plugin_cli.failing.add("codex plugin add kick@kicklabs")
    result = runner.invoke(app, ["update", "--no-pull"], env={"DEVKIT_HOME_DIR": str(home)})
    assert result.exit_code == 1
    assert "plugin (codex) kick@kicklabs: failed: boom" in result.output


def test_install_exits_nonzero_when_a_plugin_fails(home, project, plugin_cli):
    plugin_cli.failing.add("codex plugin add kick@kicklabs")
    result = runner.invoke(
        app,
        ["install", "--local", "--path", str(project), "--agent", "codex", "--skill", "plan"],
        env={"DEVKIT_HOME_DIR": str(home)},
    )
    assert result.exit_code == 1
    assert "failed: boom" in result.output
