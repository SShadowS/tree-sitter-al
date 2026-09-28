import pytest

from tools.config_oracle.directives import ResolveError, resolve

SRC = (b"a;\n"
       b"#if A // note\n"
       b"b;\n"
       b"#elif A\n"
       b"c;\n"
       b"#else\n"
       b"d;\n"
       b"#endif\n"
       b"e;\n")


def mask_of(src, env):
    return resolve(src, frozenset(env)).masked


def test_if_arm_selected_and_directive_lines_fully_masked_including_comment():
    assert mask_of(SRC, {"A"}) == (b"a;\n" + b" " * 13 + b"\n" + b"b;\n" + b" " * 7 + b"\n"
                                   + b"  \n" + b" " * 5 + b"\n" + b"  \n" + b" " * 6 + b"\n" + b"e;\n")


def test_elif_is_first_match_so_else_taken_when_A_unset():
    assert mask_of(SRC, set()) == (b"a;\n" + b" " * 13 + b"\n" + b"  \n" + b" " * 7 + b"\n"
                                   + b"  \n" + b" " * 5 + b"\n" + b"d;\n" + b" " * 6 + b"\n" + b"e;\n")


def elif_is_first_match(resolve_fn):
    """The named first-match expectation, parameterised by the resolver under test so the
    mutation test in test_configs.py can run it against a mutant. With A set, `#if A` is
    taken, so the equally-true `#elif A` must NOT be (A unset cannot tell: both are false)."""
    m = resolve_fn(SRC, frozenset({"A"})).masked
    assert b"b;" in m and b"c;" not in m and b"d;" not in m


def test_elif_is_first_match_so_a_true_elif_after_a_taken_if_is_not_taken():
    elif_is_first_match(resolve)


def test_offsets_are_preserved():
    for env in (set(), {"A"}):
        assert len(mask_of(SRC, env)) == len(SRC)


def test_crlf_is_kept_byte_for_byte():
    src = b"#if A\r\nx;\r\n#endif\r\n"
    assert mask_of(src, set()) == b"     \r\n  \r\n      \r\n"


def test_arm_choice_and_extents():
    r = resolve(SRC, frozenset({"A"}))
    first = r.directives[0]
    assert (first.kind, SRC[first.cond.start:first.cond.end]) == ("if", b"A")
    assert SRC[first.line_end:first.next_line] == b"\n"
    assert r.arm_choice == {first.hash: first.hash}


def test_nested_groups_inside_inactive_arm_are_not_reached():
    src = b"#if A\n#if B\nx;\n#endif\n#endif\n"
    r = resolve(src, frozenset())
    assert list(r.arm_choice) == [0]


def test_inactive_text_is_not_lexed():
    src = b"#if A\ny;\n#else\n  Message('abc\n  /* open\n#endif\nz;\n"
    r = resolve(src, frozenset({"A"}))
    assert r.masked.endswith(b"z;\n")


@pytest.mark.parametrize("src", [
    b"x;\n/*\n#if A\n*/\ny;\n",          # directive inside a block comment
    b"x;\n// #if A\ny;\n",               # inside a line comment
    b"M(@'l1\n#if A\nl2');\n",           # inside a multi-line verbatim string
])
def test_hash_inside_active_comment_or_verbatim_string_is_not_a_directive(src):
    r = resolve(src, frozenset({"A"}))
    assert r.directives == [] and r.masked == src


def test_directive_after_code_fails_closed():
    for src in (b"x; #if A\ny;\n#endif\n", b"#if A\ny; #endif\n"):
        with pytest.raises(ResolveError) as err:
            resolve(src, frozenset({"A"}))
        assert err.value.reason == "directive-after-code"
    # directive-looking text inside a string or a comment is still not a directive
    assert resolve(b"x := '#if';\n", frozenset()).masked == b"x := '#if';\n"
    assert resolve(b"// x #if A\n", frozenset()).masked == b"// x #if A\n"


@pytest.mark.parametrize("src,reason", [
    (b"#if A\nx;\n", "unbalanced-if"),
    (b"#endif\n", "unbalanced-endif"),
    (b"#if A\n#else B\n#endif\n", "trailing-token"),
    (b"#if A\n#endif /* c */\n", "block-comment-on-directive"),
    (b"#ifx A\n#endif\n", "unknown-directive"),
    (b"#if A\n#else\n#elif B\n#endif\n", "elif-after-else"),
    (b"#if A\n#else\n#else\n#endif\n", "duplicate-else"),
    (b"#define 1A\n", "malformed-define"),
    (b"x;\n/* never closed\n", "unterminated-active-comment"),
    (b"M(@'never closed\n", "unterminated-active-verbatim"),
    (b"#else\n", "unbalanced-else"),
    (b"#elif A\n", "unbalanced-elif"),
    (b"#if\n#endif\n", "empty-condition"),
    (b"x; '#never closed\n", "unterminated-active-string"),
    (b"#if_A\n#endif\n", "unknown-directive"),
])
def test_malformed_fails_closed(src, reason):
    with pytest.raises(ResolveError) as err:
        resolve(src, frozenset())
    assert err.value.reason == reason


def test_define_only_takes_effect_when_active():
    src = b"#if A\n#define B\n#endif\n#if B\nx;\n#endif\n"
    assert resolve(src, frozenset()).masked.count(b"x;") == 0
    assert resolve(src, frozenset({"A"})).masked.count(b"x;") == 1


