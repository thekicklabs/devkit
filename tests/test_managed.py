from devkit import managed


def test_insert_into_empty():
    assert managed.upsert("", "hello") == managed.wrap("hello")


def test_append_preserves_existing():
    out = managed.upsert("# mine\n\n- a rule\n", "block")
    assert out.startswith("# mine\n\n- a rule\n")
    assert managed.extract(out) == "block"


def test_replace_preserves_surroundings():
    first = managed.upsert("before\n", "one")
    first += "after\n"
    second = managed.upsert(first, "two")
    assert second == first.replace(managed.wrap("one"), managed.wrap("two"))
    assert "one" not in second


def test_idempotent():
    once = managed.upsert("x\n", "b")
    assert managed.upsert(once, "b") == once
