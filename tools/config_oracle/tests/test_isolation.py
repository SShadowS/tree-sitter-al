import ast
from pathlib import Path

LOWERING = Path(__file__).resolve().parents[1] / "lowering"


def test_lowering_never_imports_reference_or_a_parser():
    files = list(LOWERING.glob("*.py"))
    assert files
    for py in files:
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            names = []
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                names = [n.module or ""] + [f"{n.module}.{a.name}" for a in n.names]
            for name in names:
                assert "reference" not in name and "tree_sitter" not in name and "loader" not in name, (py, name)


def test_lowering_runs_with_parsers_disabled(al_parser, monkeypatch):
    """Spec: isolation is necessary-not-sufficient; this proves no parse call happens at runtime."""
    import tree_sitter

    from tools.config_oracle import ir
    from tools.config_oracle.directives import resolve
    from tools.config_oracle.lowering import lower_tree
    from tools.config_oracle.tests.test_lowering_select import STMT

    root, extras, _ = ir.from_tree(al_parser.parse(STMT))

    def boom(*a, **k):
        raise AssertionError("lowering invoked a parser")

    monkeypatch.setattr(tree_sitter.Parser, "parse", boom)
    lower_tree(root, extras, resolve(STMT, frozenset({"A"})))
