"""B8: incremental re-parse after an edit equals a fresh parse, CalcFormula whole-value #if."""
import pytest

from tools.config_oracle.tests.test_link_incremental import _edit

HOST = (b"table 50100 T\n{\n    fields\n    {\n        field(2; F; Decimal)\n        {\n"
        b"            FieldClass = FlowField;\n            %s\n        }\n    }\n}\n")

FLAT = b'CalcFormula = sum(S.A);'
AFTER_ENDIF = b'CalcFormula =\n#if X\n sum(S.A)\n#else\n max(S.A)\n#endif\n;'
IN_ARMS = b'CalcFormula =\n#if X\n sum(S.A);\n#else\n max(S.A);\n#endif'
EMPTY_PREFIX = b'CalcFormula =\n#if X\n#endif\n sum(S.A);'
# The declared conflict's two readings differ only in the token after #endif.
NO_ELSE = b'CalcFormula =\n#if X\n#endif\n;'

EDITS = [
    (FLAT, AFTER_ENDIF), (AFTER_ENDIF, FLAT),
    (AFTER_ENDIF, IN_ARMS), (IN_ARMS, AFTER_ENDIF),
    (FLAT, EMPTY_PREFIX), (EMPTY_PREFIX, NO_ELSE), (NO_ELSE, EMPTY_PREFIX),
    (AFTER_ENDIF, AFTER_ENDIF.replace(b'CalcFormula', b'CalcFormulaX')),
    (AFTER_ENDIF, AFTER_ENDIF.replace(b'CalcFormula', b'calcformula')),
]


@pytest.mark.parametrize("before,after", EDITS)
def test_incremental_equals_fresh(al_parser, before, after):
    old_src, new_src = HOST % before, HOST % after
    incremental = _edit(al_parser, old_src, new_src)
    fresh = al_parser.parse(new_src)
    assert str(incremental.root_node) == str(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error


@pytest.mark.parametrize("src", [FLAT, AFTER_ENDIF, IN_ARMS, EMPTY_PREFIX])
def test_valid_forms_are_one_clean_property(al_parser, src):
    root = al_parser.parse(HOST % src).root_node
    assert not root.has_error
    body = root.children[0].child_by_field_name("body")
    assert str(body).count("(property ") == 2  # FieldClass and CalcFormula, never a split
