import json
import os
import subprocess
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / "plugins" / "kick" / "hooks"
SCRIPT = HOOKS / "session-start.sh"


def _run(runtime: str, tmp_path: Path, **env: str) -> subprocess.CompletedProcess[str]:
    base = {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path)}
    return subprocess.run(
        ["sh", str(SCRIPT), runtime], env=base | env, capture_output=True, text=True
    )


@pytest.mark.parametrize(
    ("runtime", "mention"), [("claude", "`kick:kick-mode`"), ("codex", "`$kick:kick-mode`")]
)
def test_injects_mandate_for_runtime(tmp_path: Path, runtime: str, mention: str):
    out = _run(runtime, tmp_path)
    assert out.returncode == 0, out.stderr
    assert mention in out.stdout
    assert str(tmp_path / "kick" / "config.md") in out.stdout
    assert "{{" not in out.stdout
    assert len(out.stdout) < 10_000


def test_config_turns_hook_off(tmp_path: Path):
    (tmp_path / "kick").mkdir()
    (tmp_path / "kick" / "config.md").write_text("claude fast: sonnet\nsession hook: off \n")
    for runtime in ("claude", "codex"):
        out = _run(runtime, tmp_path)
        assert out.returncode == 0 and out.stdout == ""


def test_env_turns_hook_off(tmp_path: Path):
    out = _run("codex", tmp_path, KICK_HOOK="off")
    assert out.returncode == 0 and out.stdout == ""


def test_claude_file_stays_quiet_under_codex(tmp_path: Path):
    out = _run("claude", tmp_path, PLUGIN_ROOT=str(HOOKS.parent))
    assert out.returncode == 0 and out.stdout == ""


def test_unknown_runtime_fails(tmp_path: Path):
    out = _run("cursor", tmp_path)
    assert out.returncode == 2 and "unknown runtime" in out.stderr


@pytest.mark.parametrize(
    ("file", "runtime"), [("hooks.json", "claude"), ("codex-hooks.json", "codex")]
)
def test_hooks_file_passes_its_runtime(file: str, runtime: str):
    (entry,) = json.loads((HOOKS / file).read_text())["hooks"]["SessionStart"]
    (hook,) = entry["hooks"]
    assert hook["command"] == f'"${{CLAUDE_PLUGIN_ROOT}}/hooks/session-start.sh" {runtime}'
    assert os.access(SCRIPT, os.X_OK)
