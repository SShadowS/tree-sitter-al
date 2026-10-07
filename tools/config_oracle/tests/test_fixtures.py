import pytest
from collections import Counter
from pathlib import Path

from tools import count_corpus_cases
from tools.config_oracle import fixtures

CORPUS = Path(__file__).resolve().parents[3] / "test" / "corpus"


def test_per_file_names_agree_with_the_independent_counter():
    ours = Counter((c.file, c.name) for c in fixtures.extract(CORPUS))
    theirs = Counter(count_corpus_cases.cases(CORPUS))
    assert ours == theirs


def test_source_is_the_input_block(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"=====\nName\n=====\nline1\nline2\n\n-----\n\n(tree)\n")
    [case] = fixtures.extract(tmp_path)
    # Raw slice from the end of the header to the start of the divider line,
    # minus exactly one trailing byte (test.rs's `input.pop()`) -- the blank
    # line before the divider survives as a single embedded "\n".
    assert case.source == b"line1\nline2\n"
    assert case.offset == 17  # byte right after "=====\nName\n=====\n"
    assert case.id == "a.txt#Name#0"


def test_source_with_no_blank_line_before_divider_has_no_trailing_newline(tmp_path):
    # 249 of 1,647 real cases have no blank line before their divider. The old
    # blanket-rstrip-then-append-"\n" reader fabricated a newline these cases
    # never had; test.rs's `input.pop()` just removes the one real byte.
    (tmp_path / "b.txt").write_bytes(b"=====\nName2\n=====\nabc\n-----\n\n(tree)\n")
    [case] = fixtures.extract(tmp_path)
    assert case.source == b"abc"
    assert case.offset == 18  # byte right after "=====\nName2\n=====\n"
    assert case.id == "b.txt#Name2#0"


def test_classes_file_parses():
    classes = fixtures.load_classes(Path(fixtures.__file__).with_name("fixture-classes.tsv"))
    assert isinstance(classes, dict)


def test_adversarial_corpus_features_reconcile_exactly(tmp_path):
    """A scratch corpus exercising every silent-drop trap and marker rule at
    once, cross-checked against test.rs (.cache/tree-sitter-0.25.10/cli/src/
    test.rs) and against the installed tree-sitter 0.27.0 CLI
    (`tree-sitter test --file-name`, run against this exact content copied
    temporarily into test/corpus, then removed -- not committed anywhere).
    """
    eq = "=" * 72
    dash = "-" * 72
    dash_trailing_spaces = dash + "   "  # built, not a literal trailing-whitespace
    # line in this source file -- editors/tools reliably strip those on save.
    content = f"""{eq}
Blank line breaks header

{eq}
Header with no divider
{eq}
notes without any divider afterwards, straight into next header

{eq}
Skip case
:skip
{eq}
body for skip case
{dash}
(ERROR)

{eq}
Not a skip via skipfoo
:skipfoo
{eq}
body not skip
{dash}
(ERROR)

{eq}
Error case
:error
{eq}
body error
{dash}
(ERROR)

{eq}
Platform windows case
:platform(windows)
{eq}
body platform
{dash}
(ERROR)

=====
Mismatched closer lengths
=======
body mismatched
{dash}
(ERROR)

{eq}
Divider with trailing spaces
{eq}
body trailing space divider
{dash_trailing_spaces}
(ERROR)

{eq}
Comment dash line then real divider
{eq}
/* comment
----
still comment
*/
al code here
{dash}
(ERROR)

{eq}
No blank line before divider
{eq}
tight body no blank line
{dash}
(ERROR)
"""
    (tmp_path / "adversarial.txt").write_bytes(content.encode("utf-8"))

    cases = fixtures.extract(tmp_path)
    ours = Counter((c.file, c.name) for c in cases)
    theirs = Counter(count_corpus_cases.cases(tmp_path))
    assert ours == theirs

    # Hand-derived from test.rs's rules, not from either reader's output:
    #   dropped (mechanism 1):        Blank line breaks header
    #   dropped (mechanism 2):        Header with no divider
    #   dropped (rejected divider):   Divider with trailing spaces
    #   excluded (:skip):             Skip case
    #   runs (":skipfoo" != ":skip"): Not a skip via skipfoo
    #   runs (:error still runs):     Error case
    #   runs (:platform(windows) matches this OS): Platform windows case
    #   runs (closer length is not tied to opener): Mismatched closer lengths
    #   runs (longest divider wins, not first):     Comment dash line then real divider
    #   runs (no blank line before divider):        No blank line before divider
    expected = Counter({
        ("adversarial.txt", "Not a skip via skipfoo"): 1,
        ("adversarial.txt", "Error case"): 1,
        ("adversarial.txt", "Platform windows case"): 1,
        ("adversarial.txt", "Mismatched closer lengths"): 1,
        ("adversarial.txt", "Comment dash line then real divider"): 1,
        ("adversarial.txt", "No blank line before divider"): 1,
    })
    assert ours == expected

    # The embedded 4-dash comment line must not pre-empt the real 72-dash
    # divider below it.
    [comment_case] = [c for c in cases if c.name == "Comment dash line then real divider"]
    assert comment_case.source == b"/* comment\n----\nstill comment\n*/\nal code here"

    [tight_case] = [c for c in cases if c.name == "No blank line before divider"]
    assert tight_case.source == b"tight body no blank line"


