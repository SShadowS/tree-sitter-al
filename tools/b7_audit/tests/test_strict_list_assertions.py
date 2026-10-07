"""The strict-list assertion model (tools/b7_audit/strict_list_assertions.py) reads the hole text, not the parser."""
import pytest

from tools.b7_audit.strict_list_assertions import model

G = "preproc_conditional_field_list_items"


def test_items_and_groups_in_source_order_separators_and_comments_skipped():
    hole = 'A /* c */ #if X\n, "B C" // d\n#elif Y\n, 2\n#else\n#endif\n, true'
    assert model(hole, G) == (f"(identifier) ({G}! (preproc_if) (quoted_identifier) (preproc_elif) (integer) "
                              "(preproc_else) (preproc_endif)) (boolean)")


def test_nested_groups_are_exact_and_owned_by_their_arm():
    assert model("A\n#if X\n, B\n#if Y\n, C\n#endif\n#endif\n", G) == (
        f"(identifier) ({G}! (preproc_if) (identifier) ({G}! (preproc_if) (identifier) (preproc_endif)) (preproc_endif))")


@pytest.mark.parametrize("hole", ["A\n#if X\n, B\n", "A + B"])
def test_unbalanced_or_foreign_tokens_are_refused(hole):
    with pytest.raises(ValueError):
        model(hole, G)
