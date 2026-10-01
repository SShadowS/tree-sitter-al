import pytest

import support


@pytest.fixture(scope="session")
def T():
    return support.load_traversal()


@pytest.fixture(scope="session")
def policy(T):
    return T.load_policy(support.POLICY)


@pytest.fixture(scope="session")
def al_parser():
    return support.make_parser()


@pytest.fixture(scope="session")
def parse(T, policy, al_parser):
    """A fixture file under tests/traversal/fixtures -> Document."""
    def _parse(name):
        src = (support.FIXTURES / name).read_bytes()
        return T.Document(al_parser.parse(src), src, policy)
    return _parse


@pytest.fixture(scope="session")
def corpus():
    from tools.config_oracle import fixtures
    return {c.id: c for c in fixtures.extract(support.REPO / "test" / "corpus")}


@pytest.fixture(scope="session")
def doc_of(T, policy, al_parser, corpus):
    """`corpus:<Case.id>` or `fixture:<file>` -> Document. A witness must parse clean."""
    def _doc(spec):
        kind, _, ref = spec.partition(":")
        src = corpus[ref].source if kind == "corpus" else (support.FIXTURES / ref).read_bytes()
        tree = al_parser.parse(src)
        assert not tree.root_node.has_error, f"witness {spec} has an ERROR or MISSING node"
        return T.Document(tree, src, policy)
    return _doc
