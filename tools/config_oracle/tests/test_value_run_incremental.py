"""B11: incremental re-parse after an edit equals a fresh parse (spec §5.4)."""
import pytest

from tools.config_oracle.tests.test_link_incremental import _edit

HOST = b"page 50100 P { layout { area(Content) { field(F; X) {\n%s\n} } } }\n"
ONE = b"Caption =\n#if X\n 'a';\n#else\n 'b';\n#endif"
TWO = b"Caption =\n#if X\n 'a';\n#endif\n#if not X\n 'b';\n#endif"
TWO_SEMI = TWO + b"\n;"
AFTER_ML = b"CaptionML =\n#if X\n ENU='a'\n#endif\n#if not X\n ENU='b'\n#endif\n;"
INSIDE_ML = b"CaptionML =\n#if X\n ENU='a';\n#endif\n#if not X\n ENU='b';\n#endif"
EMPTY = b"Caption =\n#if X\n#endif\n 'a';"
FLAT = b"Caption = 'a';"

EDITS = [(ONE, TWO), (TWO, ONE), (TWO, TWO_SEMI), (TWO_SEMI, TWO), (INSIDE_ML, AFTER_ML),
         (AFTER_ML, INSIDE_ML), (FLAT, EMPTY), (EMPTY, FLAT), (ONE, ONE.replace(b"#else", b"#elif Y"))]


@pytest.mark.parametrize("before,after", EDITS)
def test_incremental_equals_fresh(al_parser, before, after):
    old_src, new_src = HOST % before, HOST % after
    incremental = _edit(al_parser, old_src, new_src)
    fresh = al_parser.parse(new_src)
    assert str(incremental.root_node) == str(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error
