import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def al_parser():
    """A tree-sitter Parser bound to the freshly built local grammar."""
    from tools.query_coverage import loader

    lib = loader.ensure_library(loader.REPO_ROOT)
    language = loader.load_language(lib)
    return loader.make_parser(language)


@pytest.fixture(scope="session")
def al_language():
    from tools.query_coverage import loader

    lib = loader.ensure_library(loader.REPO_ROOT)
    return loader.load_language(lib)


@pytest.fixture(scope="session")
def node_types():
    """The SHIPPED src/node-types.json, for tests that must not run against a
    hand-written stand-in — a detector reading the declared universe can go
    vacuous against real data while every fake-input test still passes."""
    import json

    from tools.query_coverage import loader

    return json.loads(
        (loader.REPO_ROOT / "src" / "node-types.json").read_text(encoding="utf-8")
    )
