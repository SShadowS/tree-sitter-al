# Fix: `database_reference` rejects numeric object IDs

## Bug

`Codeunit::80`, `Page::42`, `Report::1` (and Database/XMLport/Query variants)
fail to parse as `database_reference`. They produce an unrecognized split:

```al
Codeunit.Run(Codeunit::80);
```

Current parse:

```
argument_list
  keyword_identifier
    codeunit_keyword: "Codeunit"
  ERROR: "::80"
    integer: "80"
```

Expected parse:

```
argument_list
  database_reference
    object_type_keyword: "Codeunit"
    integer: "80"            ← under `table_name` field
```

The quoted/unquoted-name forms parse cleanly today; only the numeric form
errors out:

```al
Codeunit.Run(Codeunit::"Sales-Post"); // ✅ database_reference
Codeunit.Run(Codeunit::SalesPost);    // ✅ database_reference
Codeunit.Run(Codeunit::80);           // ❌ ERROR node
```

## Root Cause

`grammar.js:3540-3554`:

```js
database_reference: $ => prec(300, seq(
  field('keyword', alias(
    choice(
      kw('database'),
      $.page_keyword,
      $.report_keyword,
      $.codeunit_keyword,
      $.xmlport_keyword,
      $.query_keyword,
    ),
    $.object_type_keyword
  )),
  '::',
  field('table_name', $._identifier_or_quoted)   // ← rejects integers
)),
```

`_identifier_or_quoted` (grammar.js:3688-) is `identifier | quoted_identifier
| <a few contextual keywords>` — no `integer` alternative. Real AL accepts an
integer object id wherever a quoted/unquoted name is accepted in the
object-reference position.

## AL Reference

The Microsoft Business Central language allows both forms interchangeably:

```al
codeunit 50100 Demo
{
    trigger OnRun()
    begin
        Codeunit.Run(Codeunit::"Sales-Post");
        Codeunit.Run(Codeunit::80);              // identical effect
        Page.Run(Page::"Customer Card");
        Page.Run(Page::21);
        Report.Run(Report::"Aged Account Receivable");
        Report.Run(Report::105);
    end;
}
```

All six lines are valid AL and accepted by the BC compiler. The grammar
should match.

## Fix

Widen `database_reference.table_name` to also accept `integer`:

```js
database_reference: $ => prec(300, seq(
  field('keyword', alias(
    choice(
      kw('database'),
      $.page_keyword,
      $.report_keyword,
      $.codeunit_keyword,
      $.xmlport_keyword,
      $.query_keyword,
    ),
    $.object_type_keyword
  )),
  '::',
  field('table_name', choice($._identifier_or_quoted, $.integer))
)),
```

The `table_name` field continues to expose a single node — downstream
consumers read `node.childForFieldName("table_name")` and branch on
`.type === "integer"` vs `"identifier"` / `"quoted_identifier"` to
distinguish numeric ID from name.

## Why this position is unambiguous

`database_reference` has `prec(300)`. Its required prefix is one of
`Codeunit|Page|Report|Database|XMLport|Query` immediately followed by `::`.
After `::`, the parser has just seen a high-precedence
`<object_type_keyword> ::` prefix; an `integer` in that slot is the only
syntactic shape that produces a valid AL object reference. There is no
existing rule that legitimately wants `<object_type_keyword> :: <integer>`
to parse as anything else.

No conflict declarations should be required.

## Tests

Add a corpus file (suggested path:
`test/corpus/database_reference_numeric_id.txt`) covering:

```
==================
database_reference: numeric Codeunit id
==================

codeunit 50000 X
{
    trigger OnRun()
    begin
        Codeunit.Run(Codeunit::80);
    end;
}

---

(source_file
  (codeunit_declaration
    (object_id (integer))
    (object_name (identifier))
    (codeunit_body
      (trigger_declaration
        (trigger_name (identifier))
        (code_block
          (call_expression
            (member_expression
              (keyword_identifier (codeunit_keyword))
              (identifier))
            (argument_list
              (database_reference
                (object_type_keyword)
                (integer)))))))))

==================
database_reference: numeric Page id
==================

codeunit 50001 Y
{
    trigger OnRun()
    begin
        Page.Run(Page::21);
    end;
}

---

(source_file
  (codeunit_declaration
    (object_id (integer))
    (object_name (identifier))
    (codeunit_body
      (trigger_declaration
        (trigger_name (identifier))
        (code_block
          (call_expression
            (member_expression
              (keyword_identifier (page_keyword))
              (identifier))
            (argument_list
              (database_reference
                (object_type_keyword)
                (integer)))))))))

==================
database_reference: numeric Report id with Report.Run
==================

codeunit 50002 Z
{
    trigger OnRun()
    begin
        Report.Run(Report::105);
    end;
}

---

(source_file
  (codeunit_declaration
    (object_id (integer))
    (object_name (identifier))
    (codeunit_body
      (trigger_declaration
        (trigger_name (identifier))
        (code_block
          (call_expression
            (member_expression
              (keyword_identifier (report_keyword))
              (identifier))
            (argument_list
              (database_reference
                (object_type_keyword)
                (integer)))))))))
```

Existing quoted/unquoted-name corpus tests for `database_reference` must
continue to pass unchanged — the `choice($._identifier_or_quoted, $.integer)`
adds the integer alternative without altering the existing alternatives.

## Downstream consumer (al-sem)

al-sem's call resolver (`U:/Git/al-sem/src/resolve/callee.ts`) currently
regex-shreds the argument text to distinguish `Codeunit::"Name"` from
`Codeunit::80`. After this fix, al-sem reads `table_name.type` and
`table_name.text` directly — the last regex in `callee.ts` can be deleted.
This is part of an ongoing al-sem effort to replace regex-based AL parsing
with grammar nodes (PR-2 of the regex-removal series).

## Risk

Low. The change extends a closed alternative; no existing parse path is
altered. The numeric form currently produces an `ERROR` node, so any
consumer that was relying on the broken parse to detect malformed input
would lose that signal — but the broken parse is itself a parse error, not
a useful signal.

## Acceptance

- All existing `database_reference` corpus tests still pass.
- New numeric-id corpus tests pass.
- `Codeunit::80` (and Page/Report variants) parses as `database_reference`
  with `table_name = (integer)`.
- No new conflicts reported by `tree-sitter generate`.
