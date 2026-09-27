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


def test_directive_after_code_is_not_a_directive_and_fails_closed_only_if_unbalanced():
    r = resolve(b"x; #if A\ny;\n", frozenset({"A"}))
    assert r.directives == []


@pytest.mark.parametrize("src,reason", [
    (b"#if A\nx;\n", "unbalanced-if"),
    (b"#endif\n", "unbalanced-endif"),
    (b"#if A\n#else B\n#endif\n", "trailing-token"),
    (b"#if A\n#endif /* c */\n", "block-comment-on-directive"),
    (b"#ifx A\n#endif\n", "unknown-directive"),
    (b"#if A\n#else\n#elif B\n#endif\n", "elif-after-else"),
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
    assert resolve(src, frozenset()).masked.startswith(b"\xef\xbb\xbf")
