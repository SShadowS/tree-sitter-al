# Analysis of Grammar Conflicts in `grammar.js`

This document provides an analysis of the conflicts defined in the `grammar.js` file for the tree-sitter-al parser. Each conflict is explained with its root cause and potential solutions.

---

### 1. `[$._source_content, $.preproc_conditional_using]`

- **Conflict:** `[$._source_content, $.preproc_conditional_using]`
- **Rules Involved:**
  - `_source_content`: Represents the main body of a source file, which can contain `using` statements.
  - `preproc_conditional_using`: A preprocessor block (`#if...#endif`) specifically wrapping `using` statements.
- **Reason for Conflict:**
  The `_source_content` rule is defined to contain `preproc_conditional_using`. This creates an ambiguity when the parser encounters a preprocessor directive. The parser cannot decide whether the directive is part of a `preproc_conditional_using` construct or a more general preprocessor block within the broader `_source_content`. This is a classic ambiguity with nested structures.
- **Resolution:**
  This conflict is intentional and necessary. It signals to tree-sitter that `preproc_conditional_using` should be prioritized when its pattern matches, allowing the parser to correctly identify conditional using statements within the larger source file structure. No resolution is needed as this is the correct way to handle such ambiguities in tree-sitter.

---

### 2. `[$._source_content]`

- **Conflict:** `[$._source_content]`
- **Rule Involved:**
  - `_source_content`: `seq(repeat($.pragma), optional($.namespace_declaration), repeat(choice($.using_statement, $.preproc_conditional_using)), repeat1(choice($._object, $.pragma)))`
- **Reason for Conflict:**
  A conflict on a single rule typically points to an internal ambiguity. The structure of `_source_content` with its repeating and optional elements can lead to multiple valid parse trees for the same input. For instance, a pragma could be matched by `repeat($.pragma)` at the beginning or as part of the `repeat1(choice($._object, $.pragma))` at the end.
- **Resolution:**
  This conflict is likely required to handle the flexible nature of AL source files. It allows the parser to consider different valid structures. While it might be possible to eliminate the conflict by reordering or restructuring the rule, this could make the grammar less resilient to variations in source file layout. The conflict declaration is a pragmatic approach to manage this ambiguity.

---

### 3. `[$.assignment_expression, $._assignable_expression]`

- **Conflict:** `[$.assignment_expression, $._assignable_expression]`
- **Rules Involved:**
  - `assignment_expression`: `seq(field('left', $._assignable_expression), $._assignment_operator, field('right', $._expression))`
  - `_assignable_expression`: `choice($.identifier, $.member_expression, $.subscript_expression)`
- **Reason for Conflict:**
  An `assignment_expression` has an `_assignable_expression` on its left-hand side. An `_assignable_expression` can be a simple `identifier` or a more complex expression like a `member_expression` (e.g., `MyRec.MyField`). When the parser sees an identifier, it doesn't know whether to immediately consider it a complete `_assignable_expression` or to wait for subsequent tokens (like a `.`) that would make it part of a larger expression.
- **Resolution:**
  This conflict is inherent to parsing expressions and is best resolved by declaring it. This allows the parser to explore both possibilities and choose the correct one based on the surrounding code, preventing premature decisions.

---

### 4. `[$.assignment_statement, $.assignment_expression]`

- **Conflict:** `[$.assignment_statement, $.assignment_expression]`
- **Rules Involved:**
  - `assignment_statement`: `$.assignment_expression`
  - `assignment_expression`: Can be used in contexts where expressions are expected.
- **Reason for Conflict:**
  In AL, an assignment can function as both a standalone statement and as an expression within a larger statement. This creates ambiguity in contexts where either is permissible. For example, in a code block, `a := b` could be interpreted as an `assignment_statement` or an `assignment_expression`.
- **Resolution:**
  This is a classic statement vs. expression ambiguity. Declaring the conflict is the standard way to handle this in tree-sitter, allowing the parser to correctly interpret assignments based on their context.

---

### 5. `[$.preproc_conditional_enum_properties, $.preproc_conditional_enum_values]`

- **Conflict:** `[$.preproc_conditional_enum_properties, $.preproc_conditional_enum_values]`
- **Rules Involved:**
  - `enum_declaration`: Contains `repeat(choice(..., $.preproc_conditional_enum_properties, $.preproc_conditional_enum_values))`
  - `preproc_conditional_enum_properties`: A preprocessor block around enum properties.
  - `preproc_conditional_enum_values`: A preprocessor block around enum values.
- **Reason for Conflict:**
  Both of these rules begin with a preprocessor directive (`#if`). When the parser encounters an `#if` inside an enum declaration, it cannot determine whether the conditional block contains properties or values until it parses the content inside the block.
- **Resolution:**
  This conflict is unavoidable due to the nature of preprocessor directives. Declaring the conflict is the correct solution, as it instructs the parser to consider both possibilities and select the appropriate rule based on the content of the preprocessor block.

---

### 6. `[$.source_file]`

- **Conflict:** `[$.source_file]`
- **Rule Involved:**
  - `source_file`: `choice(seq(..., repeat(choice($._object, $.pragma))), $.preprocessor_file_conditional)`
- **Reason for Conflict:**
  This conflict arises from ambiguity at the top level of a file. A source file can start with various optional elements (pragmas, usings) or with a preprocessor directive that wraps the entire file (`preprocessor_file_conditional`). When a file begins with an `#if`, it could be the start of a `preprocessor_file_conditional` or just a regular `source_file` where the first object is conditionally compiled.
- **Resolution:**
  The conflict declaration is necessary to allow the parser to correctly handle files that are entirely wrapped in preprocessor directives, a valid pattern in AL development.

---

### 7. `[$.preproc_conditional_procedures, $.preproc_conditional_mixed_content]`

- **Conflict:** `[$.preproc_conditional_procedures, $.preproc_conditional_mixed_content]`
- **Rules Involved:**
  - `preproc_conditional_procedures`: A preprocessor block containing only procedures or triggers.
  - `preproc_conditional_mixed_content`: A more general preprocessor block that can contain `var_section`s in addition to procedures.
- **Reason for Conflict:**
  `preproc_conditional_mixed_content` is a superset of `preproc_conditional_procedures`. When the parser sees an `#if` followed by a procedure, this sequence is a valid start for both rules. The parser cannot decide which rule to apply without looking ahead.
- **Resolution:**
  This conflict is necessary to handle different combinations of content within preprocessor blocks. By declaring the conflict, tree-sitter can correctly parse blocks with only procedures as well as blocks with a mix of variables and procedures.

---

### 8. `[$.preproc_conditional_var_sections, $.preproc_conditional_mixed_content]`

- **Conflict:** `[$.preproc_conditional_var_sections, $.preproc_conditional_mixed_content]`
- **Rules Involved:**
  - `preproc_conditional_var_sections`: A preprocessor block containing only `var_section`s.
  - `preproc_conditional_mixed_content`: A block that can contain `var_section`s and procedures.
- **Reason for Conflict:**
  This conflict is analogous to the previous one. An `#if` followed by a `var_section` is a valid prefix for both rules. The parser faces an ambiguity that can only be resolved by examining the rest of the content within the preprocessor block.
- **Resolution:**
  Declaring the conflict is the correct approach. It allows the grammar to remain flexible and correctly parse conditional blocks containing only variable sections or a mixture of variables and other constructs.
