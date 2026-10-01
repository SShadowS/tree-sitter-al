"""tools/snip.py: exit codes, error positions, --sexp == what `tree-sitter test` compares."""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools import snip  # noqa: E402
from tools.query_coverage import loader  # noqa: E402

SCRIPT = REPO / "tools" / "snip.py"


def run(*args):
    p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return p.returncode, p.stdout


def test_clean_snippet_exits_0():
    code, out = run("x := a + 1;")
    assert code == 0
    assert 'operator: "+"' in out  # a field on an anonymous child, which parse -c hides
    assert "has_error: False" in out


def test_error_snippet_exits_1_with_snippet_position():
    code, out = run("x := 1;\\nx := ;")
    assert code == 1
    assert re.search(r"^ERROR\t2:3-2:5\t", out, re.M), out


def test_missing_is_listed():
    code, out = run("x := (1;")
    assert code == 1
    assert re.search(r"^MISSING\t1:8-1:8\t\)$", out, re.M), out


def test_sexp_is_ts_node_string():
    """tree-sitter test compares against ts_node_string; py-tree-sitter's str(node) is it."""
    parser = loader.make_parser(loader.load_language(loader.ensure_library(REPO)))
    for text in ("x := a + 1;", "x := (1;", "if A then\n#if X\nB;\n#else\nC;\n#endif"):
        tree = parser.parse(snip.wrap(text, "statement")[0].encode())
        assert " ".join(snip.sexp(tree).split()) == str(tree.root_node)


def test_flag_finds_a_two_shape_keyword_only():
    total = Counter({("object_type_keyword", 0, 1): 5, ("object_type_keyword", 0, 0): 2,
                     ("call_expression", 2, 0): 1, ("call_expression", 1, 0): 1})
    assert snip.flag(total)[1] == ["object_type_keyword"]


def test_census_missing_root_cannot_run(tmp_path):
    code, _ = run("--census", "--root", str(tmp_path / "nope"))
    assert code == 2
