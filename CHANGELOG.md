# Changelog

All notable changes to `tree-sitter-al` are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); the project
uses [Semantic Versioning](https://semver.org/) where the parse-tree shape is the
public API — a change to node structure or field names is a **major** bump.

## [3.0.0] — 2026-06-17

**Breaking parse-tree restructure.** Every scoped construct now exposes its content
as a single node via a `body` field, instead of as a flat list of direct children.
This enables editor textobjects (Helix / nvim-treesitter `@class.inside` etc.) and
cleaner code-navigation queries (GitHub issue #19), but it changes the tree shape, so
any consumer that walks the tree or writes structural queries must update.

Pure highlighting that matches node *types* (not child relationships) is unaffected.

### Migrating

#### 1. Bodies moved under a `body` field (the big one)

Content that used to be direct children of objects, sections, declarations, code
blocks, loops, `case`, and `var` is now nested under a `body` field.

Before:
```scheme
(page_declaration (layout_section) (actions_section))
(code_block (begin_keyword) (assignment_statement) (end_keyword))
(case_statement (case_branch) (case_branch))
(var_section (variable_declaration) (variable_declaration))
```
After:
```scheme
(page_declaration body: (declaration_body (layout_section) (actions_section)))
(code_block (begin_keyword) body: (statement_block (assignment_statement)) (end_keyword))
(case_statement body: (case_body (case_branch) (case_branch)))
(var_section body: (var_body (variable_declaration) (variable_declaration)))
```

- **Tree-walkers:** descend through `body` (one level) before reading members.
- **Queries:** replace child-anchored patterns like `(code_block (assignment_statement) @s)`
  with field-based ones: `(code_block body: (statement_block (assignment_statement) @s))`,
  or use the universal `(_ body: (_) @inside)`.

#### 2. New named node types (handle in exhaustive switches / regenerate bindings)

`declaration_body`, `statement_block`, `case_body`, `var_body`, `fields_body`,
`keys_body`, `fieldgroups_body`, `labels_body`, `layout_body`, `layout_container_body`,
`action_body`, `action_group_body`, `views_body`, `views_mod_body`, `dataset_body`,
`dataset_mod_body`, `report_body`, `rendering_body`, `analysisviews_body`,
`elements_body`, `query_body`, `schema_body`, `xmlport_body`, `assembly_body`,
`dotnet_body`, `controladdin_body`, `interface_body`.

Rust / TypeScript typed bindings: regenerate against the new `src/node-types.json` and
add the new kinds (or a default arm) to any exhaustive `match`/`switch`.

#### 3. New fields

- `parameters` on `procedure`, `trigger`, and `event_declaration` (previously an
  unnamed `parameter_list` child). Positional access still finds the same node;
  `parameters: (parameter_list)` now also works.
- `body` on every scoped construct, the loop statements, and `code_block`.

#### 4. `case` closing `end` is now a named node

The closing `end` of a `case … of … end` is now `(end_keyword)` at preprocessor
depth 0 (it was an anonymous `"end"` token), matching `code_block`. Update queries /
walkers that keyed on the anonymous string.

#### 5. Empty bodies emit no node

`{ }`, `begin end`, and an empty `var` produce **no** `body` node (tree-sitter forbids
a rule that matches the empty string). Never assume `body` is present — guard for its
absence. `(_ body: (_))` simply does not match empty constructs, which is correct.

#### 6. `repeat` body always wraps; other loops do not

`repeat_statement` body is always `(statement_block)`. `for` / `foreach` / `while` /
`with` bodies remain `choice(<single statement>, code_block)` — a single-statement body
has no wrapper. Do not assume symmetry across loop kinds.

### Added

- `queries/textobjects.scm` — Helix / nvim-treesitter textobject queries
  (`@class.inside/around`, `@function.inside/around`, `@parameter`, generic
  `@block.inside/around`). Query files: 5 → 6.
- `body` field across all scoped constructs; `parameters` field on procedure/trigger/event.
- Content-only `statement_block` node inside `code_block`, reused by `repeat_statement`
  and the preprocessor-split routine bodies.
- `case_body`, `var_body`, and the per-construct `*_body` nodes listed above.

### Changed

- Renamed the shared `_body_element` wrapper node `object_body` → `declaration_body`
  (it is reused well beyond objects — fields, keys, enum values, etc.).
- `case` closing `end` exposed as `end_keyword` (see migration §4).

### Unchanged / not affected

- In-repo queries `highlights.scm`, `locals.scm`, `tags.scm`, `indents.scm`,
  `folds.scm` (they match node types, not the now-nested children).
- Production parse coverage: **15,358 / 15,358 BC.History files, 0 errors (100%)**.
- 1,451 corpus tests passing; external scanner ABI unchanged.

### Decisions / known limitations

- **Attributes remain siblings**, not children/fields of their target declaration
  (preprocessor directives can sit between an attribute and its declaration; the
  first-class-statement model is deliberate — see `.claude/rules/attributes.md`).
  Associating attributes with targets is a post-parse / LSP concern.
- Empty bodies and single-statement loop bodies have no wrapper node — by design
  (see migration §5 and §6).
- See `docs/superpowers/specs/2026-06-17-body-field-textobjects-design.md` for the
  full design and rationale.
