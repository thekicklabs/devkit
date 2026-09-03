from pathlib import Path

import pytest

from devkit import catalog as catalog_mod

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
