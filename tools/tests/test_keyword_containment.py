"""B5 Review focus 1: the keyed TableRelation states never change how a generic
property value lexes these words (the issue #27 class). Every generic placement must give the same tree as the
pre-B5 library."""
import os
from pathlib import Path
import pytest
from tools import relation_census as rc
from tools.alc_facts.extract import load_keywords

BASE = os.environ.get("B5_BASE_LIB")   # $SCRATCH/al_base.dll; the test skips without it
SITES = [
    b"table 50100 T\n{\n    fields { field(1; F; Code[20])\n    {\n        Description = %s;\n    }\n    }\n}\n",
    b"page 50100 P\n{\n    layout { area(Content) { field(F; Rec.F)\n    {\n        Visible = %s;\n"
    b"        Image = %s;\n        ApplicationArea = %s;\n    }\n    }\n    }\n}\n",
]


@pytest.mark.skipif(not BASE, reason="set B5_BASE_LIB to the pre-B5 library")
@pytest.mark.parametrize("word", load_keywords())
def test_generic_value_tree_unchanged(word):
    base, cur = rc.parser_for(Path(BASE)), rc.parser_for(None)
    w = word.capitalize().encode()
    for site in SITES:
        src = site.replace(b"%s", w)
        assert str(cur.parse(src).root_node) == str(base.parse(src).root_node), (word, src)


# Absolute form: needs no base library, so the containment proof still runs after merge.
# The value node of a generic property is a childless `identifier` for every keyword
# except these, whose pinned shapes are what the pre-B5 library gave (measured at B5 review).
# `where` ERRORs as a generic value at base too (deferred-work item 28): it is pinned as an
# ERROR, so fixing item 28 fails this test on purpose and the pin is dropped then.
PINNED = {w: "keyword_identifier" for w in
          ("action", "codeunit", "enum", "page", "query", "report", "system", "xmlport")}
PINNED.update({w: "option_member_list" for w in ("internal", "local", "protected", "tabledata")})


def _values(n, out):
    if n.type == "property":
        out.append(n.child_by_field_name("value"))
    for c in n.children:
        _values(c, out)


@pytest.mark.parametrize("word", load_keywords())
def test_generic_value_shape_absolute(word):
    cur = rc.parser_for(None)
    w = word.capitalize().encode()
    for site in SITES:
        root = cur.parse(site.replace(b"%s", w)).root_node
        if word == "where":
            assert root.has_error, "item 28 fixed? drop the pin"
            continue
        assert not root.has_error, (word, site)
        vals = []
        _values(root, vals)
        assert vals, (word, site)
        want = PINNED.get(word, "identifier")
        for v in vals:
            assert v.type == want, (word, v.type, want)
            if want == "identifier":
                assert v.child_count == 0, (word, "identifier has children")
