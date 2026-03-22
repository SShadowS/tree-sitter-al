# V2 Grammar Phase 1: Scaffold + Object Shells

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the v2 grammar project scaffold with scanner, helpers, and all 19 AL object type declarations parsing empty bodies. Validate against BC.History to establish a baseline.

**Architecture:** New tree-sitter project in `v2/` subdirectory. Scanner provides `PROPERTY_NAME` token (needed from Phase 2). Grammar uses `kw()` regex helper for case-insensitive keywords. All object types parse `ObjectType ID "Name" { }` with optional `extends`/`implements` clauses.

**Tech Stack:** tree-sitter grammar.js DSL, C external scanner

**Spec:** `docs/superpowers/specs/2026-03-20-v2-grammar-design.md`

**V1 Reference:** `grammar.js` (root) — consult for AL syntax patterns but don't copy structure

---

## File Structure

```
v2/
├── grammar.js          # V2 grammar definition
├── src/
│   └── scanner.c       # External scanner (PROPERTY_NAME + v1 tokens)
├── test/
│   └── corpus/
│       └── objects.txt  # Object declaration tests
├── queries/
│   └── highlights.scm  # Minimal highlights (just to verify queries work)
└── validate.sh         # Compare v2 vs v1 on BC.History
```

---

### Task 1: Create v2 Project Scaffold

**Files:**
- Create: `v2/grammar.js`
- Create: `v2/src/scanner.c`
- Create: `v2/validate.sh`

- [ ] **Step 1: Create v2 directory and minimal grammar.js**

```bash
mkdir -p v2/src v2/test/corpus v2/queries
```

Create `v2/grammar.js` with the helper functions and minimal structure:

```javascript
/**
 * @file AL for Business Central (V2)
 * @author Torben Leth <sshadows@sshadows.dk>
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

// Case-insensitive keyword via regex
function kw(word, precedence = null) {
  const regex = new RustRegex(`(?i)${word}`);
  return precedence !== null ? token(prec(precedence, regex)) : token(regex);
}

module.exports = grammar({
  name: "al",

  word: $ => $.identifier,

  extras: $ => [
    /\s/,
    $.comment,
    $.multiline_comment,
    /\uFEFF/,  // BOM
  ],

  externals: $ => [
    $.property_name,  // identifier followed by = (not :=)
  ],

  rules: {
    source_file: $ => repeat($._object),

    _object: $ => choice(
      // Will be filled in Task 3
    ),

    // Identifiers
    identifier: $ => token(/[\p{L}_][\p{L}\p{N}_]*/u),
    quoted_identifier: $ => token(seq('"', repeat(choice(/[^"]/, '""')), '"')),

    // Comments
    comment: $ => token(seq('//', /[^\n]*/)),
    multiline_comment: $ => token(seq('/*', /[^*]*\*+([^/*][^*]*\*+)*/, '/')),

    // Literals
    string_literal: $ => token(seq("'", repeat(choice(/[^']/, "''")), "'")),
    integer: $ => token(/\d+/),
  },
});
```

- [ ] **Step 2: Create minimal scanner.c**

Create `v2/src/scanner.c`:

```c
#include "tree_sitter/parser.h"
#include <string.h>
#include <wctype.h>

enum TokenType {
  PROPERTY_NAME,
};

void *tree_sitter_al_external_scanner_create() { return NULL; }
void tree_sitter_al_external_scanner_destroy(void *payload) {}
unsigned tree_sitter_al_external_scanner_serialize(void *payload, char *buffer) { return 0; }
void tree_sitter_al_external_scanner_deserialize(void *payload, const char *buffer, unsigned length) {}

static bool is_identifier_start(int32_t c) {
  return iswalpha(c) || c == '_';
}

static bool is_identifier_char(int32_t c) {
  return iswalnum(c) || c == '_';
}

bool tree_sitter_al_external_scanner_scan(
  void *payload,
  TSLexer *lexer,
  const bool *valid_symbols
) {
  // PROPERTY_NAME: match identifier followed by = (not :=)
  if (valid_symbols[PROPERTY_NAME]) {
    // Must start with identifier character
    if (!is_identifier_start(lexer->lookahead)) return false;

    // Consume identifier
    while (is_identifier_char(lexer->lookahead)) {
      lexer->advance(lexer, false);
    }

    // Skip whitespace
    while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
           lexer->lookahead == '\r' || lexer->lookahead == '\f') {
      lexer->advance(lexer, false);
    }

    // Check for = but not :=
    if (lexer->lookahead == '=') {
      // Don't consume the =, just mark the result
      lexer->result_symbol = PROPERTY_NAME;
      lexer->mark_end(lexer);
      return true;
    }

    return false;
  }

  return false;
}
```

