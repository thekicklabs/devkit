from pathlib import Path

from typer.testing import CliRunner

from devkit import managed
from devkit.cli import app

runner = CliRunner()


def _install(home: Path, project: Path, *args: str):
    env = {"DEVKIT_HOME_DIR": str(home)}
    result = runner.invoke(
        app, ["install", "--local", "--path", str(project), "--agent", "codex", *args], env=env
    )
    assert result.exit_code == 0, result.output
    return result


def test_partial_install_keeps_stack_rows_in_router(home, project):
    _install(home, project, "--stack", "python", "--skill", "plan")
    _install(home, project, "tdd")
    router = managed.extract((project / "AGENTS.md").read_text())
    assert router is not None
    assert "`AGENTS/python/AGENTS.md`" in router
    assert (project / ".agents" / "skills" / "tdd" / "SKILL.md").exists()
