# Sublime AL Syntax Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `sublime-al` Sublime Text package with high-quality AL syntax highlighting, comment/indent settings, symbol indexing, and keyword completions.

**Architecture:** A `.sublime-syntax` file (YAML, version 2) with moderate context stacking — contexts for object declarations, procedure signatures, var sections, attributes, strings, comments, and preprocessor directives. Statement-level code uses flat keyword regex. The package lives in a new repo at `U:/Git/sublime-al/`.

**Tech Stack:** Sublime Text `.sublime-syntax` YAML format, `.tmPreferences` XML for symbol indexing, JSON for settings/completions. Node.js script for generating completions from tree-sitter-al grammar.

**Spec:** `U:/Git/tree-sitter-al/docs/superpowers/specs/2026-04-02-sublime-al-syntax-design.md`

---

## File Map

- **Create:** `U:/Git/sublime-al/AL.sublime-syntax` — Main syntax definition (~500 lines)
- **Create:** `U:/Git/sublime-al/AL.sublime-settings` — Comment toggling, indent, tab settings
- **Create:** `U:/Git/sublime-al/AL.tmPreferences` — Symbol indexing for Goto Symbol
- **Create:** `U:/Git/sublime-al/AL.sublime-completions` — Keyword/type completions
- **Create:** `U:/Git/sublime-al/scripts/generate-completions.js` — Completions generator
- **Create:** `U:/Git/sublime-al/tests/syntax_test_al.al` — Sublime syntax test file
- **Create:** `U:/Git/sublime-al/LICENSE` — MIT license
- **Create:** `U:/Git/sublime-al/README.md` — Package documentation

---

### Task 1: Repo Setup and Settings Files

**Files:**
- Create: `U:/Git/sublime-al/AL.sublime-settings`
- Create: `U:/Git/sublime-al/AL.tmPreferences`
- Create: `U:/Git/sublime-al/LICENSE`
- Create: `U:/Git/sublime-al/.gitignore`

- [ ] **Step 1: Create the repo directory and initialize git**

```bash
mkdir -p "U:/Git/sublime-al"
cd "U:/Git/sublime-al"
git init
```

- [ ] **Step 2: Create .gitignore**

Create `U:/Git/sublime-al/.gitignore`:
```
*.cache
*.pyc
__pycache__/
.DS_Store
Thumbs.db
```

- [ ] **Step 3: Create AL.sublime-settings**

Create `U:/Git/sublime-al/AL.sublime-settings`:
```json
{
    "extensions": ["al", "dal"],
    "tab_size": 4,
    "translate_tabs_to_spaces": true
}
```

- [ ] **Step 4: Create AL.tmPreferences**

Create `U:/Git/sublime-al/AL.tmPreferences`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
    <key>scope</key>
    <string>source.al</string>
    <key>settings</key>
    <dict>
        <key>shellVariables</key>
        <array>
            <dict>
                <key>name</key>
                <string>TM_COMMENT_START</string>
                <key>value</key>
                <string>// </string>
            </dict>
            <dict>
                <key>name</key>
                <string>TM_COMMENT_START_2</string>
                <key>value</key>
                <string>/*</string>
            </dict>
            <dict>
                <key>name</key>
                <string>TM_COMMENT_END_2</string>
                <key>value</key>
                <string>*/</string>
            </dict>
        </array>
        <key>increaseIndentPattern</key>
        <string>(?i)^\s*(begin|repeat|if.*then\s*$|else\s*$|for.*do\s*$|while.*do\s*$|case.*of\s*$)\s*$|.*\{\s*$</string>
        <key>decreaseIndentPattern</key>
        <string>(?i)^\s*(end;?|until\b|\})\s*$</string>
        <key>symbolTransformation</key>
        <string>s/^\s*(?:local|internal|protected)?\s*(?:procedure|trigger)\s+//; s/\(.*//;</string>
        <key>symbolIndexPattern</key>
        <string>^\s*(?:local|internal|protected)?\s*(?:procedure|trigger)\s+(\w+|"[^"]+")</string>
    </dict>
</dict>
</plist>
```

- [ ] **Step 5: Create LICENSE**

Create `U:/Git/sublime-al/LICENSE` with MIT license text, copyright holder "Torben Leth", year 2026.

- [ ] **Step 6: Commit**

```bash
cd "U:/Git/sublime-al"
git add .
git commit -m "chore: initial repo with settings and preferences"
```

---

### Task 2: Syntax Foundation — Literals, Comments, Preprocessor

**Files:**
- Create: `U:/Git/sublime-al/AL.sublime-syntax`

Build the base syntax file with `main` context handling: comments, strings, quoted identifiers, preprocessor, numeric literals, and the `prototype` context.

- [ ] **Step 1: Create the syntax file skeleton**

Create `U:/Git/sublime-al/AL.sublime-syntax`:
```yaml
%YAML 1.2
---
name: AL
scope: source.al
version: 2
file_extensions:
  - al
  - dal

variables:
  # Case-insensitive identifier
  ident: '[A-Za-z_]\w*'

