"""Minimal YAML-subset frontmatter parser: scalars, `[a, b]` lists and `- a` lists."""

from __future__ import annotations

FENCE = "---"


def split(text: str) -> tuple[dict[str, object], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != FENCE:
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == FENCE)
    except StopIteration:
        return {}, text
    body = "\n".join(lines[end + 1 :])
    if text.endswith("\n"):
        body += "\n"
    return _parse(lines[1:end]), body


def strip(text: str) -> str:
    return split(text)[1].lstrip("\n")


def _parse(lines: list[str]) -> dict[str, object]:
    data: dict[str, object] = {}
    key: str | None = None
    for raw in lines:
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")) and key is not None and line.strip().startswith("- "):
            items = data.setdefault(key, [])
            assert isinstance(items, list)
            items.append(_scalar(line.strip()[2:]))
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            data[key] = []
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [_scalar(v) for v in inner.split(",")] if inner else []
        else:
            data[key] = _scalar(value)
    return data


def _scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value
