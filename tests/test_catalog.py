import pytest

from devkit.catalog import UnknownItem


def test_every_skill_has_name_and_description(catalog):
    skills = {s.name for s in catalog.by_kind("skill")}
    assert {"plan", "commit", "tdd", "code-review", "debug", "refactor", "handoff"} <= skills
    for s in catalog.by_kind("skill"):
        assert s.description, s.name
        assert (s.path / "SKILL.md").exists()


def test_rules_have_read_when(catalog):
    rule = catalog.get("rule", "workflow")
    assert rule.description.startswith("always")


def test_find_prefers_skill_then_stack(catalog):
    assert catalog.find("plan").kind == "skill"
    with pytest.raises(UnknownItem):
        catalog.find("nope")


def test_resolve_stacks_adds_requirements_first(catalog):
    names = {s.name for s in catalog.by_kind("stack")}
    if not {"python", "fastapi"} <= names:
        pytest.skip("stacks not written yet")
    assert catalog.resolve_stacks(["fastapi"]) == ["python", "fastapi"]
    assert catalog.resolve_stacks(["fastapi", "python"]) == ["python", "fastapi"]


def test_resolve_stacks_cycle(tmp_path):
    from devkit import catalog as catalog_mod

    for name, req in (("a", "b"), ("b", "a")):
        d = tmp_path / "stacks" / name
        d.mkdir(parents=True)
        (d / "AGENTS.md").write_text(f"---\nname: {name}\nrequires: [{req}]\n---\n# {name}\n")
    cat = catalog_mod.load(tmp_path)
    with pytest.raises(ValueError, match="cycle"):
        cat.resolve_stacks(["a"])
