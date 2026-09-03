from devkit import frontmatter


def test_split_scalars_and_lists():
    text = (
        "---\nname: x\ndescription: 'quoted: text'\nrequires: [a, b]\n"
        "tags:\n  - t1\n  - t2\n---\nbody\n"
    )
    meta, body = frontmatter.split(text)
    assert meta == {
        "name": "x",
        "description": "quoted: text",
        "requires": ["a", "b"],
        "tags": ["t1", "t2"],
    }
    assert body == "body\n"


def test_no_frontmatter_is_passthrough():
    assert frontmatter.split("# hi\n") == ({}, "# hi\n")
    assert frontmatter.strip("# hi\n") == "# hi\n"


def test_unterminated_fence_is_body():
    assert frontmatter.split("---\nname: x\n") == ({}, "---\nname: x\n")
