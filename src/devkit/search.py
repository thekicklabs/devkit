from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from devkit import frontmatter
from devkit.catalog import Catalog, Item


@dataclass
class Hit:
    item: Item
    file: Path
    score: float
    line: str


def _terms(query: str) -> list[str]:
    return [t.lower() for t in re.findall(r"\w+", query) if len(t) > 1]


def search(catalog: Catalog, query: str, limit: int = 20) -> list[Hit]:
    terms = _terms(query)
    if not terms:
        return []
    hits: list[Hit] = []
    for item in catalog.items:
        for file in item.files or (item.path,):
            if file.suffix not in (".md", ".sh"):
                continue
            text = frontmatter.strip(file.read_text()) if file.suffix == ".md" else file.read_text()
            hit = _score(item, file, text, terms)
            if hit:
                hits.append(hit)
    hits.sort(key=lambda h: (-h.score, h.item.kind, h.item.name, str(h.file)))
    return hits[:limit]


def _score(item: Item, file: Path, text: str, terms: list[str]) -> Hit | None:
    score = 0.0
    name = f"{item.name} {file.stem}".lower()
    desc = item.description.lower()
    for t in terms:
        word = re.compile(rf"\b{re.escape(t)}\b")
        if word.search(name):
            score += 20
        if word.search(desc):
            score += 6
    best_line, best_count = "", 0
    full, partial = 0, 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("```", "|--", "| ---")):
            continue
        low = line.lower()
        count = sum(1 for t in terms if t in low)
        if not count:
            continue
        if count == len(terms):
            full += 1
        else:
            partial += 1
        if count > best_count or (count == best_count and len(line) < len(best_line)):
            best_line, best_count = line, count
    # Frequency is capped so a long file cannot outrank a file that is *about* the term.
    score += 3 * min(full, 5) + min(partial, 10)
    if score == 0:
        return None
    return Hit(item, file, score, best_line[:120])
