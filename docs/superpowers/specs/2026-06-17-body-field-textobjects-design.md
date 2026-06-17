# Body-field wrappers for textobject queries

**Date:** 2026-06-17
**Status:** ✅ Implemented (all constructs)
**Origin:** GitHub issue #19 — "Allow helix textobject queries" (TheJayMann)

## Problem

Helix textobjects require `@<type>.inside` to match **a single node** equal to the
content to select. AL object/section bodies are currently flat:

```js
'{', repeat($._body_element), '}'   // grammar.js:17-64 helpers + ~30 inline sites
```

The `{` `}` are anonymous tokens; body elements are direct siblings of the
declaration. No node spans the inside, so:

```scm
(page_declaration ("{") (_) @class.inside ("}")) @class.around
```

matches a single sibling (one section, one property), never the whole body.
Wildcard variants (`[_]`, `[(_)]`, `([(_)])`) cannot work — there is no single
node to capture. Confirmed by inspecting the parse tree of a sample page.

**Procedures/triggers are already OK-ish:** their body is `code_block` (a single
named `begin … end` node, `grammar.js:2582`). But `code_block` is also reused as a
nested statement block (`grammar.js:2898`), and it *includes* `begin`/`end` as
children, so `.inside` would include the delimiters.

## Correct structure

Model after mature grammars (Rust/C/JS) tuned for the one decision Helix cares
about: **`@x.inside` must equal the content without delimiters.**

> **Delimiters (`{`/`}`, `begin`/`end`) stay as children of the construct.
> A named body node holds content ONLY. Expose it via a uniform `field('body', …)`.**

### Target tree

```
(page_declaration
  (page_keyword) object_id: (integer) object_name: (identifier)
  "{"                          ← delimiter, child of declaration
  body: (object_body           ← single node, content only (no braces)
    (layout_section …)
    (actions_section …))
  "}")                         ← delimiter, child of declaration
```

Helix query becomes trivial and exact:

```scm
(page_declaration body: (_) @class.inside) @class.around
```

`.inside` spans exactly the content (no braces, no editor-side trimming).

### Why content-only (not Rust's brace-inclusive `block`)

Rust's `declaration_list`/`block` include the braces, forcing editor trimming for
"inner". Since we control all consumers, put delimiters *outside* the body node so
`.inside` is exact with zero post-processing.

### Naming: distinct node types, shared field name

Idiomatic tree-sitter uses distinct body node types because allowed children
differ (Rust: `declaration_list`, `field_declaration_list`, `block`,
`enum_variant_list`). Keep that, but always under field name `body`:

| Construct | Body node | Delimiters |
|-----------|-----------|-----------|
| object (page/table/codeunit/enum/…) | `object_body` | `{ }` |
| section (layout/actions/area/fields/keys/…) | `section_body` | `{ }` |
| field / action / control / enum value | per-construct body node | `{ }` |
| procedure / trigger | `statement_block` (begin/end out) | `begin` `end` |

Payoff:
- precise: `(page_declaration body: (object_body))`
- generic: `(_ body: (_) @inside)` — one query covers every scoped construct.

### Procedure/trigger handling

Two options:

1. **(recommended)** Routines expose `body: (statement_block …)` — a content-only
   node with `begin`/`end` as siblings of the routine. Keep `code_block` for nested
   `begin … end` *statements*. Slight duplication, smallest blast radius.
2. Move `begin`/`end` out of `code_block` and reuse it. Larger blast radius (every
   nested-block site changes).

### Empty bodies

**Constraint discovered during prototype:** tree-sitter forbids a named rule that
can match the empty string (`object_body: $ => repeat(...)` fails generate with
*"The rule `object_body` matches the empty string"*). So the body node **cannot**
be made unconditionally present.

Correct shape:

```js
'{', optional(field('body', $.object_body)), '}'
object_body: $ => repeat1($._body_element),
```

Empty `{ }` therefore yields **no** `body` node. This is acceptable — `.inside` on a
truly empty body has nothing to select. Downstream queries must tolerate the
missing node (Helix already no-ops when a capture is absent). The uniform
`(_ body: (_) @inside)` query simply does not match empty constructs, which is
correct behaviour.

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| All 1437 corpus tests change shape | High churn (expected) | `tree-sitter test -u` after confirming 0 ERROR/MISSING |
| Snapshot baseline invalidated | Expected by design | re-snapshot after merge |
| GLR conflicts at body boundary | Low (complete-unit rule) | add `conflicts` entry only if generate reports one |
| Parser size growth | Negligible | one extra reduce/construct |
| BC.History regression | **Gate** | wrapping must not change *what* parses — run `./validate-grammar.sh --full` + `./parse-al-parallel.sh ./BC.History/ .` |

