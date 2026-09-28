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
    assert case.id == "a.txt#0"


def test_source_with_no_blank_line_before_divider_has_no_trailing_newline(tmp_path):
    # 249 of 1,647 real cases have no blank line before their divider. The old
    # blanket-rstrip-then-append-"\n" reader fabricated a newline these cases
    # never had; test.rs's `input.pop()` just removes the one real byte.
    (tmp_path / "b.txt").write_bytes(b"=====\nName2\n=====\nabc\n-----\n\n(tree)\n")
    [case] = fixtures.extract(tmp_path)
    assert case.source == b"abc"
    assert case.offset == 18  # byte right after "=====\nName2\n=====\n"
    assert case.id == "b.txt#0"


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