- [ ] **Step 3: Create validate.sh**

Create `v2/validate.sh`:

```bash
#!/bin/bash
# Validate v2 grammar against BC.History, compare with v1
set -e

echo "=== V2 Grammar Validation ==="
cd "$(dirname "$0")"

echo "Generating parser..."
tree-sitter generate

echo "Running tests..."
tree-sitter test

echo "Parsing BC.History..."
../parse-al-parallel.sh ../BC.History/ .

echo ""
echo "=== V1 Baseline ==="
echo "V1 errors: 14 (99.91% success)"
```

```bash
chmod +x v2/validate.sh
```

- [ ] **Step 4: Verify generation succeeds**

```bash
cd v2 && tree-sitter generate
```

Expected: Success. If tree-sitter can't find the project, create a minimal `package.json`:

```json
{
  "name": "tree-sitter-al-v2",
  "version": "0.0.1",
  "main": "bindings/node",
  "tree-sitter": [{"scope": "source.al", "file-types": ["al"]}]
}
```

---

### Task 2: Add Namespace and Using Declarations

**Files:**
- Modify: `v2/grammar.js`
- Create: `v2/test/corpus/namespace_test.txt`

- [ ] **Step 1: Create test**

Create `v2/test/corpus/namespace_test.txt`:

```
========================================================================
Namespace declaration
========================================================================
namespace Microsoft.Sales;
------------------------------------------------------------------------
(source_file
  (namespace_declaration
    name: (namespace_name
      (identifier)
      (identifier))))

========================================================================
Using statement
========================================================================
using Microsoft.Foundation.Period;
------------------------------------------------------------------------
(source_file
  (using_statement
    namespace: (namespace_name
      (identifier)
      (identifier)
      (identifier))))

========================================================================
Namespace with using
========================================================================
namespace MyApp.Core;

using Microsoft.Sales;
using System.IO;
------------------------------------------------------------------------
(source_file
  (namespace_declaration
    name: (namespace_name
      (identifier)
      (identifier)))
  (using_statement
    namespace: (namespace_name
      (identifier)
      (identifier)))
  (using_statement
    namespace: (namespace_name
      (identifier)
      (identifier))))
```

- [ ] **Step 2: Add namespace/using rules to grammar.js**

Add to the rules:

```javascript
source_file: $ => seq(
  optional($.namespace_declaration),
  repeat($.using_statement),
  repeat($._object),
),

namespace_declaration: $ => seq(
  kw('namespace'),
  field('name', $.namespace_name),
  ';'
),

using_statement: $ => seq(
  kw('using'),
  field('namespace', $.namespace_name),
  ';'
),

namespace_name: $ => seq(
  $.identifier,
  repeat(seq('.', $.identifier))
),
```

- [ ] **Step 3: Run tests**

```bash
cd v2 && tree-sitter generate && tree-sitter test
```

Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
cd v2 && git add -A . && git commit -m "v2: scaffold with namespace/using declarations"
```

---

### Task 3: Add All Object Type Declarations

**Files:**
- Modify: `v2/grammar.js`
- Create: `v2/test/corpus/object_declarations.txt`

- [ ] **Step 1: Create test for all 19 object types**

Create `v2/test/corpus/object_declarations.txt` with tests for:
- `table`, `tableextension`, `page`, `pageextension`, `pagecustomization`
- `codeunit`, `report`, `reportextension`
- `query`, `xmlport`
- `enum`, `enumextension`
- `interface`, `controladdin`, `dotnet`
- `profile`, `profileextension`
- `permissionset`, `permissionsetextension`
- `entitlement`

Each test follows this pattern (adjust for each type):

```
========================================================================
Table declaration
========================================================================
table 50100 "My Table"
{
}
------------------------------------------------------------------------
(source_file
  (table_declaration
    object_id: (integer)
    object_name: (quoted_identifier)))

