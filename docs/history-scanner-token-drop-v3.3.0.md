# Source text that lands in no node

> **HISTORICAL — the numbers here are pre-4.0.0 and are not current.** This is the
> measurement that started the losslessness work; 4.0.0 fixed the classes it
> describes. Kept for the *method* (walk the tree, collect every leaf's byte range,
> report uncovered non-whitespace runs), which is reusable and is what
> `tools/validate_al_file.py` and the query-coverage harness now automate. See
> [`deferred-work.md`](deferred-work.md).

Found on 2026-08-09 while porting the queries to nvim-treesitter.

Measured against the **released v3.3.0 tag** (`77c14b2f`), compiled from GitHub by
`nvim-treesitter`'s own installer, so this is what a consumer of the published
parser sees — not the working tree.

## How it was measured

Walk the tree, collect every leaf node's byte range, and report any run of
non-whitespace source bytes that no leaf covers. Comments are extras and are
themselves leaves, so they count as covered. Anything left over is text the tree
does not account for.

Over the first 500 files of `BC.History`:

```
files parsed: 500, with dropped text: 495, errored: 0
     47237  "Record"
     22964  ":="
     11111  "Code"
      4924  "TestPage"
      2703  "of"
      2478  "array"
      1519  "Text"
       528  "+="
       517  "end"
       516  "begin"
       398  "Option"
       382  "field"
       248  "TestRequestPage"
       158  "List"
       128  "TableData"
        85  "action"
        48  "content"
        45  "-="
        40  "Dictionary"
        40  "value"
        27  "Array"
        27  "tabledata"
        25  "record"
        24  "where"
        19  "label"
        17  "processing"
        17  "actionref"
        16  "testpage"
        15  "code"
        12  "lookup"
         9  "modify"
         8  "Promoted"
         7  "Processing"
         6  "sorting"
         6  "*="
         5  "<>"
         5  "const"
         4  "addafter"
         4  "textelement"
         4  "Content"
```

495 of 500 real files contain text the tree cannot see. There are two separate
causes.

---

## 1. Keywords and operators used inline are invisible tokens

This accounts for everything in the table except `begin` and `end`.

tree-sitter only creates an anonymous node for a token written as a **string
literal** in a rule. A token produced by a regex, or by `token(choice(...))`, has
no string identity, so it becomes an unnamed terminal and never appears in the
tree. The only way such a token becomes visible is by giving it a named rule of
its own.

`grammar.js` does both, and the split lines up exactly with the measurement:

```js
// Case-insensitive keyword via regex
function kw(word, precedence = null) {
  const regex = new RustRegex(`(?i)${word}`);
  return precedence !== null ? token(prec(precedence, regex)) : token(regex);
}
```

Visible, because the `kw()` call sits inside a named rule:

```js
fields_keyword: $ => kw('fields'),          // `fields` appears in the tree
table_keyword: $ => kw('table'),            // `table` appears in the tree
if_keyword: $ => prec(10, choice('if', 'IF', 'If')),
```

Invisible, because `kw()` is called inline:

