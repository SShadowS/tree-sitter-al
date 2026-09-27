import pytest

from tools.config_oracle.directives import ResolveError, evaluate, parse_condition


def cond(text: str):
    b = text.encode()
    return parse_condition(b, 0, len(b))


@pytest.mark.parametrize("text,env,expected", [
    ("A and B", {"A", "B"}, True),
    ("A and B", {"A"}, False),
    ("A AND B", {"A", "B"}, True),
    ("A or B", {"B"}, True),
    ("A or B", set(), False),
    ("not A", set(), True),
    ("NOT A", set(), True),
    ("not A", {"A"}, False),
    ("(A)", {"A"}, True),
    ("true", set(), True),
    ("TRUE", set(), True),
    ("false", set(), False),
    ("A or B and C", {"A"}, True),       # prec_or_and
    ("A and B or C", {"C"}, True),       # prec_and_or: and binds tighter
    ("not A and B", set(), False),       # prec_not_and: (not A) and B
    ("not not A", {"A"}, True),
    ("not (A or B)", set(), True),
    ("CLEAN25", {"CLEAN25"}, True),
    ("_X1", {"_X1"}, True),
])
def test_semantics_table(text, env, expected):
    assert evaluate(cond(text).expr, frozenset(env)) is expected


def test_symbols_are_case_sensitive():
    assert evaluate(cond("foo").expr, frozenset({"FOO"})) is False


@pytest.mark.parametrize("text,reason", [
    ("A && B", "unsupported-condition-token"),
    ("A || B", "unsupported-condition-token"),
    ("!A", "unsupported-condition-token"),
    ("A == B", "unsupported-condition-token"),
    ("A xor B", "unsupported-condition"),
    ("A B", "unsupported-condition"),
    ("", "empty-condition"),
    ("   // only a comment", "empty-condition"),
    ("A /* c */", "block-comment-on-directive"),
    ("and", "unsupported-condition"),   # a symbol spelled like an operator: not established, fail closed
])
def test_rejections_fail_closed(text, reason):
    with pytest.raises(ResolveError) as err:
        cond(text)
    assert err.value.reason == reason


def test_extent_excludes_whitespace_and_line_comment():
    line = b"  not (A or B)   // note"
    c = parse_condition(line, 0, len(line))
    assert line[c.start:c.end] == b"not (A or B)"
    assert c.symbols == frozenset({"A", "B"})
