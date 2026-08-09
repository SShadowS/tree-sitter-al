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
