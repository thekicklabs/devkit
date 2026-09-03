from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from devkit import catalog as catalog_mod
from devkit import installer, machine, picker
from devkit import search as search_mod
from devkit.catalog import KINDS, UnknownItem
from devkit.paths import home, repo_root
from devkit.targets import AGENTS, supports

app = typer.Typer(
    help="Install skills, rules and stack conventions for Claude Code, Codex and Cursor.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _catalog() -> catalog_mod.Catalog:
    return catalog_mod.load(repo_root())


def _csv(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


@app.command("list")
def list_(kind: str | None = typer.Argument(None, help="skills | stacks | rules | machine")):
    """Show what the catalog offers."""
    cat = _catalog()
    kinds = list(KINDS)
    if kind:
        wanted = kind.rstrip("s")
        if wanted not in KINDS:
            raise typer.BadParameter(f"kind must be one of {', '.join(k + 's' for k in KINDS)}")
        kinds = [wanted]
    for k in kinds:
        items = cat.by_kind(k)
        if not items:
            continue
        table = Table(title=f"{k}s", show_lines=False, title_justify="left")
        table.add_column("name", style="bold")
        table.add_column("description")
        if k == "stack":
            table.add_column("requires")
        for item in items:
            row = [item.name, item.description]
            if k == "stack":
                row.append(", ".join(item.requires))
            table.add_row(*row)
        console.print(table)


@app.command()
def search(query: list[str] = typer.Argument(..., help="words to look for")):
    """Full-text search over skills, rules, stacks and machine scripts."""
    cat = _catalog()
    hits = search_mod.search(cat, " ".join(query))
    if not hits:
        console.print("[dim]no matches[/dim]")
        raise typer.Exit(1)
    table = Table(show_header=True, title_justify="left")
    table.add_column("kind")
    table.add_column("name", style="bold")
    table.add_column("file", style="dim")
    table.add_column("match")
    for h in hits:
        rel = h.file.relative_to(cat.root)
        table.add_row(h.item.kind, h.item.name, str(rel), h.line)
    console.print(table)


@app.command()
def install(
    names: list[str] = typer.Argument(
        None, help="skills/stacks to install (reuses last scope+agents)"
    ),
    global_: bool = typer.Option(False, "--global", "-g", help="install under ~"),
    local: bool = typer.Option(False, "--local", "-l", help="install into a project"),
    path: Path | None = typer.Option(
        None, "--path", "-C", help="project dir for --local (default: cwd)"
    ),
    agent: str | None = typer.Option(None, help="comma list: claude,codex,cursor"),
    skill: str | None = typer.Option(None, help="comma list of skills"),
    stack: str | None = typer.Option(None, help="comma list of stacks"),
    all_: bool = typer.Option(False, "--all", help="every skill and stack"),
    yes: bool = typer.Option(False, "--yes", "-y", help="never prompt"),
):
    """Copy skills + rules into each agent's directories and upsert the router."""
    cat = _catalog()
    home_dir = home()
    manifest = installer.read_manifest(home_dir)
    last = manifest.get("last") or {}
    prompt = picker.interactive() and not yes

    if global_ and local:
        raise typer.BadParameter("--global and --local are exclusive")

    skills = _csv(skill)
    stacks = _csv(stack)
    for name in names or []:
        try:
            item = cat.find(name)
        except UnknownItem as e:
            raise typer.BadParameter(str(e)) from None
        (skills if item.kind == "skill" else stacks).append(item.name)

    if all_:
        skills = [i.name for i in cat.by_kind("skill")]
        stacks = [i.name for i in cat.by_kind("stack")]
    elif not skills and not stacks:
        if not prompt:
            raise typer.BadParameter("nothing selected: pass names, --skill/--stack, or --all")
        skills, stacks = picker.pick_items(cat)
        if not skills and not stacks:
            console.print("[dim]nothing selected[/dim]")
            raise typer.Exit(1)

    if global_:
        scope = "global"
    elif local or path is not None:
        scope = "local"
    elif names and last.get("scope"):
        scope = last["scope"]
        if scope == "local" and path is None and last.get("project"):
            path = Path(last["project"])
    elif prompt:
        scope = picker.pick_scope()
    else:
        scope = "local"

    agents = _csv(agent)
    if not agents:
        if names and last.get("agents"):
            agents = [a for a in last["agents"] if supports(a, scope)]
        elif prompt:
            agents = picker.pick_agents(scope)
        else:
            agents = [a for a in AGENTS if supports(a, scope)]
    for a in agents:
        if a not in AGENTS:
            raise typer.BadParameter(f"unknown agent '{a}' (choose from {', '.join(AGENTS)})")
        if not supports(a, scope):
            raise typer.BadParameter(f"{a} has no file-based {scope} scope")

    project = None if scope == "global" else (path or Path.cwd()).resolve()
    req = installer.Request(
        scope=scope,
        agents=agents,
        skills=sorted(set(skills)),
        stacks=sorted(set(stacks)),
        home=home_dir,
        project=project,
    )
    try:
        report = installer.install(cat, req)
    except (UnknownItem, ValueError) as e:
        raise typer.BadParameter(str(e)) from None

    table = Table(title=f"installed · {scope} · {', '.join(agents)}", title_justify="left")
    table.add_column("what")
    table.add_column("where", style="dim")
    grouped: dict[str, list[Path]] = {}
    for w in report.written:
        grouped.setdefault(w.what, []).append(w.path)
    for what, paths in grouped.items():
        table.add_row(what, _summarise(paths, home_dir))
    console.print(table)
    added = [s for s in report.stacks if s not in req.stacks]
    if added:
        console.print(f"[dim]added required stack(s): {', '.join(added)}[/dim]")


def _summarise(paths: list[Path], home_dir: Path) -> str:
    def short(p: Path) -> str:
        try:
            return "~/" + str(p.relative_to(home_dir))
        except ValueError:
            return str(p)

    if len(paths) <= 3:
        return "\n".join(short(p) for p in paths)
    common = Path(os.path.commonpath([str(p) for p in paths]))
    return f"{short(common)}/ ({len(paths)} files)"


@app.command("machine")
def machine_(
    tools: list[str] = typer.Argument(None, help="docker tailscale uv node gh claude codex …"),
    all_: bool = typer.Option(False, "--all", help="run every script"),
):
    """Bootstrap this machine: each script is skipped when its check already passes."""
    cat = _catalog()
    names = [i.name for i in cat.by_kind("machine")]
    if all_:
        chosen = None
    elif tools:
        chosen = list(tools)
    elif picker.interactive():
        chosen = picker.pick_machine(names)
        if not chosen:
            raise typer.Exit(1)
    else:
        raise typer.BadParameter("name the tools or pass --all")
    try:
        outcomes = machine.run(cat, chosen, log=console.print)
    except ValueError as e:
        raise typer.BadParameter(str(e)) from None
    if any(o.status == "failed" for o in outcomes):
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