========================================================================
Table extension declaration
========================================================================
tableextension 50100 "My Ext" extends "Base Table"
{
}
------------------------------------------------------------------------
(source_file
  (tableextension_declaration
    object_id: (integer)
    object_name: (quoted_identifier)
    base_object: (quoted_identifier)))
```

Include tests for:
- Unquoted names: `codeunit 50100 MyCodeunit { }`
- `extends` clause: extensions, enums
- `implements` clause: codeunits, enums
- `customizes` clause: pagecustomization
- No object_id: interface, profile, entitlement, pagecustomization

- [ ] **Step 2: Add object declaration rules**

Add a helper for the common pattern:

```javascript
// Object declaration template
function _object_declaration(keyword, hasId = true) {
  if (hasId) {
    return $ => seq(
      kw(keyword),
      field('object_id', $.integer),
      field('object_name', $._identifier_or_quoted),
      '{',
      repeat($._body_element),
      '}'
    );
  } else {
    return $ => seq(
      kw(keyword),
      field('object_name', $._identifier_or_quoted),
      '{',
      repeat($._body_element),
      '}'
    );
  }
}
```

Then define all object types:

```javascript
_object: $ => choice(
  $.table_declaration,
  $.tableextension_declaration,
  $.page_declaration,
  $.pageextension_declaration,
  $.pagecustomization_declaration,
  $.codeunit_declaration,
  $.report_declaration,
  $.reportextension_declaration,
  $.query_declaration,
  $.xmlport_declaration,
  $.enum_declaration,
  $.enumextension_declaration,
  $.interface_declaration,
  $.controladdin_declaration,
  $.dotnet_declaration,
  $.profile_declaration,
  $.profileextension_declaration,
  $.permissionset_declaration,
  $.permissionsetextension_declaration,
  $.entitlement_declaration,
),

_identifier_or_quoted: $ => choice($.identifier, $.quoted_identifier),

_body_element: $ => choice(
  // Will be filled in later phases
  $.empty_statement,
),

empty_statement: $ => ';',

// Object declarations
table_declaration: _object_declaration('table'),
page_declaration: _object_declaration('page'),
codeunit_declaration: $ => seq(
  kw('codeunit'),
  field('object_id', $.integer),
  field('object_name', $._identifier_or_quoted),
  optional($.implements_clause),
  '{', repeat($._body_element), '}'
),
report_declaration: _object_declaration('report'),
query_declaration: _object_declaration('query'),
xmlport_declaration: _object_declaration('xmlport'),
enum_declaration: $ => seq(
  kw('enum'),
  field('object_id', $.integer),
  field('object_name', $._identifier_or_quoted),
  optional($.implements_clause),
  '{', repeat($._body_element), '}'
),
interface_declaration: $ => seq(
  kw('interface'),
  field('object_name', $._identifier_or_quoted),
  optional(seq(kw('extends'), field('extends_interface', $._identifier_or_quoted))),
  '{', repeat($._body_element), '}'
),
controladdin_declaration: _object_declaration('controladdin', false),
dotnet_declaration: $ => seq(
  kw('dotnet'),
  '{', repeat($._body_element), '}'
),
profile_declaration: _object_declaration('profile', false),
entitlement_declaration: _object_declaration('entitlement', false),
permissionset_declaration: _object_declaration('permissionset'),
pagecustomization_declaration: $ => seq(
  kw('pagecustomization'),
  field('object_name', $._identifier_or_quoted),
  kw('customizes'),
  field('target_page', $._identifier_or_quoted),
  '{', repeat($._body_element), '}'
),

