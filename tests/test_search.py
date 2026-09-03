from devkit import search


def test_name_match_ranks_first(catalog):
    hits = search.search(catalog, "handoff")
    assert hits[0].item.name == "handoff"
    assert hits[0].line


def test_multi_term_all_matching_line_wins(catalog):
    hits = search.search(catalog, "conventional commit")
    assert hits[0].item.name == "commit"


def test_no_terms(catalog):
    assert search.search(catalog, "") == []
    assert search.search(catalog, "zzzzqqq") == []
