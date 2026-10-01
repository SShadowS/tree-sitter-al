"""tools/nodetypes.py on known types, and a diff that must find a change."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools import nodetypes  # noqa: E402


def test_show_known_type(capsys):
    assert nodetypes.main(["show", "additive_expression"]) == 0
    out = capsys.readouterr().out
    assert "  operator: multiple=False required=True" in out
    assert '    "+"' in out


def test_show_unknown_type_exits_1():
    assert nodetypes.main(["show", "no_such_node_type"]) == 1


def test_who_has_finds_anonymous_operator(capsys):
    assert nodetypes.main(["who-has", "+"]) == 0
    assert "additive_expression\toperator\t" in capsys.readouterr().out


def test_diff_reports_a_narrowed_field(capsys):
    new = nodetypes.load()
    old = [dict(e) for e in new]
    entry = next(e for e in old if e["type"] == "additive_expression")
    entry["fields"] = {**entry["fields"], "operator": {**entry["fields"]["operator"], "multiple": True}}
    assert nodetypes.diff(old, new) == 1
    assert "~ additive_expression.operator multiple: True -> False" in capsys.readouterr().out
    assert nodetypes.diff(new, new) == 0
