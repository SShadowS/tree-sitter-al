import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def al_language():
    from tools.query_coverage import loader
    return loader.load_language(loader.ensure_library(loader.REPO_ROOT))


@pytest.fixture(scope="session")
def al_parser(al_language):
    from tools.query_coverage import loader
    return loader.make_parser(al_language)


from tools.config_oracle.ir import Node


def leaf(kind, start, end, named=False, field=None):
    return Node(kind, named, field, start, end, [])


def node(kind, *children, field=None, named=True):
    kids = list(children)
    return Node(kind, named, field, kids[0].start if kids else 0, kids[-1].end if kids else 0, kids)
