import json
from pathlib import Path

import pytest

from devkit import catalog as catalog_mod
from devkit.plugins import Result

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def catalog():
    return catalog_mod.load(ROOT)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    h = tmp_path / "home"
    h.mkdir()
    return h


@pytest.fixture
def project(tmp_path: Path) -> Path:
    p = tmp_path / "proj"
    p.mkdir()
    return p


class FakePluginCli:
    """Stands in for the `claude plugin` and `codex plugin` CLIs."""

    def __init__(
        self,
        missing: tuple[str, ...] = (),
        failing: tuple[str, ...] = (),
        garbled: tuple[str, ...] = (),
    ) -> None:
        self.calls: list[tuple[tuple[str, ...], Path | None]] = []
        self.missing = set(missing)
        self.failing = set(failing)
        self.garbled = set(garbled)
        self.markets: dict[str, dict[str, str]] = {"claude": {}, "codex": {}}
        self.claude_plugins: list[dict] = []
        self.codex_plugins: set[str] = set()

    def ran(self, *argv: str) -> list[Path | None]:
        return [cwd for args, cwd in self.calls if args == argv]

    def __call__(self, argv: list[str], cwd: Path | None) -> Result:
        self.calls.append((tuple(argv), cwd))
        tool, *rest = argv
        if tool in self.missing:
            return Result(127, stderr=f"{tool}: not found")
        if " ".join(argv) in self.failing:
            return Result(1, stderr="boom")
        if " ".join(argv) in self.garbled:
            return Result(0, "WARNING: not json")
        match tool, rest:
            case "claude", ["plugin", "marketplace", "list", "--json"]:
                markets = [
                    {"name": n, "source": "directory", "path": p}
                    for n, p in sorted(self.markets[tool].items())
                ]
                return Result(0, json.dumps(markets))
            case "codex", ["plugin", "marketplace", "list"]:
                rows = "".join(f"{n}  {p}\n" for n, p in sorted(self.markets[tool].items()))
                return Result(0, "MARKETPLACE  ROOT\n" + rows)
            case _, ["plugin", "marketplace", "add", source]:
                self.markets[tool]["kicklabs"] = source
                return Result(0)
            case "claude", ["plugin", "list", "--json"]:
                return Result(0, json.dumps(self.claude_plugins))
            case "claude", ["plugin", "install", pid, "--scope", scope]:
                entry = {"id": pid, "scope": scope}
                if scope == "project":
                    entry["projectPath"] = str(cwd)
                self.claude_plugins.append(entry)
                return Result(0)
            case "codex", ["plugin", "list", "--json"]:
                installed = [{"pluginId": p} for p in sorted(self.codex_plugins)]
                return Result(0, json.dumps({"installed": installed, "available": []}))
            case "codex", ["plugin", "add", pid]:
                self.codex_plugins.add(pid)
                return Result(0)
            case "claude", ["plugin", "update", _]:
                return Result(0)
        raise AssertionError(f"unexpected call: {argv}")


@pytest.fixture
def plugin_cli() -> FakePluginCli:
    return FakePluginCli()
