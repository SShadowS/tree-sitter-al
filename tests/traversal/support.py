"""Shared by conftest.py and regen_expected.py: paths, the module under test, a parser.

The traversal module is loaded BY PATH, not imported as tree_sitter_al.traversal:
importing the package runs tree_sitter_al/__init__.py, which needs the compiled
_binding extension, and these tests use the repo's own parser library instead
(tools/query_coverage/loader.py, the same one every other Python gate uses).
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FIXTURES = HERE / "fixtures"
MODULE = REPO / "bindings" / "python" / "tree_sitter_al" / "traversal.py"
POLICY = REPO / "traversal" / "policy.json"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def load_traversal():
    name = "tree_sitter_al_traversal"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, MODULE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module          # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(module)
    return module


def make_parser():
    from tools.query_coverage import loader
    return loader.make_parser(loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