def test_undef_removes_assigned_symbol():
    src = b"#undef B\n#if B\nx;\n#endif\n"
    assert resolve(src, frozenset({"B"})).masked.count(b"x;") == 0


def test_extras_exclude_masked_directive_lines_and_inactive_text():
    src = b"// top\n#if A // on-directive\n/* in-arm */\n#else\n// inactive\n#endif\n#pragma warning disable X\n"
    r = resolve(src, frozenset({"A"}))
    assert [(e.kind, src[e.start:e.end]) for e in r.extras] == [
        ("comment", b"// top"), ("multiline_comment", b"/* in-arm */"), ("pragma", b"#pragma warning disable X"),
    ]


def test_leading_bom_is_kept():
    src = b"\xef\xbb\xbf#if A\nx;\n#endif\n"
    r = resolve(src, frozenset())
    assert r.masked == b"\xef\xbb\xbf" + b" " * 5 + b"\n" + b"  \n" + b" " * 6 + b"\n"


def test_active_marks_only_kept_lines():
    src = b"a;\n" + b"#if A\n" + b"b;\n" + b"#else\n" + b"c;\n" + b"#endif\n"
    r = resolve(src, frozenset({"A"}))
    expected = bytearray(len(src))
    expected[0:3] = b"\x01\x01\x01"    # "a;\n" — kept, top level
    expected[9:12] = b"\x01\x01\x01"   # "b;\n" — kept, if-arm taken
    assert r.active == expected


def test_nested_group_guarded_by_outer_inactive_even_when_inner_condition_true():
    # A is false (outer not taken) but B is true: the "here and" guard on the inner
    # #if must still keep it unreached, proving the guard isn't a no-op (unlike the
    # original fixture, which left both symbols unset and so couldn't tell).
    src = b"#if A\n#if B\nx;\n#endif\n#endif\n"
    r = resolve(src, frozenset({"B"}))
    assert r.masked.count(b"x;") == 0
    assert r.arm_choice == {0: None}


def test_nested_active_groups_arm_choice_for_both_levels():
    src = b"#if A\n#if B\nx;\n#endif\n#endif\n"
    r = resolve(src, frozenset({"A", "B"}))
    outer, inner = r.directives[0], r.directives[1]
    assert r.arm_choice == {outer.hash: outer.hash, inner.hash: inner.hash}


def test_arm_choice_points_at_chosen_elif_and_else_directives():
    src = b"#if X\na;\n#elif Y\nb;\n#else\nc;\n#endif\n"

    r_elif = resolve(src, frozenset({"Y"}))
    if_d, elif_d = r_elif.directives[0], r_elif.directives[1]
    assert r_elif.arm_choice == {if_d.hash: elif_d.hash}

    r_else = resolve(src, frozenset())
    if_d2, else_d2 = r_else.directives[0], r_else.directives[2]
    assert r_else.arm_choice == {if_d2.hash: else_d2.hash}


def test_define_inside_nested_inactive_arm_has_no_effect():
    src = b"#if A\n#if B\n#define C\n#endif\n#endif\n#if C\nx;\n#endif\n"
    r = resolve(src, frozenset({"A"}))  # B unset: inner arm carrying #define C is inactive
    assert r.masked.count(b"x;") == 0


def test_define_inside_nested_active_arm_takes_effect():
    src = b"#if A\n#if B\n#define C\n#endif\n#endif\n#if C\nx;\n#endif\n"
    r = resolve(src, frozenset({"A", "B"}))
    assert r.masked.count(b"x;") == 1


def test_extras_include_define_undef_region_endregion_when_active():
    src = b"#define A\n#undef A\n#region r\n#endregion\n"
    r = resolve(src, frozenset())
    assert [e.kind for e in r.extras] == [
        "preproc_define", "preproc_undef", "preproc_region", "preproc_endregion",
    ]


# ---- final review, finding 2: extra extents follow the grammar's token regexes ----
# `comment` is `//[^\n]*` (grammar.js), so on a CRLF line it INCLUDES the `\r`; the
# line-level directives (`pragma`, `preproc_region`, ...) are `[^\n\r]*` and do not.

def test_line_comment_event_on_crlf_runs_to_the_newline():
    src = b"x; // c\r\n#pragma warning disable X // y\r\n"
    ev = {e.kind: (e.start, e.end) for e in resolve(src, frozenset()).extras}
    assert ev["comment"] == (3, 8)          # includes the \r at 7
    assert ev["pragma"] == (9, 39)         # stops before the \r at 39


def test_group_of_maps_every_later_directive_to_its_if():
    src = b"#if A\nx\n#elif B\ny\n#else\nz\n#endif\n"
    res = resolve(src, frozenset())
    if_at = src.index(b"#if")
    for d in (b"#elif", b"#else", b"#endif"):
        assert res.group_of[src.index(d)] == if_at


def test_crlf_comment_trivia_is_clean_end_to_end(al_parser):
    from tools.config_oracle import runner
    src = b"codeunit 1 T\r\n{\r\n    trigger OnRun()\r\n    begin\r\n#if A\r\n        x := 1; // t\r\n#endif\r\n    end;\r\n}\r\n"
    recs = runner.check_input(al_parser, "crlf", src)
    assert [r.status for r in recs] == ["pass", "pass"], [r.items for r in recs]
