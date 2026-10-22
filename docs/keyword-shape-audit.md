# Keyword node shapes: the 4.0.0 audit

Carried out of `CLAUDE.md` and `.claude/rules/contextual-keywords.md` on 2026-10-21. The
rules those files keep are one line each; this is the record of how the two-shape defects
were found, measured and fixed, and why the fixes have the form they have. Counts are the
BC.History measurements of 4.0.0 (15,358 files); re-measure before quoting.

## The contract

Every grammar keyword rule has the same shape: exactly one anonymous child, typed as the
canonical lowercase spelling.

```javascript
table_keyword: $ => alias(kw('table'), 'table'),          // anonymous "table" child
procedure_keyword: $ => alias(kw('procedure'), 'procedure'),
if_keyword: $ => prec(10, alias(kw('if'), 'if')),         // anonymous "if" child
enum_keyword: $ => prec(10, kwCases('enum', 'enum', 'ENUM', 'Enum', 'eNUM', 'eNum', 'ENum')),
```

| body | child | count (4.0.0) |
|---|---|---|
| `alias(kw('word'), 'word')` → STRING | one anonymous child typed `"word"` | 139 |
| `kwCases('word', …)` → STRING, each spelling aliased to `'word'` | one anonymous child typed `"word"` | 13 |
| external scanner token (`begin_keyword`, `end_keyword`) | none — cannot take a child | 2 |

The child's type is always the canonical lowercase spelling regardless of how the source
spelled the keyword: `XmlPort` yields `(xmlport_keyword "xmlport")`, and the node's own text
is still `XmlPort`.

**Why the shape is decided by the token.** A named rule whose entire body is a single token
collapses *into* that token, so the node's shape is decided by that token's visibility. A bare
`kw('word')` builds a `token(PATTERN)`, and tree-sitter renders anonymous *pattern* tokens as
hidden `aux_sym_*` symbols (`.visible = false`), unlike anonymous *string* tokens such as
`";"`, which are visible. So a bare `kw()` yields a **childless leaf**; wrapping it in
`alias(…, 'word')` makes the token a visible STRING and yields **one anonymous child**. Before
4.0.0 the grammar mixed both, so a consumer could not predict a keyword's shape.

**`node-types.json` cannot confirm this.** It lists anonymous children only when they sit
inside a field, and none of these do, so all keyword nodes look childless there regardless of
their real shape. Read a keyword's text from the node itself, never by descending into a
child; that stays correct for the two external tokens and survives any change to the
anonymous layer.

## begin/end: why the depth guard was wrong

Until 4.0.0 `BEGIN_KEYWORD`/`END_KEYWORD` were guarded by `state->depth == 0`, and the depth > 0
case handed off to an anonymous `kw('begin')`. That made a complete `begin … end` inside any
`#if` block **vanish from the tree**: the pattern token was lexed and then dropped, so the CST
was not lossless over the source and both keywords were unhighlightable inside every `#if`.
Now `begin_keyword`/`end_keyword` are emitted at **every** depth, `grammar.js` has no
`kw('begin')`/`kw('end')` fallback (so there is no scanner/literal pair for GLR to fork on),
and the depth counter decides only whether a `PREPROC_SPLIT_*` token gets first refusal. Both
decisions happen in **one** scan: the scanner reads the keyword, calls `mark_end`, runs the
split lookahead, and picks the symbol from the result. Direct naming via grammar rules or
`alias()` still breaks GLR backtracking; the stateful scanner is the correct approach
(`docs/superpowers/specs/2026-03-24-stateful-scanner-begin-end-design.md`).

## `object_type_keyword`: one node type, two shapes

`node-types.json` contains one more named `*_keyword` type than there are keyword rules:
`object_type_keyword` has no rule of its own. `database_reference` builds it by aliasing a
`choice` of six alternatives (`grep -n "object_type_keyword" grammar.js`). Five were named
`$.*_keyword` rules carrying visible aliased STRING tokens while the sixth was a bare
`kw('database')`, a hidden pattern token, so one node type shipped two shapes decided purely
by which word the source used:

```
(object_type_keyword text='Page')      children=[("page", anonymous)]
(object_type_keyword text='DATABASE')  children=[]                     <- childless
```

