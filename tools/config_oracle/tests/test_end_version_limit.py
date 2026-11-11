"""Issues #40/#41: an if / else-if chain whose blocks each hold a block opened in a `#if` arm
(shape A) or a whole `if ... else begin ... end;` inside `#if` (shape B, 8 blocks) used to exceed
tree-sitter's MAX_VERSION_COUNT / MAX_LINK_COUNT: one parse version per block read `end;` as a call
of a name `end`, and the right version was dropped (ERROR over the procedure). That version now dies
at once: since state review C3 `end` is a grammar token reserved at a statement start (the reserved set
`statement_names` on `_expression_statement` and `_assign_target`); until C3 the scanner did it
(`end` where BEGIN_KEYWORD was valid and END_KEYWORD was not). Every name position of `end` is pinned
by test_end_name_positions.py.

The inputs are the committed alc probes (alc accepts them), parsed as whole files; the `// expect`
header lines are comments to the parser. Shape B is also run at 16 blocks, twice the old limit."""
from pathlib import Path

import pytest

CASES = Path(__file__).resolve().parents[2] / "alc_probe" / "cases" / "issue40-42"


def _object(root):
    return next(c for c in root.children if c.type != "comment")


def _procedures(root):
    body = next(c for c in _object(root).children if c.type == "declaration_body")
    return [c for c in body.children if c.type == "procedure"]


@pytest.mark.parametrize("name,procedures", [("shape_A.al", 2), ("shape_B.al", 3)])
def test_chain_parses_clean(al_parser, name, procedures):
    root = al_parser.parse((CASES / name).read_bytes()).root_node
    assert not root.has_error
    assert _object(root).type == "codeunit_declaration"
    assert len(_procedures(root)) == procedures


def test_shape_b_twice_the_old_limit(al_parser):
    src = (CASES / "shape_B.al").read_text(encoding="utf-8")
    block = "end else if M1 then begin\n"
    start = src.index(block)
    end = src.index("end else if M2 then begin\n")
    longer = src[:end] + src[start:end] * 8 + src[end:]   # 8 more blocks: 16 in all
    root = al_parser.parse(longer.encode()).root_node
    assert not root.has_error
    assert len(_procedures(root)) == 3