```js
field_declaration: $ => seq(
  kw('field'),                              // `field` is in no node
  '(',                                      // `(` is, it is a string literal
  field('id', $.integer),
  ...

record_type: $ => prec.right(seq(
  prec(1, kw('record')),                    // `Record` is in no node
  field('reference', $._namespaced_or_simple_ref),
  optional($.temporary_keyword)
)),
```

And for the assignment operators:

```js
_assignment_operator: $ => token(choice(':=', '+=', '-=', '*=', '/=')),
```

`token(choice(...))` collapses the alternatives into one unnamed terminal, and
the rule is hidden anyway by its leading underscore. `:=` — the most common
operator in the language, 22964 occurrences in 500 files — is therefore
unhighlightable, as are `+=`, `-=`, `*=`, `/=`.

### Why it matters

Every one of these is something an editor wants to colour. In the
nvim-treesitter queries the following patterns are dead as written, and there is
no way to express them at all:

```query
":=" @operator                              ; matches nothing
(field_declaration) ...                     ; the `field` keyword cannot be reached
(record_type) ...                           ; the `Record` keyword cannot be reached
```

The result is AL files where `Rec := Customer;` shows an uncoloured `:=`, and
`field(1; "No."; Code[20])` shows neither `field` nor `Code` as keywords, while
the `fields` header right above them is coloured. The inconsistency is visible
at a glance.

It also affects anything else that consumes the tree: textobjects that should
select from a keyword, `tags.scm`, structural search, and any tooling that
assumes leaf ranges reconstruct the source.

### Suggested fix

Give each of these its own named rule, exactly as the existing `*_keyword` rules
do, and reference `$.x_keyword` from the rule that currently calls `kw()`
inline. From the measured list, at minimum:

`field`, `record`, `code`, `text`, `option`, `list`, `dictionary`, `array`, `of`,
`testpage`, `tabledata`, `action`, `actionref`, `value`, `label`, `where`,
`const`, `sorting`, `order`, `ascending`, `lookup`, `modify`, `addafter`,
`addbefore`, `textelement`, `tableelement`, `content`, `processing`,
`factboxes`, `promoted`.

For the operators, replace the hidden `_assignment_operator` with a named node:

```js
assignment_operator: $ => token(choice(':=', '+=', '-=', '*=', '/=')),
```

so queries can write `(assignment_operator) @operator`, mirroring the existing
`comparison_operator`.

This is a node-adding change, so _minor_ under the project's semver policy —
existing queries keep working, new nodes become available.

### Regression test

A corpus test will not catch this: the files parse fine. The check that catches
it is the coverage walk above — assert that concatenating leaf ranges plus
whitespace reproduces the input. Worth adding to CI as its own step over a
sample of `BC.History`.

---

## 2. `begin` / `end` are dropped inside `#if` … `#endif`

This one is a genuine inconsistency rather than a grammar-design consequence:
the same keywords *are* visible outside a preprocessor conditional.

```al
codeunit 50100 C
{
    procedure WithRet(): Integer
    begin
        exit(1);
    end;

    #if X
    procedure InIf()
    begin
        exit;
    end;
    #endif
}
```

```console
$ tree-sitter parse -c t3.al | grep -n "code_block\|begin_keyword\|end_keyword\|procedure\b\|preproc_conditional"
9:2:4   - 5:8           procedure
17:3:4   - 5:8             body: code_block
18:3:4   - 3:9               begin_keyword `begin`
27:5:4   - 5:7               end_keyword `end`
29:7:4   - 12:10         preproc_conditional
33:8:4   - 11:8            procedure
38:9:4   - 11:8              body: code_block
```

The second `code_block` has no `begin_keyword` and no `end_keyword`. The full
subtree for it:

```
9:4   - 11:8   body: code_block
10:8  - 10:13    body: statement_block
10:8  - 10:12      exit_statement
10:8  - 10:12        exit_keyword
10:8  - 10:12          "exit"
10:12 - 10:13        ";"
11:7  - 11:8     ";"
```

Only the trailing `;` of `end;` survives. The coverage walk on the same file
reports exactly `begin` and `end` as dropped.

### Cause

`src/scanner.c:245` and `:254` gate both keywords on preprocessor depth:

```c
  // BEGIN_KEYWORD: 'begin' at depth 0 only — decline at depth > 0
  if (valid_symbols[BEGIN_KEYWORD] && state->depth == 0) { ... }

  // END_KEYWORD: 'end' at depth 0 only — decline at depth > 0
  if (valid_symbols[END_KEYWORD] && state->depth == 0) { ... }
```

Inside a conditional the scanner falls through to `PREPROC_SPLIT_BEGIN` /
`PREPROC_SPLIT_END` (`:272`, `:290`), which exist for the case where a `begin`
and its matching `end` sit on opposite sides of a `#else` / `#endif`. That
handoff is right for genuinely split constructs. It is wrong for a *complete*
`begin … end` that merely happens to sit inside `#if`: nothing then claims the
keyword text, and it is skipped.

The gate is too coarse. What matters is whether the block is split across a
directive boundary, not whether it is inside a conditional at all.

### Suggested fix

At depth > 0, attempt the split tokens first — they already look ahead for
`#endif` / `#else` — and fall back to emitting the ordinary `BEGIN_KEYWORD` /
`END_KEYWORD` when that lookahead shows the block is not split.

### Impact

Feature-flagged procedures are the standard Business Central pattern for
`CLEAN*` / obsoletion gating, so this is not a rare shape: 516 `begin` and 517
`end` in a 500-file sample.

---

## Note on `property_name`

An earlier version of this file reported `property_name` as a zero-width token
that dropped the property name text. That was measured against the **working
tree** build of `al.dll` (uncommitted `src/scanner.c`), not against v3.3.0.
Against v3.3.0 as compiled by nvim-treesitter, property names are correct:

```console
$ cat t1.al
table 50100 "T"
{
    Caption = 'X';
}
$ # coverage walk
no dropped text
```

Worth keeping in mind while the scanner is being changed: the failing shape was
a single-property object body, and the mechanism was a
`skip_whitespace_and_comments` call — which advances with `skip = true`, and so
moves `token_start_position` — running *after* the identifier had already been
consumed. Any external token that skips whitespace after consuming content has
that failure mode.
