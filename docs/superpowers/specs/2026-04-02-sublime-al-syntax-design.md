# Sublime Text AL Syntax Package Design Spec

## Goal

Create a `sublime-al` package providing high-quality syntax highlighting for AL (Application Language) in Sublime Text, targeting AL developers who use Sublime as their primary editor. The package lives in a separate repo from tree-sitter-al but uses its grammar and highlights.scm as the authoritative reference.

## Architecture

A standalone Sublime Text package using `.sublime-syntax` (YAML format) with moderate context stacking. Contexts handle object declarations, procedure/trigger signatures, attributes, var sections, and string/comment literals. Statement-level code uses flat keyword regex matching — no attempt to parse expressions or full procedure bodies.

Keywords, types, and completions are derived from the tree-sitter-al grammar's keyword lists.

## Package Structure

```
sublime-al/
├── AL.sublime-syntax          # Main syntax definition
├── AL.sublime-settings        # Comment toggling, indent rules, word separators
├── AL.sublime-completions     # Keyword/type completions
├── AL.tmPreferences           # Symbol indexing (Goto Symbol support)
├── scripts/
│   └── generate-completions.js  # Extracts keywords from tree-sitter-al grammar.js
├── tests/                      # Sublime syntax test files
│   └── syntax_test_al.al
├── LICENSE
└── README.md
```

## File Extensions

- `.al` — standard AL files
- `.dal` — AL delta files (used in some tooling)

Scope name: `source.al`

## Context Stack Design

### Contexts

| Context | Enters on | Exits on | Purpose |
|---------|-----------|----------|---------|
| `main` | file start | — | Top-level: namespace/using, object declarations, preprocessor, comments |
| `object-header` | object type keyword (`codeunit`, `table`, etc.) | `{` | Scopes object ID, object name, `extends`/`implements` target |
| `object-body` | `{` after object header | `}` | Properties, sections, procedures, triggers, var sections, nested `{}`  |
| `procedure-declaration` | `procedure`/`trigger` keyword | `)` closing params | Procedure/trigger name, parameters with types |
| `parameter-list` | `(` after procedure name | `)` | Parameter names, types after `:`, `var` modifier |
| `var-section` | `var` keyword | lookahead for `begin`/`procedure`/`trigger`/`}` | Variable names and type annotations after `:` |
| `type-annotation` | `:` in var/parameter context | `;` or `)` or `,` | Type names, generic brackets `[N]` |
| `attribute` | `[` at line start or after whitespace | `]` | Attribute name, arguments |
| `string-single` | `'` | unescaped `'` | String content, `''` escape |
| `string-verbatim` | `@'` | unescaped `'` | Multiline string content, `''` escape |
| `quoted-identifier` | `"` | `"` | Quoted identifier content (distinct from strings) |
| `comment-line` | `//` | EOL | Comment text |
| `comment-block` | `/*` | `*/` | Comment text |
| `preprocessor-line` | `#` at line start | EOL | Directive keyword, condition identifiers |

### Context transitions

```
main
├── object-header → object-body
│   ├── procedure-declaration → parameter-list → (back to object-body)
│   ├── var-section → type-annotation → (back to var-section)
│   ├── attribute
│   ├── object-body (nested { } for field bodies, action bodies, etc.)
│   └── (flat keyword matching for statements inside begin/end)
├── comment-line, comment-block
├── preprocessor-line
├── string-single, string-verbatim
└── quoted-identifier
```

## Keyword Scoping

All keyword matching uses `(?i:)` for case-insensitivity. Keywords are matched with `\b` word boundaries.

### Control flow → `keyword.control.al`
```
if, then, else, case, of, while, do, for, foreach, in, repeat, until,
exit, break, continue, with, asserterror, to, downto, begin, end
```

### Declarations → `keyword.declaration.al`
```
procedure, trigger, var, event
```

### Object types → `storage.type.al`
```
codeunit, table, tableextension, page, pageextension, report, reportextension,
query, xmlport, enum, enumextension, interface, controladdin, dotnet,
profile, profileextension, permissionset, permissionsetextension,
entitlement, pagecustomization
```

### Structure/sections → `keyword.other.al`
```
fields, keys, key, fieldgroups, fieldgroup, actions, layout, area, group,
repeater, cuegroup, fixed, grid, part, systempart, usercontrol, dataset,
elements, dataitem, column, filter, labels, rendering, requestpage, schema,
views, view, field, value, separator, label, modify, add, addfirst,
addlast, addafter, addbefore, movefirst, movelast, moveafter, movebefore
```

### Structure keywords → `keyword.import.al`
```
namespace, using, extends, implements, customizes
```

### Modifiers → `storage.modifier.al`
```
local, internal, protected, temporary
```

### Operators → `keyword.operator.al`
```
and, or, not, xor, div, mod, in, is, as
```

