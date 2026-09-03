from __future__ import annotations

import sys

from devkit.catalog import Catalog
from devkit.targets import AGENTS, SCOPES, supports


def interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def pick_items(catalog: Catalog) -> tuple[list[str], list[str]]:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice

    choices = [
        Choice(value=item.label, name=f"{item.kind:<5} {item.name:<12} {item.description}")
        for item in catalog.by_kind("skill") + catalog.by_kind("stack")
    ]
    picked: list[str] = inquirer.fuzzy(
        message="Install (type to filter, tab to select, enter to confirm):",
        choices=choices,
        multiselect=True,
        max_height="70%",
        transformer=lambda r: f"{len(r)} selected",
    ).execute()
    skills = [p.split(":", 1)[1] for p in picked if p.startswith("skill:")]
    stacks = [p.split(":", 1)[1] for p in picked if p.startswith("stack:")]
    return skills, stacks


def pick_scope() -> str:
    from InquirerPy import inquirer

    return inquirer.select(message="Scope:", choices=list(SCOPES), default="local").execute()


def pick_agents(scope: str) -> list[str]:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice

    choices = [Choice(a, enabled=True) for a in AGENTS if supports(a, scope)]
    return inquirer.checkbox(
        message="Agents:",
        choices=choices,
        validate=lambda r: len(r) > 0,
        invalid_message="pick at least one",
    ).execute()


def pick_machine(names: list[str]) -> list[str]:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice

    return inquirer.checkbox(
        message="Machine steps:", choices=[Choice(n, enabled=True) for n in names]
    ).execute()