Measured over BC.History: **22,988 of 40,674 `object_type_keyword` nodes were the childless
kind**, every `DATABASE::` in the corpus answering differently from its siblings. Fixed by
giving `database` a real `database_keyword` rule like the other five. All 40,674 now have
exactly one anonymous child.

**The nested form does not work, and the fixture pins that.**
`alias(alias(kw('database'), 'database'), $.object_type_keyword)` looks equivalent and is not:
the two aliases do not compose, the DATABASE case loses its `object_type_keyword` node
entirely, and the `keyword` field points straight at an anonymous token.
`test/corpus/object_type_keyword_uniform_shape_test.txt` fails on exactly that.

## `keyword_identifier`: the same defect one level up

`keyword_identifier` accepts thirteen words; six were named `*_keyword` rules and seven were
bare `kw()`, so `Codeunit.Run()` gave `(keyword_identifier (codeunit_keyword))` while
`Record.Get()` gave a childless `(keyword_identifier)`. All thirteen are now named rules;
`test/corpus/keyword_identifier_uniform_shape_test.txt` pins the shape, and unlike the
`object_type_keyword` fixture it really does, because these children are *named* and corpus
expected trees show named children.

## `keyword_as_identifier`: the opposite direction

`keyword_as_identifier` is consumed only as `alias($.keyword_as_identifier, $.identifier)`,
so the node claims to be an `identifier`, and an `identifier` is a leaf everywhere else.
`key`, `dataset` and `table` were named `$.x_keyword` alternatives there and gave that
"identifier" a child no other identifier has:

```
parameter name: identifier            <- `Type`, bare kw('type')   leaf, correct
parameter name: identifier
                  key_keyword         <- `Key`,  $.key_keyword     named child
                    "key"
```

Measured over BC.History before the fix, `identifier` had **four** distinct shapes: 5,906,275
leaves, plus 2,151 with a `table_keyword` child, 42 with `key_keyword`, 12 with
`dataset_keyword`. Afterwards, one shape: all 5,908,480 are leaves. **2,151 of 4,524
`table_keyword` nodes in the corpus, 47.5%, were not the `table` keyword at all.**

**It also mis-highlighted.** `queries/highlights.scm` matches bare `(table_keyword)`,
`(key_keyword)` and `(dataset_keyword)` patterns with no parent context, so those nodes
matched and a parameter named `Table` was captured as **both** `@variable.parameter` and
`@keyword.type`, 2,151 times corpus-wide. Demoting the three fixes the highlight; the patterns
keep working at real keyword sites because all three rules are still referenced elsewhere.

So the direction of a fix is decided by what the outer node claims to be: `keyword_identifier`
and `object_type_keyword` claim "a keyword stands here" and the bare ones were **promoted**;
`keyword_as_identifier` claims to be an `identifier` and the named ones were **demoted**.

## Converting a bare `kw()` to `alias(kw(w), w)` cannot steal a spelling

`kw(w)` is `token(RustRegex('(?i)w'))` and `alias()` wraps that same token, so matching is
unchanged. Verified over BC.History rather than argued: the `identifier` node count was
5,908,480 before and after, and the full `(parent, field, child)` edge census was
byte-identical (13,339,003 fielded edges, 911 kinds). The `kwCases()` whitelist argument does
**not** apply to such a conversion: `kwCases()` exists to stop `kw()` from *widening* a
compound keyword over spellings AL uses as identifiers, and an alias widens nothing.

## `tabledata_keyword`

Until the losslessness pass this was `_tabledata_keyword`, a hidden rule over a bare `kw()`,
and the largest single byte-gap cluster left after the type keywords (23,481 occurrences
across BC.History). It is now a visible `tabledata_keyword` rule with the uniform shape; the
`option_member` site aliases it to `$.identifier`, which keeps the option-member node an
`identifier` but gives it an anonymous `"tabledata"` child, the one remaining two-shape
`identifier` (`docs/deferred-work.md` item 27; the comment at the rule in `grammar.js`).

## Why no gate caught any of this

Neither defect was a byte gap, so `qc` reported nothing for either: the outer node covered
the bytes, and both survived the losslessness work that drove gap clusters to zero. They were
*shape* inconsistencies. The instrument that shows this class is a tree-cursor walk
(`tools/fieldwalk.c`), and the corpus-wide form is a census keyed by `(type, child count)`:
`python tools/snip.py --census --root ./BC.History`.
