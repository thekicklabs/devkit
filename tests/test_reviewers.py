import os
import subprocess
from pathlib import Path

SCRIPTS = (
    Path(__file__).resolve().parents[1] / "plugins" / "kick" / "skills" / "interrogate" / "scripts"
)


def _stub(bin_dir: Path, name: str, body: str) -> None:
    path = bin_dir / name
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(0o755)


def _detect(bin_dir: Path, **env: str) -> dict[str, list[str]]:
    out = subprocess.run(
        ["sh", str(SCRIPTS / "detect-reviewers.sh")],
        env={"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(bin_dir)} | env,
        capture_output=True,
        text=True,
        check=True,
    )
    rows = [line.split("\t") for line in out.stdout.splitlines()]
    return {row[0]: row[1:] for row in rows}


def test_detects_installed_and_authed_clis(tmp_path: Path):
    _stub(tmp_path, "claude", '[ "$1 $2" = "auth status" ] && exit 0; exit 9')
    _stub(tmp_path, "codex", '[ "$1 $2" = "login status" ] && exit 1; exit 9')
    found = _detect(tmp_path)
    assert found["claude"] == ["installed", "authed", "stable"]
    assert found["codex"] == ["installed", "unauthed", "stable"]
    for cli in ("agent", "gemini", "opencode"):
        assert found[cli] == ["missing", "unknown", "experimental"]


def test_gemini_auth_comes_from_its_environment(tmp_path: Path):
    _stub(tmp_path, "gemini", "exit 0")
    assert _detect(tmp_path)["gemini"] == ["installed", "unknown", "experimental"]
    found = _detect(tmp_path, GEMINI_API_KEY="x")
    assert found["gemini"] == ["installed", "authed", "experimental"]


def test_scripts_are_executable():
    for script in SCRIPTS.glob("*.sh"):
        assert os.access(script, os.X_OK), script