// Extension declarations
tableextension_declaration: $ => seq(
  kw('tableextension'),
  field('object_id', $.integer),
  field('object_name', $._identifier_or_quoted),
  kw('extends'),
  field('base_object', $._identifier_or_quoted),
  '{', repeat($._body_element), '}'
),
pageextension_declaration: $ => seq(
  kw('pageextension'),
  field('object_id', $.integer),
  field('object_name', $._identifier_or_quoted),
  kw('extends'),
  field('base_object', $._identifier_or_quoted),
  '{', repeat($._body_element), '}'
),
reportextension_declaration: $ => seq(
  kw('reportextension'),
  field('object_id', $.integer),
  field('object_name', $._identifier_or_quoted),
  kw('extends'),
  field('base_object', $._identifier_or_quoted),
  '{', repeat($._body_element), '}'
),
enumextension_declaration: $ => seq(
  kw('enumextension'),
  field('object_id', $.integer),
  field('object_name', $._identifier_or_quoted),
  kw('extends'),
  field('base_object', $._identifier_or_quoted),
  '{', repeat($._body_element), '}'
),
profileextension_declaration: $ => seq(
  kw('profileextension'),
  field('object_name', $._identifier_or_quoted),
  kw('extends'),
  field('base_object', $._identifier_or_quoted),
  '{', repeat($._body_element), '}'
),
permissionsetextension_declaration: $ => seq(
  kw('permissionsetextension'),
  field('object_id', $.integer),
  field('object_name', $._identifier_or_quoted),
  kw('extends'),
  field('base_object', $._identifier_or_quoted),
  '{', repeat($._body_element), '}'
),

// Implements clause (for codeunits and enums)
implements_clause: $ => seq(
  kw('implements'),
  field('interface', $._identifier_or_quoted),
  repeat(seq(',', field('interface', $._identifier_or_quoted)))
),
```

- [ ] **Step 3: Run tests**

```bash
cd v2 && tree-sitter generate && tree-sitter test
```

Expected: All tests pass.

- [ ] **Step 4: Run BC.History baseline**

```bash
cd v2 && ../parse-al-parallel.sh ../BC.History/ .
```

Record the initial error count. Most files will fail (we only parse object shells), but some minimal files might pass. This establishes the v2 baseline to improve from.

- [ ] **Step 5: Commit**

```bash
cd v2 && git add -A . && git commit -m "v2: all 19 object type declarations

V2 baseline: XXXX errors on BC.History (XX.XX% success)"
```

---

### Task 4: Verify Parser Size and Structure

**Files:**
- Read: `v2/src/parser.c`

- [ ] **Step 1: Check parser metrics**

```bash
cd v2
echo "parser.c size: $(wc -c < src/parser.c) bytes"
grep 'STATE_COUNT\|SYMBOL_COUNT' src/parser.c | head -2
```

Expected: parser.c well under 10 MB, SYMBOL_COUNT under 100. This confirms the v2 architecture is on the right track.

- [ ] **Step 2: Verify scanner token works**

Create a quick test to verify the PROPERTY_NAME scanner token is operational (even though we don't use it yet):

```bash
echo 'table 50100 Test { }' > /tmp/v2test.al
cd v2 && tree-sitter parse /tmp/v2test.al
```

Expected: Parses successfully as `(source_file (table_declaration ...))`.

- [ ] **Step 3: Create minimal highlights.scm**

Create `v2/queries/highlights.scm`:

```scheme
; Minimal V2 highlights — will be expanded in Phase 8
(comment) @comment.line
(multiline_comment) @comment.block
(string_literal) @string
(integer) @number
(identifier) @variable
(quoted_identifier) @string.special
";" @punctuation.delimiter
"{" @punctuation.bracket
"}" @punctuation.bracket
```

Verify: `cd v2 && tree-sitter query queries/highlights.scm /tmp/v2test.al`

- [ ] **Step 4: Commit**

```bash
cd v2 && git add -A . && git commit -m "v2: verify parser size and structure

SYMBOL_COUNT: XX, STATE_COUNT: XX, parser.c: XX KB"
```

---

## Phase 1 Completion Criteria

- [ ] All 19 object types parse empty bodies: `ObjectType [ID] "Name" [extends/implements ...] { }`
- [ ] Namespace and using declarations parse
- [ ] Scanner compiles and PROPERTY_NAME token is available
- [ ] parser.c is under 10 MB
- [ ] SYMBOL_COUNT is under 100
- [ ] BC.History baseline recorded
- [ ] All tests pass

## Next Phase

Phase 2 (Properties) will add:
- Generic `property` rule using `PROPERTY_NAME` scanner token
- Complex properties (CalcFormula, TableRelation, Permissions, ML, etc.)
- This is where the main architectural win happens
