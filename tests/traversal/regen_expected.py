#!/usr/bin/env python3
"""Rewrite tests/traversal/fixtures/*.visits.json (and assemblers.arm_pieces.json) from the Python walker.

The same trap as `tree-sitter test -u`: this blesses whatever the walker does today.
Run it only after a deliberate change, then read `git diff tests/traversal/fixtures`
hunk by hunk and trace each one to that change. The hand-written tests in
test_walk.py, test_split.py and test_witnesses.py are what say the walker is RIGHT;
these files only make the three runtimes agree with it.

    python tests/traversal/regen_expected.py
"""
import support

ARM_PIECES_FIXTURE = "assemblers.al"   # arm_pieces (Task 8b): the fixture with fragments in arms

T = support.load_traversal()
policy = T.load_policy(support.POLICY)
parser = support.make_parser()
for path in sorted(support.FIXTURES.glob("*.al")):
    source = path.read_bytes()
    doc = T.Document(parser.parse(source), source, policy)
    out = path.with_suffix(".visits.json")
    out.write_text(T.dump_expected(doc, T.walk(doc, policy)), encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(support.REPO).as_posix()}")
    if path.name == ARM_PIECES_FIXTURE:
        out = path.with_suffix(".arm_pieces.json")
        out.write_text(T.arm_pieces_to_json(doc, T.walk(doc, policy), policy), encoding="utf-8", newline="\n")
        print(f"wrote {out.relative_to(support.REPO).as_posix()}")
