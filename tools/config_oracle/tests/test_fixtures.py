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
    assert case.source == b"line1\nline2\n"
    assert case.id == "a.txt#0"


def test_classes_file_parses():
    classes = fixtures.load_classes(Path(fixtures.__file__).with_name("fixture-classes.tsv"))
    assert isinstance(classes, dict)
