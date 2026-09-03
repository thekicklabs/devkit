"""Run machine/*.sh in order. A script whose `check` passes is skipped."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from devkit.catalog import Catalog, Item


@dataclass
class Outcome:
    item: Item
    status: str  # skipped | ok | failed
    returncode: int = 0


def is_satisfied(item: Item) -> bool:
    return subprocess.run(["bash", str(item.path), "check"], capture_output=True).returncode == 0


def run(catalog: Catalog, names: list[str] | None, *, log=print) -> list[Outcome]:
    items = catalog.by_kind("machine")
    if names:
        wanted = set(names)
        unknown = wanted - {i.name for i in items}
        if unknown:
            raise ValueError(f"unknown machine step(s): {', '.join(sorted(unknown))}")
        items = [i for i in items if i.name in wanted]
    outcomes: list[Outcome] = []
    for item in items:
        if is_satisfied(item):
            log(f"skip  {item.name}: already present")
            outcomes.append(Outcome(item, "skipped"))
            continue
        log(f"run   {item.name}: {item.description}")
        rc = subprocess.run(["bash", str(item.path)]).returncode
        outcomes.append(Outcome(item, "ok" if rc == 0 else "failed", rc))
        if rc != 0:
            log(f"fail  {item.name} exited {rc}")
            break
    return outcomes