contexts:
  prototype:
    - include: comments
    - include: preprocessor

  main:
    - include: literals
    - include: keywords

  # ===========================================================================
  # Comments
  # ===========================================================================

  comments:
    - match: //
      scope: punctuation.definition.comment.al
      push: comment-line
    - match: /\*
      scope: punctuation.definition.comment.begin.al
      push: comment-block

  comment-line:
    - meta_scope: comment.line.double-slash.al
    - match: $\n?
      pop: true

  comment-block:
    - meta_scope: comment.block.al
    - match: \*/
      scope: punctuation.definition.comment.end.al
      pop: true

  # ===========================================================================
  # Preprocessor Directives
  # ===========================================================================

  preprocessor:
    - match: ^\s*(#)\s*(?i:(if|elif))\b
      captures:
        1: punctuation.definition.directive.al
        2: keyword.control.import.al
      push: preprocessor-condition
    - match: ^\s*(#)\s*(?i:(else|endif))\b
      captures:
        1: punctuation.definition.directive.al
        2: keyword.control.import.al
    - match: ^\s*(#)\s*(?i:(pragma|region|endregion))\b
      captures:
        1: punctuation.definition.directive.al
        2: keyword.control.import.al
      push: preprocessor-rest

  preprocessor-condition:
    - meta_content_scope: meta.preprocessor.al
    - match: \b(?i:not)\b
      scope: keyword.operator.al
    - match: \b(?i:and|or)\b
      scope: keyword.operator.al
    - match: '{{ident}}'
      scope: variable.other.al
    - match: $\n?
      pop: true

  preprocessor-rest:
    - meta_content_scope: meta.preprocessor.al
    - match: $\n?
      pop: true

  # ===========================================================================
  # String and Identifier Literals
  # ===========================================================================

  literals:
    - include: strings
    - include: quoted-identifiers
    - include: numeric-literals

  strings:
    - match: "@'"
      scope: punctuation.definition.string.begin.al
      push: string-verbatim
    - match: "'"
      scope: punctuation.definition.string.begin.al
      push: string-single

  string-single:
    - meta_scope: string.quoted.single.al
    - meta_include_prototype: false
    - match: "''"
      scope: constant.character.escape.al
    - match: "'"
      scope: punctuation.definition.string.end.al
      pop: true

  string-verbatim:
    - meta_scope: string.quoted.other.al
    - meta_include_prototype: false
    - match: "''"
      scope: constant.character.escape.al
    - match: "'"
      scope: punctuation.definition.string.end.al
      pop: true

  quoted-identifiers:
    - match: '"'
      scope: punctuation.definition.variable.begin.al
      push: quoted-identifier

  quoted-identifier:
    - meta_scope: variable.other.quoted.al
    - meta_include_prototype: false
    - match: '"'
      scope: punctuation.definition.variable.end.al
      pop: true

  # ===========================================================================
  # Numeric Literals
  # ===========================================================================

  numeric-literals:
    # DateTime: 0DT or digits+DT (must come before date)
    - match: \b\d+(?i:DT)\b
      scope: constant.numeric.datetime.al
    # Date: 0D or digits+D
    - match: \b\d+(?i:D)\b
      scope: constant.numeric.date.al
    # Time: 0T or 6-digit+T
    - match: \b\d+(?i:T)\b
      scope: constant.numeric.time.al
    # BigInteger: digits+L
    - match: \b\d+(?i:L)\b
      scope: constant.numeric.biginteger.al
    # Decimal: digits.digits
    - match: \b\d+\.\d+\b
      scope: constant.numeric.decimal.al
    # Integer
    - match: \b\d+\b
      scope: constant.numeric.integer.al

  # ===========================================================================
  # Keywords (flat matching for statement-level code)
  # ===========================================================================

  keywords:
    - include: operators
    - include: keyword-constants
    - include: keyword-control
    - include: keyword-operators
    - include: keyword-builtin-types
    - include: keyword-property

  keyword-constants:
    - match: \b(?i:true|false)\b
      scope: constant.language.al

  keyword-control:
    - match: \b(?i:if|then|else|case|of|while|do|for|foreach|in|repeat|until|exit|break|continue|with|asserterror|to|downto|begin|end)\b
      scope: keyword.control.al

  keyword-operators:
    - match: \b(?i:and|or|not|xor|div|mod|is|as)\b
      scope: keyword.operator.al

  keyword-builtin-types:
    - match: \b(?i:Integer|BigInteger|Decimal|Text|Code|Boolean|Char|Byte|Date|Time|DateTime|DateFormula|Duration|Guid|Blob|Record|RecordId|RecordRef|FieldRef|KeyRef|Option|Dialog|File|InStream|OutStream|TextBuilder|JsonObject|JsonArray|JsonToken|JsonValue|HttpClient|HttpContent|HttpHeaders|HttpRequestMessage|HttpResponseMessage|XmlDocument|XmlElement|XmlNode|XmlNodeList|XmlAttribute|XmlComment|XmlText|XmlCData|XmlDeclaration|XmlNamespaceManager|XmlWriteOptions|XmlReadOptions|List|Dictionary|Notification|ErrorInfo|Media|MediaSet|Variant|Action|FilterPageBuilder|SessionSettings|WebServiceActionContext|Label|TextConst|SecretText|Version|ModuleInfo|DotNet)\b
      scope: support.type.al

  keyword-property:
    - match: \b(?i:average|const|count|exist|field|filter|lookup|max|min|order|sorting|sum|tabledata|upperlimit|where|ascending|descending)\b
      scope: keyword.other.property.al

  operators:
    # Assignment operators (must come before comparison =)
    - match: ':=|\+=|-=|/=|\*='
      scope: keyword.operator.assignment.al
    # Comparison operators
    - match: '<>|<=|>=|<|>|='
      scope: keyword.operator.comparison.al
    # Range operator
    - match: '\.\.'
      scope: keyword.operator.range.al
    # Enum/scope accessor
    - match: '::'
      scope: punctuation.accessor.al
    # Arithmetic operators
    - match: '[+\-*/]'
      scope: keyword.operator.arithmetic.al
    # Punctuation
    - match: '[;,]'
      scope: punctuation.separator.al
    - match: '\.'
      scope: punctuation.accessor.dot.al
```

- [ ] **Step 2: Verify it loads without errors**

Open Sublime Text, open any `.al` file. Check the console (`Ctrl+`` `) for syntax errors. The bottom status bar should show "AL" as the syntax.

Alternatively, if you have Sublime's `sublime_syntax_test` or `PackageDev` installed:
```bash
# From Sublime console:
# sublime.run_command("build", {"variant": "Syntax Tests"})
```

- [ ] **Step 3: Commit**

```bash
cd "U:/Git/sublime-al"
git add AL.sublime-syntax
git commit -m "feat: add syntax foundation — literals, comments, preprocessor, keywords"
```

---

### Task 3: Object Declaration Contexts

**Files:**
- Modify: `U:/Git/sublime-al/AL.sublime-syntax`

Add `object-header` and `object-body` contexts so that object declarations get proper structural highlighting.

- [ ] **Step 1: Add object declaration matching to `main` context**

Insert before `- include: literals` in `main`:

```yaml
  main:
    - include: object-declarations
    - include: literals
    - include: keywords
```

- [ ] **Step 2: Add the object-declarations, object-header, and object-body contexts**

Add after the `preprocessor-rest` context:

```yaml
  # ===========================================================================
  # Object Declarations
  # ===========================================================================

  object-declarations:
    - match: \b(?i:codeunit|table|tableextension|page|pageextension|report|reportextension|query|xmlport|enum|enumextension|interface|controladdin|dotnet|profile|profileextension|permissionset|permissionsetextension|entitlement|pagecustomization)\b
      scope: storage.type.al
      push: object-header

  object-header:
    - match: \b\d+\b
      scope: constant.numeric.integer.al
    - match: '"[^"]*"'
      scope: entity.name.type.al
    - match: '{{ident}}'
      scope: entity.name.type.al
    - match: \b(?i:extends|implements|customizes)\b
      scope: keyword.import.al
    - match: \{
      scope: punctuation.section.block.begin.al
      set: object-body
    - match: $\n?
      # Stay in header across newlines until {

  object-body:
    - meta_scope: meta.block.al
    - match: \}
      scope: punctuation.section.block.end.al
      pop: true
    - include: object-body-contents

  object-body-contents:
    - include: attributes
    - include: procedure-declarations
    - include: var-sections
    - include: section-keywords
    - include: nested-braces
    - include: literals
    - include: keywords

  section-keywords:
    - match: \b(?i:fields|keys|key|fieldgroups|fieldgroup|actions|layout|area|group|repeater|cuegroup|fixed|grid|part|systempart|usercontrol|dataset|elements|dataitem|column|filter|labels|rendering|requestpage|schema|views|view|field|value|separator|label|modify|add|addfirst|addlast|addafter|addbefore|movefirst|movelast|moveafter|movebefore)\b
      scope: keyword.other.al

  nested-braces:
    - match: \{
      scope: punctuation.section.block.begin.al
      push: object-body-nested

  object-body-nested:
    - meta_scope: meta.block.al
    - match: \}
      scope: punctuation.section.block.end.al
      pop: true
    - include: object-body-contents
```

- [ ] **Step 3: Verify object highlighting**

Open an AL file with object declarations. Verify:
- `codeunit` is highlighted as `storage.type`
- Object ID (`50000`) is `constant.numeric`
- Object name (`"My Object"`) is `entity.name.type`
- `extends`/`implements` is `keyword.import`
- Body content is highlighted with keywords

- [ ] **Step 4: Commit**

```bash
cd "U:/Git/sublime-al"
git add AL.sublime-syntax
git commit -m "feat: add object declaration contexts with header and body"
```

---

### Task 4: Procedure and Trigger Contexts

**Files:**
- Modify: `U:/Git/sublime-al/AL.sublime-syntax`

Add procedure/trigger declaration contexts with name highlighting and parameter list parsing.

- [ ] **Step 1: Add procedure-declarations and related contexts**

Add after `section-keywords`:

```yaml
  # ===========================================================================
  # Procedures and Triggers
  # ===========================================================================

  procedure-declarations:
    # Modifiers before procedure/trigger
    - match: \b(?i:local|internal|protected)\b
      scope: storage.modifier.al
    # procedure keyword + name
    - match: \b(?i:procedure)\b
      scope: keyword.declaration.al
      push: procedure-name
    # trigger keyword + name
    - match: \b(?i:trigger)\b
      scope: keyword.declaration.al
      push: procedure-name
    # event keyword
    - match: \b(?i:event)\b
      scope: keyword.declaration.al
      push: procedure-name

  procedure-name:
    - match: '"[^"]*"'
      scope: entity.name.function.al
      set: procedure-params-expect
    - match: '{{ident}}'
      scope: entity.name.function.al
      set: procedure-params-expect
    - match: (?=\S)
      pop: true

  procedure-params-expect:
    - match: \(
      scope: punctuation.section.parameters.begin.al
      set: parameter-list
    - match: (?=\S)
      pop: true

  parameter-list:
    - match: \)
      scope: punctuation.section.parameters.end.al
      set: procedure-return
    - match: \b(?i:var)\b
      scope: storage.modifier.al
    - match: ':'
      scope: punctuation.separator.type.al
      push: type-annotation
    - match: '"[^"]*"'
      scope: variable.parameter.al
    - match: '{{ident}}'
      scope: variable.parameter.al
    - match: ;
      scope: punctuation.separator.al
    - include: literals

  procedure-return:
    # Return type after ): Type or name: Type
    - match: ':'
      scope: punctuation.separator.type.al
      push: type-annotation
    - match: ;
      scope: punctuation.terminator.al
      pop: true
    - match: '{{ident}}'
      scope: variable.other.al
    - match: (?=\b(?i:var|begin)\b)
      pop: true
    - match: (?=\{|\})
      pop: true

  type-annotation:
    - match: \b(?i:Integer|BigInteger|Decimal|Text|Code|Boolean|Char|Byte|Date|Time|DateTime|DateFormula|Duration|Guid|Blob|Record|RecordId|RecordRef|FieldRef|KeyRef|Option|Dialog|File|InStream|OutStream|TextBuilder|JsonObject|JsonArray|JsonToken|JsonValue|HttpClient|HttpContent|HttpHeaders|HttpRequestMessage|HttpResponseMessage|XmlDocument|XmlElement|XmlNode|XmlNodeList|XmlAttribute|XmlComment|XmlText|XmlCData|XmlDeclaration|XmlNamespaceManager|XmlWriteOptions|XmlReadOptions|List|Dictionary|Notification|ErrorInfo|Media|MediaSet|Variant|Action|FilterPageBuilder|SessionSettings|WebServiceActionContext|Label|TextConst|SecretText|Version|ModuleInfo|DotNet)\b
      scope: support.type.al
    - match: \b(?i:Codeunit|Record|Page|Report|Query|XmlPort|Enum|Interface)\b
      scope: support.type.al
    - match: \b(?i:array)\b
      scope: support.type.al
    - match: \b(?i:temporary)\b
      scope: storage.modifier.al
    - match: '"[^"]*"'
      scope: entity.name.type.al
    - match: '{{ident}}'
      scope: storage.type.al
    - match: \[
      scope: punctuation.section.brackets.begin.al
      push: type-brackets
    - match: (?=[;,)])
      pop: true

  type-brackets:
    - match: \]
      scope: punctuation.section.brackets.end.al
      pop: true
    - include: numeric-literals
    - include: strings
```

- [ ] **Step 2: Verify procedure highlighting**

Open an AL file with procedures. Verify:
- `local` is `storage.modifier`
- `procedure` is `keyword.declaration`
- `MyMethod` is `entity.name.function`
- Parameter names are `variable.parameter`
- Types after `:` are `support.type`
- Quoted type names like `"Customer"` are `entity.name.type`

- [ ] **Step 3: Commit**

```bash
cd "U:/Git/sublime-al"
git add AL.sublime-syntax
git commit -m "feat: add procedure/trigger declaration contexts with parameters and types"
```

---

### Task 5: Var Section and Attribute Contexts

**Files:**
- Modify: `U:/Git/sublime-al/AL.sublime-syntax`

Add var section context (variable name + type annotation) and attribute context (`[...]`).

- [ ] **Step 1: Add var-sections context**

Add after `type-brackets`:

```yaml
  # ===========================================================================
  # Var Sections
  # ===========================================================================

  var-sections:
    - match: \b(?i:var)\b
      scope: keyword.declaration.al
      push: var-section

  var-section:
    # Exit on begin, procedure, trigger, or closing brace
    - match: (?=\b(?i:begin|procedure|trigger|event)\b)
      pop: true
    - match: (?=\})
      pop: true
    # Variable declaration: name : type ;
    - match: ':'
      scope: punctuation.separator.type.al
      push: type-annotation
    - match: '"[^"]*"'
      scope: variable.other.al
    - match: '{{ident}}'
      scope: variable.other.al
    - match: ;
      scope: punctuation.separator.al
    - include: literals

  # ===========================================================================
  # Attributes
  # ===========================================================================

  attributes:
    - match: '\['
      scope: punctuation.definition.annotation.begin.al
      push: attribute-body

  attribute-body:
    - meta_scope: meta.annotation.al
    - match: '\]'
      scope: punctuation.definition.annotation.end.al
      pop: true
    - match: '{{ident}}'
      scope: variable.annotation.al
    - match: \(
      scope: punctuation.section.arguments.begin.al
      push: attribute-arguments
    - include: literals

  attribute-arguments:
    - match: \)
      scope: punctuation.section.arguments.end.al
      pop: true
    - match: ','
      scope: punctuation.separator.al
    - include: literals
    - match: '{{ident}}'
      scope: variable.other.al
```

- [ ] **Step 2: Verify**

Open an AL file. Check:
- `var` keyword highlighted as `keyword.declaration`
- Variable names in var sections scoped as `variable.other`
- Type annotations after `:` work correctly
- `[Scope('OnPrem')]` — brackets are `meta.annotation`, `Scope` is `variable.annotation`, `'OnPrem'` is `string.quoted.single`

- [ ] **Step 3: Commit**

```bash
cd "U:/Git/sublime-al"
git add AL.sublime-syntax
git commit -m "feat: add var section and attribute contexts"
```

---

### Task 6: Namespace/Using and Structure Keywords in Main

**Files:**
- Modify: `U:/Git/sublime-al/AL.sublime-syntax`

Add namespace/using support to the `main` context so top-level structure is highlighted.

- [ ] **Step 1: Add namespace-using to main**

Insert into `main` context before `object-declarations`:

```yaml
  main:
    - include: namespace-using
    - include: object-declarations
    - include: literals
    - include: keywords
```

Add the context:

```yaml
  # ===========================================================================
  # Namespace and Using
  # ===========================================================================

  namespace-using:
    - match: \b(?i:namespace|using)\b
      scope: keyword.import.al
```

- [ ] **Step 2: Commit**

```bash
cd "U:/Git/sublime-al"
git add AL.sublime-syntax
git commit -m "feat: add namespace/using keyword support"
```

---

### Task 7: Syntax Tests

**Files:**
- Create: `U:/Git/sublime-al/tests/syntax_test_al.al`

Write Sublime syntax test file covering all major constructs.

- [ ] **Step 1: Create test file**

Create `U:/Git/sublime-al/tests/syntax_test_al.al`:
```al
// SYNTAX TEST "Packages/AL/AL.sublime-syntax"

namespace MyCompany.MyApp;
// ^^^^^^^ keyword.import.al

using System.Text;
// ^^^ keyword.import.al

codeunit 50000 "My Codeunit" implements IFace
// ^^^^^ storage.type.al
//       ^^^^^ constant.numeric.integer.al
//             ^^^^^^^^^^^^^^ entity.name.type.al
//                            ^^^^^^^^^^ keyword.import.al
{
    var
//  ^^^ keyword.declaration.al
        MyVar: Integer;
//      ^^^^^ variable.other.al
//             ^^^^^^^ support.type.al

    [Scope('OnPrem')]
//   ^^^^^ variable.annotation.al
//         ^^^^^^^^ string.quoted.single.al

    local procedure MyMethod(var Param: Record "Customer"): Boolean
//  ^^^^^ storage.modifier.al
//        ^^^^^^^^^ keyword.declaration.al
//                  ^^^^^^^^ entity.name.function.al
//                           ^^^ storage.modifier.al
//                               ^^^^^ variable.parameter.al
//                                      ^^^^^^ support.type.al
//                                             ^^^^^^^^^^ entity.name.type.al
//                                                         ^^^^^^^ support.type.al
    var
        x: Integer;
    begin
//  ^^^^^ keyword.control.al
        if x > 0 then
//      ^^ keyword.control.al
//             ^ keyword.operator.comparison.al
//               ^^^^ keyword.control.al
            x := x + 1;
//            ^^ keyword.operator.assignment.al
//                 ^ keyword.operator.arithmetic.al
        MyVar := 'hello';
//               ^^^^^^^ string.quoted.single.al
        exit(true);
//      ^^^^ keyword.control.al
//           ^^^^ constant.language.al
    end;
//  ^^^ keyword.control.al
}

table 50000 "My Table"
// ^^ storage.type.al
{
    fields
//  ^^^^^^ keyword.other.al
    {
        field(1; "No."; Code[20])
        {
            Caption = 'Number';
//                    ^^^^^^^^ string.quoted.single.al
        }
    }
}

// Preprocessor
#if not CLEAN25
// <- keyword.control.import.al
//  ^^^ keyword.operator.al
//      ^^^^^^^ variable.other.al
#else
// <- keyword.control.import.al
#endif
// <- keyword.control.import.al

// Operators
#pragma warning disable AL0432
// <- keyword.control.import.al

// Verbatim string
//    @'hello
//    world'
// would be string.quoted.other.al

// Numeric literals
// 42 is constant.numeric.integer.al
// 3.14 is constant.numeric.decimal.al
// 0DT is constant.numeric.datetime.al
// 0D is constant.numeric.date.al
// 0T is constant.numeric.time.al
// 1000L is constant.numeric.biginteger.al

// Quoted identifier
//    "Customer No." is variable.other.quoted.al

// Comments
/* block comment */
// ^^^^^^^^^^^^^ comment.block.al

// line comment
// <- comment.line.double-slash.al
```

- [ ] **Step 2: Run syntax tests**

In Sublime Text, open the test file and run `Tools > Build` with the `Syntax Tests` build system. Or from the console:
```
sublime.run_command("build", {"variant": "Syntax Tests - All"})
```

Fix any assertion failures.

- [ ] **Step 3: Commit**

```bash
cd "U:/Git/sublime-al"
git add tests/
git commit -m "test: add syntax test file covering all major AL constructs"
```

---

### Task 8: Completions and Generation Script

**Files:**
- Create: `U:/Git/sublime-al/AL.sublime-completions`
- Create: `U:/Git/sublime-al/scripts/generate-completions.js`

- [ ] **Step 1: Create the completions file**

Create `U:/Git/sublime-al/AL.sublime-completions`:
```json
{
    "scope": "source.al",
    "completions": [
        {"trigger": "asserterror", "kind": "keyword"},
        {"trigger": "begin", "kind": "keyword"},
        {"trigger": "break", "kind": "keyword"},
        {"trigger": "case", "kind": "keyword"},
        {"trigger": "continue", "kind": "keyword"},
        {"trigger": "do", "kind": "keyword"},
        {"trigger": "downto", "kind": "keyword"},
        {"trigger": "else", "kind": "keyword"},
        {"trigger": "end", "kind": "keyword"},
        {"trigger": "exit", "kind": "keyword"},
        {"trigger": "for", "kind": "keyword"},
        {"trigger": "foreach", "kind": "keyword"},
        {"trigger": "if", "kind": "keyword"},
        {"trigger": "in", "kind": "keyword"},
        {"trigger": "of", "kind": "keyword"},
        {"trigger": "repeat", "kind": "keyword"},
        {"trigger": "then", "kind": "keyword"},
        {"trigger": "to", "kind": "keyword"},
        {"trigger": "until", "kind": "keyword"},
        {"trigger": "while", "kind": "keyword"},
        {"trigger": "with", "kind": "keyword"},
        {"trigger": "procedure", "kind": "keyword"},
        {"trigger": "trigger", "kind": "keyword"},
        {"trigger": "var", "kind": "keyword"},
        {"trigger": "event", "kind": "keyword"},
        {"trigger": "local", "kind": "keyword"},
        {"trigger": "internal", "kind": "keyword"},
        {"trigger": "protected", "kind": "keyword"},
        {"trigger": "temporary", "kind": "keyword"},
        {"trigger": "codeunit", "kind": "keyword"},
        {"trigger": "table", "kind": "keyword"},
        {"trigger": "tableextension", "kind": "keyword"},
        {"trigger": "page", "kind": "keyword"},
        {"trigger": "pageextension", "kind": "keyword"},
        {"trigger": "report", "kind": "keyword"},
        {"trigger": "reportextension", "kind": "keyword"},
        {"trigger": "query", "kind": "keyword"},
        {"trigger": "xmlport", "kind": "keyword"},
        {"trigger": "enum", "kind": "keyword"},
        {"trigger": "enumextension", "kind": "keyword"},
        {"trigger": "interface", "kind": "keyword"},
        {"trigger": "controladdin", "kind": "keyword"},
        {"trigger": "dotnet", "kind": "keyword"},
        {"trigger": "profile", "kind": "keyword"},
        {"trigger": "profileextension", "kind": "keyword"},
        {"trigger": "permissionset", "kind": "keyword"},
        {"trigger": "permissionsetextension", "kind": "keyword"},
        {"trigger": "entitlement", "kind": "keyword"},
        {"trigger": "namespace", "kind": "keyword"},
        {"trigger": "using", "kind": "keyword"},
        {"trigger": "extends", "kind": "keyword"},
        {"trigger": "implements", "kind": "keyword"},
        {"trigger": "and", "kind": "keyword"},
        {"trigger": "or", "kind": "keyword"},
        {"trigger": "not", "kind": "keyword"},
        {"trigger": "xor", "kind": "keyword"},
        {"trigger": "div", "kind": "keyword"},
        {"trigger": "mod", "kind": "keyword"},
        {"trigger": "true", "kind": "keyword"},
        {"trigger": "false", "kind": "keyword"},
        {"trigger": "Integer", "kind": "type"},
        {"trigger": "BigInteger", "kind": "type"},
        {"trigger": "Decimal", "kind": "type"},
        {"trigger": "Text", "kind": "type"},
        {"trigger": "Code", "kind": "type"},
        {"trigger": "Boolean", "kind": "type"},
        {"trigger": "Char", "kind": "type"},
        {"trigger": "Byte", "kind": "type"},
        {"trigger": "Date", "kind": "type"},
        {"trigger": "Time", "kind": "type"},
        {"trigger": "DateTime", "kind": "type"},
        {"trigger": "DateFormula", "kind": "type"},
        {"trigger": "Duration", "kind": "type"},
        {"trigger": "Guid", "kind": "type"},
        {"trigger": "Blob", "kind": "type"},
        {"trigger": "Record", "kind": "type"},
        {"trigger": "RecordId", "kind": "type"},
        {"trigger": "RecordRef", "kind": "type"},
        {"trigger": "FieldRef", "kind": "type"},
        {"trigger": "KeyRef", "kind": "type"},
        {"trigger": "Option", "kind": "type"},
        {"trigger": "Dialog", "kind": "type"},
        {"trigger": "File", "kind": "type"},
        {"trigger": "InStream", "kind": "type"},
        {"trigger": "OutStream", "kind": "type"},
        {"trigger": "TextBuilder", "kind": "type"},
        {"trigger": "JsonObject", "kind": "type"},
        {"trigger": "JsonArray", "kind": "type"},
        {"trigger": "JsonToken", "kind": "type"},
        {"trigger": "JsonValue", "kind": "type"},
        {"trigger": "HttpClient", "kind": "type"},
        {"trigger": "HttpContent", "kind": "type"},
        {"trigger": "HttpHeaders", "kind": "type"},
        {"trigger": "HttpRequestMessage", "kind": "type"},
        {"trigger": "HttpResponseMessage", "kind": "type"},
        {"trigger": "XmlDocument", "kind": "type"},
        {"trigger": "XmlElement", "kind": "type"},
        {"trigger": "XmlNode", "kind": "type"},
        {"trigger": "XmlNodeList", "kind": "type"},
        {"trigger": "XmlAttribute", "kind": "type"},
        {"trigger": "List", "kind": "type"},
        {"trigger": "Dictionary", "kind": "type"},
        {"trigger": "Notification", "kind": "type"},
        {"trigger": "ErrorInfo", "kind": "type"},
        {"trigger": "Media", "kind": "type"},
        {"trigger": "MediaSet", "kind": "type"},
        {"trigger": "Variant", "kind": "type"},
        {"trigger": "Label", "kind": "type"},
        {"trigger": "TextConst", "kind": "type"},
        {"trigger": "SecretText", "kind": "type"},
        {"trigger": "Version", "kind": "type"},
        {"trigger": "DotNet", "kind": "type"},
        {"trigger": "Action", "kind": "type"}
    ]
}
```

- [ ] **Step 2: Create the generation script**

Create `U:/Git/sublime-al/scripts/generate-completions.js`:
```javascript
#!/usr/bin/env node
// Extracts keywords from tree-sitter-al grammar.js and generates AL.sublime-completions
// Usage: node generate-completions.js <path-to-grammar.js>

const fs = require('fs');
const path = require('path');

const grammarPath = process.argv[2];
if (!grammarPath) {
    console.error('Usage: node generate-completions.js <path-to-grammar.js>');
    process.exit(1);
}

const grammar = fs.readFileSync(grammarPath, 'utf8');

// Extract kw('...') calls
const kwMatches = [...grammar.matchAll(/kw\('(\w+)'\)/g)];
const keywords = [...new Set(kwMatches.map(m => m[1].toLowerCase()))];

// Built-in types from the spec (not easily extractable from grammar.js regex patterns)
const types = [
    'Integer', 'BigInteger', 'Decimal', 'Text', 'Code', 'Boolean', 'Char', 'Byte',
    'Date', 'Time', 'DateTime', 'DateFormula', 'Duration', 'Guid', 'Blob', 'Record',
    'RecordId', 'RecordRef', 'FieldRef', 'KeyRef', 'Option', 'Dialog', 'File',
    'InStream', 'OutStream', 'TextBuilder', 'JsonObject', 'JsonArray', 'JsonToken',
    'JsonValue', 'HttpClient', 'HttpContent', 'HttpHeaders', 'HttpRequestMessage',
    'HttpResponseMessage', 'XmlDocument', 'XmlElement', 'XmlNode', 'XmlNodeList',
    'XmlAttribute', 'List', 'Dictionary', 'Notification', 'ErrorInfo', 'Media',
    'MediaSet', 'Variant', 'Label', 'TextConst', 'SecretText', 'Version', 'DotNet',
    'Action'
];

const completions = [
    ...keywords.sort().map(k => ({ trigger: k, kind: 'keyword' })),
    ...types.sort().map(t => ({ trigger: t, kind: 'type' })),
];

const output = {
    scope: 'source.al',
    completions
};

const outputPath = path.join(path.dirname(__dirname), 'AL.sublime-completions');
fs.writeFileSync(outputPath, JSON.stringify(output, null, 4) + '\n');
console.log(`Generated ${completions.length} completions to ${outputPath}`);
```

- [ ] **Step 3: Verify the script runs**

```bash
cd "U:/Git/sublime-al"
node scripts/generate-completions.js "U:/Git/tree-sitter-al/grammar.js"
```

Expected: `Generated N completions to .../AL.sublime-completions`

- [ ] **Step 4: Commit**

```bash
cd "U:/Git/sublime-al"
git add AL.sublime-completions scripts/
git commit -m "feat: add keyword/type completions and generation script"
```

---

### Task 9: README

**Files:**
- Create: `U:/Git/sublime-al/README.md`

- [ ] **Step 1: Write the README**

Create `U:/Git/sublime-al/README.md`:
````markdown
# AL for Sublime Text

Syntax highlighting for the AL programming language used in Microsoft Dynamics 365 Business Central.

## Features

- Full syntax highlighting for AL files (`.al`, `.dal`)
- Context-aware scoping for object declarations, procedures, var sections, and attributes
- Preprocessor directive highlighting (`#if`, `#else`, `#endif`, `#pragma`)
- Keyword completions for all AL keywords and built-in types
- Symbol indexing — jump to procedures/triggers with `Ctrl+R`
- Line and block comment toggling (`Ctrl+/`, `Ctrl+Shift+/`)
- Proper indentation rules for begin/end blocks

## Installation

### Package Control (recommended)

1. Open Command Palette (`Ctrl+Shift+P`)
2. Select `Package Control: Install Package`
3. Search for `AL` and install

### Manual

1. Clone this repo into your Sublime Text Packages directory:
   ```
   cd "%APPDATA%/Sublime Text/Packages"
   git clone https://github.com/SShadowS/sublime-al.git AL
   ```
2. Restart Sublime Text

## LSP Support

For full language intelligence (go-to-definition, diagnostics, completions), install the [LSP-AL](https://github.com/SShadowS/LSP-AL) package which connects to the AL Language Server.

## Highlighting Examples

The syntax highlights:
- **Object declarations** — `codeunit`, `table`, `page`, etc. with ID and name
- **Procedures and triggers** — with parameter types and return types
- **Attributes** — `[Scope('OnPrem')]`, `[NonDebuggable]`
- **Preprocessor** — `#if`, `#else`, `#endif` with condition highlighting
- **Strings** — single-quoted `'text'` and verbatim `@'multiline'`
- **AL-specific literals** — date (`0D`), time (`0T`), datetime (`0DT`), biginteger (`1000L`)

## Regenerating Completions

If the AL language adds new keywords, regenerate completions from the [tree-sitter-al](https://github.com/SShadowS/tree-sitter-al) grammar:

```bash
node scripts/generate-completions.js /path/to/tree-sitter-al/grammar.js
```

## License

MIT
````

- [ ] **Step 2: Commit**

```bash
cd "U:/Git/sublime-al"
git add README.md
git commit -m "docs: add README with installation and feature documentation"
```

---

### Task 10: Final Verification

- [ ] **Step 1: Install in Sublime Text**

Symlink or copy the package to Sublime's Packages directory:
```bash
# Windows
mklink /D "%APPDATA%\Sublime Text\Packages\AL" "U:\Git\sublime-al"
```

- [ ] **Step 2: Open test AL files**

Open several real AL files from `U:/Git/DO.Support-Reviewer3/` or `U:/Git/tree-sitter-al/BC.History/`. Verify:
- Object declarations (codeunit, table, page, etc.) highlighted correctly
- Procedure/trigger names stand out
- Parameters and types are distinguishable
- Attributes scoped properly
- Strings, comments, preprocessor all work
- No false highlighting (keywords inside strings shouldn't be colored)
- Quoted identifiers (`"Customer"`) distinct from strings

- [ ] **Step 3: Run syntax tests**

In Sublime, open `tests/syntax_test_al.al` and run syntax tests. Fix any failures.

- [ ] **Step 4: Final commit**

```bash
cd "U:/Git/sublime-al"
git add -A
git commit -m "chore: final verification pass"
```

---

## Execution Order & Dependencies

| Task | Description | Dependencies |
|------|-------------|-------------|
| 1 | Repo setup + settings | None |
| 2 | Syntax foundation (literals, comments, preproc, keywords) | Task 1 |
| 3 | Object declaration contexts | Task 2 |
| 4 | Procedure/trigger contexts | Task 3 |
| 5 | Var section + attribute contexts | Task 4 |
| 6 | Namespace/using keywords | Task 2 |
| 7 | Syntax tests | Task 5 |
| 8 | Completions + generation script | Task 1 |
| 9 | README | Task 1 |
| 10 | Final verification | All above |

Tasks 1→2→3→4→5 are sequential (each builds on the syntax file). Tasks 6, 8, 9 can run in parallel after their dependencies.
