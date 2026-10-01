"""The shared expected-visit files (D4): one per fixture, current with the Python walker.

JS (tests/traversal/js/parity.test.js) and Rust (bindings/rust/traversal.rs) compare
their own walks against the same files, so the three runtimes agree byte for byte
on class, type, field, offsets, arm identity, host policy and SplitInfo.
"""
import json

import pytest

import support

ALS = sorted(support.FIXTURES.glob("*.al"))


def test_every_fixture_has_an_expected_file_and_no_file_is_orphaned():
    assert len(ALS) == 12
    assert sorted(p.stem for p in support.FIXTURES.glob("*.visits.json")) == \
        sorted(p.stem + ".visits" for p in ALS)


@pytest.mark.parametrize("path", ALS, ids=[p.name for p in ALS])
def test_expected_visits_are_current(T, policy, al_parser, path):
    source = path.read_bytes()
    doc = T.Document(al_parser.parse(source), source, policy)
    want = path.with_suffix(".visits.json").read_text(encoding="utf-8")
    got = T.dump_expected(doc, T.walk(doc, policy))
    assert got == want, f"{path.name}: run tests/traversal/regen_expected.py, then review the diff"
    assert json.loads(want)["revision"] == doc.revision
