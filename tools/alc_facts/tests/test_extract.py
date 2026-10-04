"""The committed compiler facts match what ObjectParser/SyntaxFacts say (spec §2.1)."""
from tools.alc_facts import extract


def test_keyword_set_has_the_compiler_size_and_known_members():
    kws = extract.load_keywords()
    assert len(kws) == 99   # 101 IsKeywordAllowedIdentifier kinds, 99 distinct texts: field, filter twice
    for w in ("system", "table", "tabledata", "page", "codeunit", "field", "type",
              "filter", "order", "enum", "namespace", "group"):   # group = PageGroupKeyword
        assert w in kws
    for w in ("begin", "end", "where", "if", "else", "pagegroup"):
        assert w not in kws
    assert kws == sorted(set(kws))


def test_property_hosts_known_rows():
    rows = {(n, h): (vk, d) for n, h, vk, d in extract.load_property_hosts()}
    assert rows[("ENABLED", "PageField")][1] == "ParseClientSideBooleanExpressionPropertyValue"
    assert rows[("ENABLED", "Field")][1] == "ParseBooleanPropertyValue"
    assert rows[("INDENTATIONCOLUMN", "PageGroup")][1] == "ParseIntegerExpressionPropertyValue"
    assert rows[("AUTOFORMATEXPRESSION", "Field")][1] == "ParseTextExpressionPropertyValue"
    assert rows[("TABLERELATION", "Field")][1] == "ParseTableRelationPropertyValue"
    assert rows[("TABLERELATION", "PageField")][1] == "ParseTableRelationPropertyValue"
