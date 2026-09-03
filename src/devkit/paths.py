import os
from pathlib import Path


def repo_root() -> Path:
    env = os.environ.get("DEVKIT_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[2]


def home() -> Path:
    return Path(os.environ.get("DEVKIT_HOME_DIR") or Path.home()).resolve()


def config_dir(home_dir: Path) -> Path:
    return home_dir / ".config" / "devkit"
