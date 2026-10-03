import json
import os
import re
import subprocess
from pathlib import Path

import pytest

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


REVIEW = SCRIPTS / "review.sh"
SKILLS = SCRIPTS.parents[1]
SCHEMA = SKILLS / "interrogate" / "references" / "findings.schema.json"


def _git_env(tmp_path: Path) -> dict[str, str]:
    return {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    root = tmp_path / "repo"
    root.mkdir()
    env = _git_env(tmp_path)
    git = ["git", "-C", str(root)]
    subprocess.run([*git, "init", "-q"], env=env, check=True)
    (root / "calc.py").write_text("def add(a, b):\n    return a - b\n")
    subprocess.run([*git, "add", "."], env=env, check=True)
    subprocess.run([*git, "commit", "-qm", "calc"], env=env, check=True)
    (root / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (root / "notes.txt").write_text("new file\n")
    return root, env


def _prepare(root: Path, env: dict[str, str]) -> Path:
    out = subprocess.run(
        ["sh", str(REVIEW), "prepare", "--uncommitted"],
        input="Fix add.\n",
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(out.stdout.strip())


def _run(cli: str, run: Path, env: dict[str, str], *args: str):
    return subprocess.run(
        ["sh", str(REVIEW), "run", cli, str(run), *args], env=env, capture_output=True, text=True
    )


def test_prepare_builds_the_brief(repo):
    root, env = repo
    run = _prepare(root, env)
    assert run.parent == root / ".git" / "kick"
    patch = (run / "diff.patch").read_text()
    assert "+    return a + b" in patch and "notes.txt" in patch
    prompt = (run / "prompt.md").read_text()
    for part in ("Fix add.", "### 3. Try to disprove each finding", "| BLOCKER |", "notes.txt"):
        assert part in prompt
    assert json.loads((run / "schema.json").read_text()) == json.loads(SCHEMA.read_text())
    assert (run / "repo").read_text().strip() == str(root)


def test_prepare_refuses_an_empty_diff(repo):
    root, env = repo
    subprocess.run(["git", "-C", str(root), "stash", "-uq"], env=env, check=True)
    out = subprocess.run(
        ["sh", str(REVIEW), "prepare", "--uncommitted"],
        input="Nothing.\n",
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    assert out.returncode == 2 and "empty" in out.stderr
    assert not (root / ".git" / "kick").exists() or not any((root / ".git" / "kick").iterdir())


def test_dry_run_argv(repo):
    root, env = repo
    run = _prepare(root, env)
    schema = (run / "schema.json").read_text()
    claude = _run("claude", run, env, "--dry-run").stdout.splitlines()
    assert claude == [
        "claude", "-p", "--safe-mode", "--model", "opus", "--effort", "high",
        "--tools", "Read,Grep,Glob", "--allowedTools", "Read,Grep,Glob",
        "--disallowedTools",
        "Bash,Edit,Write,NotebookEdit,WebFetch,WebSearch,Read(**/.env),Read(**/.env.*)",
        "--permission-mode", "dontAsk", "--strict-mcp-config", "--no-session-persistence",
        "--output-format", "json", "--json-schema", schema,
        f"< {run}/prompt.md", f"> {run}/claude.json",
    ]  # fmt: skip
    codex = _run("codex", run, env, "--dry-run").stdout.splitlines()
    assert codex == [
        "codex", "exec", "--sandbox", "read-only", "--ephemeral", "--ignore-user-config",
        "-C", str(root), "-m", "gpt-6.1-sol", "-c", "model_reasoning_effort=high",
        "--output-schema", f"{run}/schema.json", "-o", f"{run}/codex.json", "-",
        f"< {run}/prompt.md", f"> {run}/codex.log",
    ]  # fmt: skip


def test_dry_run_reads_reviewer_models_from_config(repo):
    root, env = repo
    run = _prepare(root, env)
    config = Path(env["XDG_CONFIG_HOME"]) / "kick"
    config.mkdir(parents=True)
    (config / "config.md").write_text("codex reviewer: gpt-6-luna\ngemini reviewer: g-pro\n")
    assert "gpt-6-luna" in _run("codex", run, env, "--dry-run").stdout.splitlines()
    gemini = _run("gemini", run, env, "--dry-run").stdout.splitlines()
    assert gemini[:7] == ["gemini", "--approval-mode", "plan", "-o", "json", "-m", "g-pro"]
    opencode = _run("opencode", run, env, "--dry-run").stdout.splitlines()
    assert "-m" not in opencode and opencode[-3] == f"Follow {run}/prompt.md"


def _stub_run(repo, body: str, **extra: str) -> tuple[str, Path]:
    root, env = repo
    run = _prepare(root, env)
    bin_dir = root.parent / "bin"
    bin_dir.mkdir(exist_ok=True)
    _stub(bin_dir, "claude", body)
    env = env | {"PATH": f"{bin_dir}:{env['PATH']}"} | extra
    _run("claude", run, env)
    return (run / "claude.status").read_text().strip(), run


def test_status_ok(repo):
    status, run = _stub_run(repo, 'cat >/dev/null; echo "{}"')
    assert status == "ok"
    assert (run / "claude.json").read_text().strip() == "{}"


def test_status_failed(repo):
    assert _stub_run(repo, "exit 3")[0] == "failed"


def test_status_tainted_when_reviewer_writes(repo):
    assert _stub_run(repo, "echo oops >> calc.py")[0] == "tainted"
    assert _stub_run(repo, "touch stray.txt")[0] == "tainted"


def test_status_timeout(repo):
    assert _stub_run(repo, "sleep 5", KICK_REVIEW_TIMEOUT="1")[0] == "timeout"


def test_reviewer_sees_hook_disabled(repo):
    status, run = _stub_run(repo, 'echo "$KICK_HOOK"')
    assert status == "ok" and (run / "claude.json").read_text().strip() == "off"


def _table_column(text: str, heading: str) -> list[str]:
    section = text.split(heading, 1)[1]
    rows = [line for line in section.splitlines() if line.startswith("| ")][2:]
    rows = rows[: next((i for i, r in enumerate(rows) if not r.strip()), len(rows))]
    return [row.split("|")[1].strip() for row in rows]


def test_schema_matches_code_review_scales():
    review = (SKILLS / "code-review" / "SKILL.md").read_text()
    finding = json.loads(SCHEMA.read_text())["properties"]["findings"]["items"]["properties"]
    severities = re.findall(r"^\| (BLOCKER|HIGH|MEDIUM|LOW) \|", review, re.MULTILINE)
    assert finding["severity"]["enum"] == severities
    confidence = re.search(r"Confidence on every finding:(.*?)\n\n", review, re.DOTALL)
    assert confidence
    assert finding["confidence"]["enum"] == re.findall(r"\*\*(\w+)\*\*", confidence[1])
    section = review.split("| Dimension | Look for |", 1)[1].split("###", 1)[0]
    dimensions = re.findall(r"^\| ([A-Z][a-z ]+) \|", section, re.MULTILINE)
    expected = [d.lower().replace(" ", "_") for d in dimensions] + ["house_rule"]
    assert finding["category"]["enum"] == expected
    assessments = re.search(r"exactly one of: (.*?)\. No score", review, re.DOTALL)
    assert assessments
    phrases = re.findall(r"\*([^*]+)\*", assessments[1])
    top = json.loads(SCHEMA.read_text())["properties"]["assessment"]["enum"]
    assert [p.split()[0].lower() for p in phrases] == [t.split("_")[0] for t in top]


def test_schema_is_strict():
    def walk(node: dict) -> None:
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node["properties"])
        for child in node.get("properties", {}).values():
            walk(child)
        if isinstance(node.get("items"), dict):
            walk(node["items"])

    walk(json.loads(SCHEMA.read_text()))