# ---- final review, finding 3: case ids do not shift when a case is inserted ----

def _corpus(tmp_path, *names):
    eq, dash = "=" * 10, "-" * 10
    (tmp_path / "c.txt").write_text("".join(f"{eq}\n{n}\n{eq}\nx;\n{dash}\n\n(t)\n\n" for n in names))
    return [c.id for c in fixtures.extract(tmp_path)]


def test_case_id_is_name_and_ordinal_among_same_named_cases(tmp_path):
    assert _corpus(tmp_path, "A", "B", "A") == ["c.txt#A#0", "c.txt#B#0", "c.txt#A#1"]


def test_inserting_a_case_does_not_shift_later_ids(tmp_path):
    before = _corpus(tmp_path, "A", "B")
    after = _corpus(tmp_path, "New", "A", "B")
    assert after[1:] == before


def test_case_id_escapes_separators(tmp_path):
    assert _corpus(tmp_path, "a#b|c%d") == ["c.txt#a%23b%7Cc%25d#0"]


def _classes(tmp_path, line):
    p = tmp_path / "classes.tsv"
    p.write_text("# header\n" + line + "\n", encoding="utf-8")
    return fixtures.load_classes(p)


def test_classes_require_a_cannot_validate_reason_prefix(tmp_path):
    ok = _classes(tmp_path, "c.txt#A#0\t*\tcannot-validate:reference-error\tdebt(C1): no handler")
    assert ok == {("c.txt#A#0", "*"): ("cannot-validate:reference-error", "debt(C1): no handler")}
    for bad in ("discrepancy", "cannot-validate", "cannot-validate:", "pass:x", "representation-violation:x"):
        with pytest.raises(ValueError):
            _classes(tmp_path, f"c.txt#A#0\t*\t{bad}\treason")


def test_classes_accept_a_hyphenated_b7b_owner(tmp_path):
    ok = _classes(tmp_path, "c.txt#A#0\t*\tcannot-validate:resolver\tdebt(B7b-3): the fixed `;` of a move")
    assert ok[("c.txt#A#0", "*")][1].startswith("debt(B7b-3)")
    with pytest.raises(ValueError, match="not a roadmap sub-project"):
        _classes(tmp_path, "c.txt#A#0\t*\tcannot-validate:resolver\tdebt(B7b-9): no such sub-project")


def test_classes_require_a_reason(tmp_path):
    with pytest.raises(ValueError):
        _classes(tmp_path, "c.txt#A#0\t*\tcannot-validate:resolver\t ")


