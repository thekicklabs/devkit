START = "<!-- devkit:start -->"
END = "<!-- devkit:end -->"


def wrap(block: str) -> str:
    return f"{START}\n{block.strip()}\n{END}\n"


def upsert(existing: str, block: str) -> str:
    """Replace the managed region, or append one. Text outside the markers is untouched."""
    managed = wrap(block)
    start = existing.find(START)
    end = existing.find(END, start + len(START)) if start != -1 else -1
    if start != -1 and end != -1:
        tail = existing[end + len(END) :]
        if tail.startswith("\n"):
            tail = tail[1:]
        return existing[:start] + managed + tail
    if not existing.strip():
        return managed
    sep = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    return existing + sep + managed


def extract(existing: str) -> str | None:
    start = existing.find(START)
    end = existing.find(END, start + len(START)) if start != -1 else -1
    if start == -1 or end == -1:
        return None
    return existing[start + len(START) : end].strip()