### Built-in types → `support.type.al`
```
Integer, BigInteger, Decimal, Text, Code, Boolean, Char, Byte, Date,
Time, DateTime, DateFormula, Duration, Guid, Blob, Record, RecordId,
RecordRef, FieldRef, KeyRef, Option, Dialog, File, InStream, OutStream,
TextBuilder, JsonObject, JsonArray, JsonToken, JsonValue, HttpClient,
HttpContent, HttpHeaders, HttpRequestMessage, HttpResponseMessage,
XmlDocument, XmlElement, XmlNode, XmlNodeList, XmlAttribute, XmlComment,
XmlText, XmlCData, XmlDeclaration, XmlNamespaceManager, XmlWriteOptions,
XmlReadOptions, List, Dictionary, Notification, ErrorInfo, Media,
MediaSet, Variant, Action, FilterPageBuilder, SessionSettings,
WebServiceActionContext, Label, TextConst, SecretText, Version,
ModuleInfo, DotNet
```

### Property keywords (CalcFormula, where, etc.) → `keyword.other.property.al`
```
average, const, count, exist, field, filter, lookup, max, min, order,
sorting, sum, tabledata, upperlimit, where, ascending, descending
```

### Constants → `constant.language.al`
```
true, false
```

## Operator Scoping

| Pattern | Scope |
|---------|-------|
| `:=`, `+=`, `-=`, `/=`, `*=` | `keyword.operator.assignment.al` |
| `=`, `<>`, `<`, `>`, `<=`, `>=` | `keyword.operator.comparison.al` |
| `+`, `-`, `*`, `/` | `keyword.operator.arithmetic.al` |
| `..` | `keyword.operator.range.al` |
| `::` | `punctuation.accessor.al` |

## Numeric Literals → `constant.numeric.al`

AL-specific patterns (not C/C++ patterns):
- Integers: `\b\d+\b`
- Decimals: `\b\d+\.\d+\b`
- BigInteger: `\b\d+L\b` (case-insensitive)
- Date: `\b\d+D\b` (case-insensitive)
- Time: `\b\d{6}T\b` and `\b0T\b` (case-insensitive)
- DateTime: `\b\d+DT\b` and `\b0DT\b` (case-insensitive)

## Contextual Highlighting

### Object declarations
```al
codeunit 50000 "My Codeunit" implements IFace
^^^^^^^^ storage.type
         ^^^^^ constant.numeric
                ^^^^^^^^^^^^^^ entity.name.type
                               ^^^^^^^^^^ keyword.import
                                          ^^^^^ entity.other.inherited-class
```

### Procedure declarations
```al
local procedure MyMethod(var Param: Record "Customer"): Boolean
^^^^^ storage.modifier
      ^^^^^^^^^ keyword.declaration
                ^^^^^^^^ entity.name.function
                         ^^^ storage.modifier
                             ^^^^^ variable.parameter
                                    ^^^^^^ support.type
                                           ^^^^^^^^^^ variable.other.quoted
                                                       ^^^^^^^ support.type
```

### Attributes
```al
[Scope('OnPrem')]
 ^^^^^ variable.annotation
       ^^^^^^^^ string.quoted.single
```

### Preprocessor
```al
#if not CLEAN25
^^^ keyword.control.import
    ^^^ keyword.operator
        ^^^^^^^ variable.other
```

## Settings File (`AL.sublime-settings`)

```json
{
    "extensions": ["al", "dal"],
    "tab_size": 4,
    "translate_tabs_to_spaces": true
}
```

## Comment Preferences (`AL.tmPreferences`)

- Line comment: `//`
- Block comment: `/* */`
- Symbol indexing: procedures and triggers appear in Goto Symbol (`Ctrl+R`)
  - Pattern: `^\s*(?:local|internal|protected)?\s*(?:procedure|trigger)\s+(\w+|"[^"]+")`

## Completions (`AL.sublime-completions`)

Generated from tree-sitter-al `grammar.js` keyword lists. Includes:
- All keywords (control, declaration, object type, section, modifier)
- All built-in types
- Common property names
- Trigger: `source.al` scope

Not context-aware — offers all completions everywhere. This is acceptable for a syntax-only package; context-aware completions come from the LSP.

## Generation Script (`scripts/generate-completions.js`)

Reads `grammar.js` from tree-sitter-al repo (path provided as argument), extracts all `kw('...')` calls and named keyword rules, outputs `AL.sublime-completions` JSON.

## Testing

Sublime syntax tests use specially formatted AL files:
```al
// SYNTAX TEST "Packages/AL/AL.sublime-syntax"
codeunit 50000 "Test"
// ^^^^^^^^ storage.type.al
//         ^^^^^ constant.numeric.al
```

One test file covering all major constructs: object declarations, procedures, var sections, attributes, strings, comments, preprocessor, operators, numeric literals.

## Out of Scope

- LSP integration (separate `LSP-AL` package)
- Build systems / compiler integration
- Snippet templates
- Color scheme customization (uses Sublime's standard scopes)
- Statement-level expression parsing (diminishing returns for syntax highlighting)
