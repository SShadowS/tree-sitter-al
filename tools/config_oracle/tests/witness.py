"""Witness helpers: run the whole oracle over one AL source in every configuration."""
from __future__ import annotations

from tools.config_oracle import runner


def verdicts(parser, src, input_id="witness"):
    return {r.config: (r.status, list(r.items)) for r in runner.check_input(parser, input_id, src)}


def assert_all_pass(parser, src):
    v = verdicts(parser, src)
    bad = {c: s for c, s in v.items() if s[0] != "pass"}
    assert v, "no configuration was checked"
    assert not bad, bad


def statuses_with(parser, src, prefix):
    return sorted(c for c, (_, items) in verdicts(parser, src).items()
                  if any(i.startswith(prefix) for i in items))


def assert_produces(parser, src, kind):
    """The witness must actually produce the special type it claims to test (base §5)."""
    stack = [parser.parse(src).root_node]
    while stack:
        n = stack.pop()
        if n.type == kind:
            return
        stack.extend(n.children)
    raise AssertionError(f"source does not produce {kind}")
