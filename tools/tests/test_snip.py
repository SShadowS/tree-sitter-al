"""tools/snip.py: exit codes, error positions, encodings, --sexp == what `tree-sitter test` compares."""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools import snip  # noqa: E402
from tools.config_oracle import fixtures  # noqa: E402
from tools.query_coverage import loader  # noqa: E402

SCRIPT = REPO / "tools" / "snip.py"


def run(*args, stdin=None):
    p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, input=stdin)
    return p.returncode, p.stdout.decode("utf-8").replace("\r\n", "\n")


def test_clean_snippet_exits_0():
    code, out = run("x := a + 1;")
    assert code == 0
    assert 'operator: "+"' in out  # a field on an anonymous child, which parse -c hides
    assert "has_error: False" in out


def test_error_snippet_exits_1_with_snippet_position():
    code, out = run(r"x := 1;\nx := ;")
    assert code == 1
    assert re.search(r"^ERROR\t2:3-2:5\t", out, re.M), out


def test_missing_is_listed():
    code, out = run("x := (1;")
    assert code == 1
    assert re.search(r"^MISSING\t1:8-1:8\t\)$", out, re.M), out


def test_position_in_the_wrapper_tail_is_labelled():
    code, out = run("if a then begin")
    assert code == 1
    assert re.search(r"^MISSING\twrapper \d+:\d+-wrapper \d+:\d+\tend_keyword$", out, re.M), out


def test_piped_output_is_utf8():
    """A cp1252 stdout crashed on text outside it."""
    code, out = run("x := 'Привет→'; y := ;")
    assert code == 1
    assert "'Привет→'" in out


def test_stdin_is_utf8_and_columns_are_bytes():
    """stdin was decoded as cp1252, which put the ERROR 2 columns late (1:16)."""
    code, out = run("-", stdin="x := 'æ'; y := ;".encode("utf-8"))
    assert code == 1
    assert re.search(r"^ERROR\t1:14-1:16\t", out, re.M), out


def test_file_is_read_as_bytes_with_no_cr_translation(tmp_path):
    """A lone CR is not a line break to tree-sitter; text mode made it one (2:3).
    The UTF-8 BOM is stripped, so it shifts nothing."""
    f = tmp_path / "s.al"
    f.write_bytes(b"\xef\xbb\xbfx := 1;\rx := ;")
    code, out = run("-f", str(f))
    assert code == 1
    assert re.search(r"^ERROR\t1:11-1:13\t", out, re.M), out


PARSER = None


def parse(source: bytes):
    global PARSER
    PARSER = PARSER or loader.make_parser(loader.load_language(loader.ensure_library(REPO)))
    return PARSER.parse(source)


def test_sexp_is_ts_node_string_on_every_corpus_case():
    """tree-sitter test compares against ts_node_string (to_sexp); str(node) is it."""
    cases = fixtures.extract(REPO / "test" / "corpus")
    assert len(cases) > 1000
    for c in cases:
        tree = parse(c.source)
        assert " ".join(snip.sexp(tree).split()) == str(tree.root_node), c.id


def test_sexp_keeps_unexpected():
    """A rebuilt s-expression printed (ERROR (ERROR)) here; ts_node_string does not."""
    tree = parse(snip.wrap("x := 1 $ 2;", "statement")[0].encode())
    out = snip.sexp(tree)
    assert "(UNEXPECTED '$')" in out
    assert " ".join(out.split()) == str(tree.root_node)


def test_pretty_sexp_keeps_parentheses_inside_quoted_tokens():
    flat = '(a (MISSING ")") f: (UNEXPECTED \'(\') (b (MISSING c)))'
    assert " ".join(snip.pretty_sexp(flat).split()) == flat


class Stub:
    def __init__(self, type, start, children=(), has_error=False, is_error=False, is_missing=False):
        self.type, self.start_byte, self.children = type, start, list(children)
        self.has_error, self.is_error, self.is_missing = has_error, is_error, is_missing


def test_hidden_missing_site_is_reported():
    """A MISSING hidden token: its parent has has_error, but no child of it shows one."""
    hidden_site = Stub("preproc_if", 5, [Stub("identifier", 9)], has_error=True)
    root = Stub("source_file", 0, [Stub("identifier", 0), hidden_site], has_error=True)
    tree = type("T", (), {"root_node": root})()
    assert [(k, n.type) for k, n in snip.problems(tree)] == [("HIDDEN", "preproc_if")]


def test_flag_finds_a_two_shape_keyword_only():
    total = Counter({("object_type_keyword", 0, 1): 5, ("object_type_keyword", 0, 0): 2,
                     ("call_expression", 2, 0): 1, ("call_expression", 1, 0): 1})
    assert snip.flag(total)[1] == ["object_type_keyword"]


def test_census_missing_root_cannot_run(tmp_path):
    code, _ = run("--census", "--root", str(tmp_path / "nope"))
    assert code == 2