## Rollout

1. **Prototype** (this commit): `page_declaration` standalone with `object_body`.
   Confirm Helix query matches, no GLR conflict, no new ERRORs.
   **Result:** ✅ generate clean (0 conflicts); `body: (object_body …)` spans content
   only (no braces); `(page_declaration body: (_) @class.inside) @class.around` returns
   a single `@class.inside` node; empty `{ }` → no body node, no error; 355 corpus tests
   show shape diffs only, **zero ERROR/MISSING nodes** (regen with `-u` at full rollout).
2. Fan out to the 4 object helpers (`_object_with_id`, `_object_without_id`,
   `_extension_with_id`, `_extension_without_id`) + `codeunit`/`enum`/`controladdin`/
   `interface` declarations.
3. Section bodies (`_named_section` + inline section bodies).
4. Field/action/control/enum-value bodies.
5. Routines: `statement_block` for procedure/trigger.
6. Update queries (highlights/locals/tags/indents/folds) if they reference the old
   flat shape; add example textobject query for downstream Helix users.
7. Full validation gate + `tree-sitter test -u`; re-snapshot.

## Implementation result (2026-06-17)

All body-bearing constructs now expose a `body` field. Body node types created:

| Node | Content | Used by |
|------|---------|---------|
| `object_body` | `_body_element` | objects, extensions, codeunit, enum, pagecustomization, fields/keys/fieldgroups + field/key/fieldgroup declarations, enum values, part/systempart/usercontrol, modify, page_field, report_column/dataitem-children, query_column/filter, xmlport_attribute, view_definition, requestpage, rendering_layout, type_declaration, split-field bodies |
| `controladdin_body` | `_body_element` + interface_procedure + preproc | controladdin |
| `interface_body` | `_body_element` + interface_procedure | interface |
| `fields_body` / `keys_body` / `fieldgroups_body` | section choices | table internals |
| `labels_body` | label declarations | labels |
| `layout_body` | `_layout_element` | layout, area, addfirst/last/after/before layout mods |
| `layout_container_body` | mixed layout/body/preproc | group/repeater/cuegroup/fixed/grid |
| `action_body` | `_action_element` | actions, action area, action mods |
| `action_group_body` | action + body | action group |
| `views_body` / `views_mod_body` | view defs + mods | views |
| `dataset_body` / `dataset_mod_body` | dataitems/columns/mods | report dataset |
| `report_body` | `_report_body_element` | report dataitem |
| `rendering_body` | rendering layouts | rendering |
| `analysisviews_body` | analysisview decls | analysisviews |
| `elements_body` / `query_body` | query dataitems / `_query_body_element` | query |
| `schema_body` / `xmlport_body` | xmlport elements | xmlport |
| `assembly_body` / `dotnet_body` | assembly/type decls | dotnet |
| `code_block` (existing) | statements; begin/end inside | procedure/trigger via `body:` field |

**Decisions made during rollout:**
- Empty bodies cannot carry a named node (tree-sitter forbids empty-matching rules);
  used `optional(field('body', $.<x>_body))` + `repeat1`. Empty `{ }` → no body node.
- `code_block` keeps `begin`/`end` inside (it is reused as a nested statement block);
  exposed via `field('body', $.code_block)` rather than a new content-only node. This
  is the only construct where `.inside` includes its delimiters (Rust `block` model).
- One new GLR conflict required: `[$.layout_body]` — `area_section` (and layout mods)
  may close with a `#if`-led `preproc_split_brace_close`, so GLR must choose between
  extending `layout_body` and opening the split brace.
- Preproc *branch* repeats (e.g. `preproc_conditional_*`, `preproc_split_brace_close`,
  source_file, var_section) were intentionally NOT wrapped — they are not construct
  bodies.

**Validation:**
- `tree-sitter generate` — clean, only the documented `[$.layout_body]` conflict.
- `tree-sitter test` — 1451/1451 pass after `-u`; 0 ERROR/MISSING nodes.
- `./parse-al-parallel.sh ./BC.History/ .` — **15,358 / 15,358, 0 errors (100%)**.
- No new orphaned/duplicate rules (the 2 pre-existing orphans `break_keyword` /
  `chartpart_keyword` are unrelated).
- `queries/textobjects.scm` added (Helix/nvim) — compiles and captures
  `@class.inside`, `@function.inside`, generic `@block.inside` correctly.

## Validation commands

```bash
tree-sitter generate           # watch for conflict warnings
tree-sitter parse sample.al    # inspect body node shape
./validate-grammar.sh --full
./parse-al-parallel.sh ./BC.History/ .   # must stay 0 errors
```
