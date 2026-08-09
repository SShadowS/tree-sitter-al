from tools.query_coverage import lexer


def kinds(source: str) -> list[str]:
    return [span.kind for span in lexer.scan(source)]


def test_single_quoted_string():
    assert kinds("x := 'hello';") == ["string"]


def test_doubled_quote_escape_does_not_end_the_string():
    spans = lexer.scan("x := 'it''s';")

    assert len(spans) == 1
    assert spans[0].end == len("x := 'it''s'")


def test_quoted_identifier():
    assert kinds('x := "My Field";') == ["string"]


def test_line_comment():
    assert kinds("x := 1; // trailing\ny := 2;") == ["comment"]


def test_block_comment():
    assert kinds("x /* mid */ := 1;") == ["comment"]


def test_directive_line():
    assert kinds("#if CLEAN24\nx := 1;\n#endif\n") == ["directive", "directive"]


def test_string_inside_comment_is_not_a_string():
    assert kinds("// it's fine\n") == ["comment"]


def test_comment_marker_inside_string_is_not_a_comment():
    assert kinds("x := '// not a comment';") == ["string"]


def test_is_code_excludes_span_interiors():
    source = "field(1; N; Text[5]) // field(999)"
    spans = lexer.scan(source)

    assert lexer.is_code(spans, source.index("field(1"))
    assert not lexer.is_code(spans, source.index("field(999"))


def test_unterminated_string_runs_to_end_of_input():
    spans = lexer.scan("x := 'oops")

    assert len(spans) == 1
    assert spans[0].end == len("x := 'oops")
