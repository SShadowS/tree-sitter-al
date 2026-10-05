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
