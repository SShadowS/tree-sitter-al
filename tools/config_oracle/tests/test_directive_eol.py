"""`_directive_eol` must accept every extra-space character before the newline.

It is hidden, so a MISSING `_directive_eol` shows only as `has_error`: no
command-line gate (`tree-sitter parse`, `--json-summary`, parse-al-parallel.sh,
corpus tests) reports it. Before the fix the scanner skipped only space and tab.
"""
import pytest

BOM = "﻿".encode("utf-8")

# `A` + BOM lexes the BOM into the identifier, so the space-led BOM case is the
# one that reaches the scanner. Both are kept.
EOLS = [b"\f\n", b"\v\n", BOM + b"\n", b" " + BOM + b"\n", b"\r\r\n", b"\r\n", b"\n",
        b" \t\f\r\n"]


@pytest.mark.parametrize("eol", EOLS, ids=repr)
def test_directive_eol_after_extra_space(al_parser, eol):
    src = b"codeunit 1 T { trigger OnRun() begin\n#if A" + eol + b"x := 1;\n#endif\nend; }\n"
    root = al_parser.parse(src).root_node
    assert root.has_error is False