# ---- categories and evidence (A3 fix round 1, review F1) ----

NEG_CASE = "tools/alc_probe/cases/oracle-negative/split-operator.al"   # X: accept; !X: reject
NEG_ID = "preproc_split_operator_test.txt#An OPERATOR alone in a %23if arm: the operand follows %23endif#0"


def test_classes_require_a_category(tmp_path):
    with pytest.raises(ValueError, match="must start with"):
        _classes(tmp_path, "c.txt#A#0\t*\tcannot-validate:resolver\tdeliberate negative")


@pytest.mark.parametrize("category", ["negative", "invalid-config"])
def test_rejection_claims_need_evidence(tmp_path, category):
    with pytest.raises(ValueError, match="evidence"):
        _classes(tmp_path, f"c.txt#A#0\tX=0\tcannot-validate:resolver\t{category}: alc rejects it")


def test_a_star_negative_cannot_rest_on_a_manual_note(tmp_path):
    line = "c.txt#A#0\t{}\tcannot-validate:resolver\tnegative: AL0621; evidence: alc manual, 2026-09-29"
    assert _classes(tmp_path, line.format("-"))
    with pytest.raises(ValueError, match="needs alc_probe evidence"):
        _classes(tmp_path, line.format("*"))


def test_probe_alc_evidence_must_name_a_recorded_reject(tmp_path):
    """B2 review M5: `evidence: probe_alc <name>` is checked against probe_alc.PROBES."""
    line = "c.txt#A#0\t{}\tcannot-validate:resolver\tnegative: AL0631; evidence: probe_alc {}"
    assert _classes(tmp_path, line.format("-", "endif_semicolon_rejected"))
    with pytest.raises(ValueError, match="not in probe_alc.PROBES"):
        _classes(tmp_path, line.format("-", "no_such_probe"))
    with pytest.raises(ValueError, match="expects an ACCEPT"):
        _classes(tmp_path, line.format("-", "endregion_semicolon_accepted"))
    with pytest.raises(ValueError, match="not one raw compile"):
        _classes(tmp_path, line.format("*", "endif_semicolon_rejected"))


def test_a_star_negative_over_a_configuration_alc_accepts_is_rejected(tmp_path):
    """The F1 defect: `*` claimed X=1 was rejected, and alc accepts it."""
    line = (f"{NEG_ID}\t{{}}\tcannot-validate:multi-config-parse:error\tnegative: x; "
            f"evidence: alc_probe {NEG_CASE}")
    assert _classes(tmp_path, line.format("X=0"))
    for cfg in ("*", "X=1"):
        with pytest.raises(ValueError, match="does not expect a reject"):
            _classes(tmp_path, line.format(cfg))


def test_evidence_must_exist_and_name_the_configs_symbols(tmp_path):
    line = NEG_ID + "\t{}\tcannot-validate:x\tinvalid-config: x; evidence: alc_probe {}"
    with pytest.raises(ValueError, match="does not exist"):
        _classes(tmp_path, line.format("X=0", "tools/alc_probe/cases/no-such.al"))
    with pytest.raises(ValueError, match="does not name the symbols"):
        _classes(tmp_path, line.format("Y=0", NEG_CASE))


def test_evidence_must_be_the_probe_for_this_fixture(tmp_path):
    """Re-review m1: X=0 pointed at an unrelated probe that also uses X, and rejects X=0,
    was accepted on the path alone."""
    other = "tools/alc_probe/cases/oracle-invalid-config/13-g6-pragma-only-arm.al"
    line = f"{NEG_ID}\tX=0\tcannot-validate:multi-config-parse:error\tnegative: x; evidence: alc_probe {{}}"
    assert _classes(tmp_path, line.format(NEG_CASE))
    with pytest.raises(ValueError, match="is the probe for"):
        _classes(tmp_path, line.format(other))
