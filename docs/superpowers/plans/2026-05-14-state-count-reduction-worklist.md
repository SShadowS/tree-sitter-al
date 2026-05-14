# Parser State-Count Reduction — Worklist

**Goal:** reduce STATE_COUNT and parser.c size, **zero behavior change** (1437 corpus tests + 15358 production files, 0 errors).

**Baseline after first pass (commit `200b1e6`):** STATE_COUNT 15525, parser.c 33.31 MiB, SYMBOL_COUNT 803.
First pass landed: removed 3 unnecessary conflicts + extracted `_preproc_branch_body` (complete-unit hidden rule). Cut 18290→15525 (-15%).

## Stats Record

Measure with: `grep -E '#define (STATE_COUNT|LARGE_STATE_COUNT|SYMBOL_COUNT)' src/parser.c`, `ls -l src/parser.c`, `tree-sitter test`, `./parse-al-parallel.sh ./BC.History/ .`

| Checkpoint | STATE_COUNT | LARGE_STATE | SYMBOL_COUNT | parser.c bytes | parser.c MiB | grammar.js lines | conflicts | tests | BC.History errors |
|------------|------------:|------------:|-------------:|---------------:|-------------:|-----------------:|----------:|------:|------------------:|
| **Pre** (orig, pre-`200b1e6`) | 18290 | — | 802 | 40,778,685 | 38.89 | — | 56 | 1437/1437 | 0 |
| **After pass 1** (`200b1e6`, current) | 15525 | 5265 | 803 | 34,925,072 | 33.31 | 3767 | 53 | 1437/1437 | 0 |
| After #1 `_procedure_name_and_params` | 14851 | 5215 | 804 | 34,051,645 | 32.47 | 3766 | 53 | 1437/1437 | TBD |
| After #2 `_routine_regular_body` | 13791 | 5106 | 805 | 32,873,110 | 31.35 | 3759 | 53 | 1437/1437 | TBD |
| After #3 `_else_begin_block` | 12797 | 4727 | 806 | 30,411,455 | 29.00 | 3758 | 53 | 1437/1437 | TBD |
| After #4 `_preproc_split_then_begin_open` + `_preproc_end_guard` | 12373 | 4529 | 808 | 29,192,796 | 27.84 | 3760 | 53 | 1437/1437 | TBD |
| After #5 `inline` experiment | 12373 | 4529 | 808 | 29,192,796 | 27.84 | 3760 | 53 | 1437/1437 | — |
| ↳ #5 result: **REVERTED** — `inline` array *did* bypass the GLR conflict (Gemini correct), but ballooned STATE_COUNT +56 (DevGuide §7 warning confirmed). Net negative. | | | | | | | | | |
| After #6 `_expression_list` | 12293 | 4505 | 809 | 28,993,640 | 27.65 | 3760 | 53 | 1437/1437 | TBD |
| After #7 operator consolidation | 12293 | 4505 | 809 | 28,993,640 | 27.65 | 3760 | 53 | — | — |
| ↳ #7 result: **REVERTED** — `token(choice('and',...))` cut states (−210, would hit 12083) but broke `highlights.scm` (operator literals no longer matchable as `"and"` etc. node types). Breaks query ergonomics = behavior change. Operator consolidation is fundamentally incompatible with literal-operator queries. | | | | | | | | | |
| After #8 assignment de-dup | 12293 | 4505 | 809 | 28,993,640 | 27.65 | 3760 | 53 | — | — |
| ↳ #8 result: **REVERTED** — `assignment_statement` / `assignment_expression` are NOT structurally identical: the latter is `prec.right`, the former isn't. A shared `_assignment_body` can't carry per-parent associativity; moving `prec.right` outside the `seq` → unresolved conflict on chained assignment. Gemini's premise was wrong. | | | | | | | | | |
| After #9 `_then_branch` + `_else_branch` | 11878 | 4247 | 811 | 27,580,022 | 26.30 | 3744 | 53 | 1437/1437 | TBD |
| After #10 trivial inline cleanup | 11872 | 4244 | 809 | 27,551,493 | 26.28 | 3750 | 53 | 1437/1437 | 0 |

*(BC.History batched once at end of pass per plan; intermediate "TBD" rows were gated on the corpus tests only.)*

**Pass 2 delta (`200b1e6` → here):** STATE_COUNT −3653 (−23.5%) · parser.c −3.32 MiB (−11.2%). Landed: #1 #2 #3 #4 #6 #9 #10. Reverted: #5 (inline balloon), #7 (broke queries), #8 (associativity conflict).
**Cumulative (orig → here):** STATE_COUNT 18290 → 11872 (−35.1%) · parser.c 38.89 → 26.28 MiB (−32.4%).

**Pass 1 delta:** STATE_COUNT −2765 (−15.1%) · parser.c −5,853,613 bytes (−5.58 MiB, −14.4%) · conflicts −3 · zero behavior change.

**Hard lesson from first pass:** extracting a *partial prefix* into the `preproc_split_*` family (`_preproc_if_header`, `_preproc_var_begin`) causes "Unresolved conflict" at generate — GLR can't defer the reduction decision when a hidden rule ends mid-construct and is reachable via multiple sibling preproc rules. **Only complete-unit extraction (clear terminator) works as a plain hidden rule.**

This worklist synthesizes recommendations from GPT-5.5, GPT-5.5-pro, and Gemini-3-pro. Run **one candidate per commit**: edit → `tree-sitter generate` → check STATE_COUNT delta → `tree-sitter test` → revert if it conflicts or balloons. Batch BC.History run at the end of the pass.

---

## Ranked candidates

### 1. `_procedure_signature` extraction — HIGH impact, MED risk
**All 3 models agree.** `procedure`, `_procedure_header`, and `interface_procedure` each re-inline the signature `[modifier] procedure_keyword name ( params ) [return]`.

- Extract hidden `_procedure_signature` (modifier + keyword + name + params + optional return clause). Optionally also `_procedure_name_and_params` and `_procedure_return_clause`.
- Use in `procedure`, `interface_procedure`, and `_procedure_header` (`_procedure_header = repeat(attribute_item) + _procedure_signature`).
- **Do NOT make `procedure` reuse `_procedure_header` directly** — `_procedure_header` has `repeat($.attribute_item)` at front; that would pull preceding attributes under the procedure node = AST change.
- Why it should work: complete balanced unit ending after `)` + optional return — not a mid-construct prefix.
- Fallback if it conflicts: extract only `_procedure_name_and_params` (ends at hard `)`), safer but smaller.
- Bonus: likely lets us delete the 6 `procedure`/`_procedure_header` conflict entries — verify with generate.
- Est: 250–700 states, 0.5–1.8 MB.

### 2. `_routine_body` extraction — MED impact, LOW risk
**GPT-5.5 + GPT-5.5-pro agree.** `procedure`, `trigger_declaration`, `preproc_split_procedure` all repeat `optional(choice(var_section, preproc_conditional_var_block)) + code_block`.

- Extract hidden `_routine_body` = that body choice (optionally including `preproc_split_complete_body` as an alternative).
- Why it should work: complete unit — `code_block` terminates at `end`/split-end. Same shape as the successful `_preproc_branch_body`.
- Est: 100–300 states, 0.2–0.7 MB.

### 3. Complete-unit preproc block extraction — MED impact, LOW risk
**All 3 agree.** Extract the `end else begin … end ;` tail and the depth-`begin … end ;` block — both are complete units with clear terminators.

- `_else_begin_block` = `seq(else_keyword, kw('begin'), repeat($._statement), kw('end'), optional(';'))` — used in `preproc_split_code_block_end` (1104 states) and `preproc_split_if_then_begin` (669).
- Optionally `_preproc_begin_end_block` = `seq(kw('begin'), repeat($._statement), kw('end'), optional(';'))`, and refactor `_preproc_branch_body` to `optional(var_section) + _preproc_begin_end_block`.
- Keep these for preprocessor-depth `kw('begin')`/`kw('end')` only — do NOT touch normal `code_block` (would break `begin_keyword`/`end_keyword` external tokens).
- Est: 150–450 states.

### 4. Complete-unit split-if opening extraction — MED impact, LOW/MED risk
**GPT-5.5 + GPT-5.5-pro agree.** Extract the *complete* `#if … #endif` opening unit (ends at `#endif`, NOT at `then`).

- `_preproc_if_then_split_begin_block` = `seq(preproc_if, repeat($._statement), if_keyword, condition, then_keyword, preproc_split_begin, preproc_endif)` — used in `preproc_split_if_then_begin` + `preproc_split_if_begin_asymmetric`.
- `_preproc_end_guard` = `seq(preproc_if, kw('end'), optional(';'), preproc_endif)` — used in `preproc_split_if_begin_else`, `preproc_fragmented_else_tail`.
- Why it should work: reduction point is a completed `#if…#endif` unit, not the ambiguous `then`.
- Est: 150–500 states.

### 5. The `inline` array escape hatch for partial prefixes — UNKNOWN impact, MED risk
**Gemini's key unique insight.** Rules in the `inline:` array are macro-substituted *before* the LR automaton is built — no reduction decision is ever made for them, so they bypass the GLR deferral problem that killed first-pass steps 3/4/5.

- Could rescue `_preproc_if_header` / `_preproc_var_begin` extraction: define them as hidden rules AND add to `inline: $ => [...]`.
- **Caveat (DevGuide §7):** `inline` can *balloon* STATE_COUNT instead of shrinking it — it duplicates the definition into every call site. Must measure STATE_COUNT before/after; keep only if it drops or moves a few %.
- Treat as experimental: try on one rule, measure, revert if neutral/negative.

### 6. `_expression_list` extraction — LOW/MED impact, MED risk
**GPT-5.5 + GPT-5.5-pro agree.** `argument_list`, `list_literal`, `preproc_split_call_statement` all repeat `expr (, expr)*`.

- `_expression_list` = `seq($._expression, repeat(seq(',', $._expression)))` — used in `argument_list`, `list_literal`, split-call shared args.
- Why it should work: complete comma-list bounded by hard delimiter `)` / `]`.
- **Caution:** `subscript_expression` first index has `field('index', …)` — needs a separate `_subscript_index_list` preserving the field, or skip subscripts.
- Est: 50–250 states.

### 7. Operator token consolidation — LOW/MED impact, **BEHAVIOR-CHANGE RISK**
**All 3 mention it; models disagree on risk.** Expression operator rules use `choice('div','DIV','Div')` etc. — literal-string casing variants create branch states inside the highly-connected `_expression` graph.

- Replace with `kw()` / `token()` so the lexer absorbs casing.
- **DISAGREEMENT:** Gemini calls this "zero risk"; GPT-5.5 and GPT-5.5-pro flag it correctly — `kw('and')` is a case-insensitive regex that accepts spellings (`aNd`) the current 3-variant `choice` rejects. **This widens the accepted language = not strictly zero behavior change.**
- **Decision needed:** AL is case-insensitive, so accepting all casings is arguably *more correct* — but it's a behavior change. If acceptable: use `kw()`. If strict: use exact-alternation regexes matching only current spellings.
- Est: 20–200 states; parser.c/SYMBOL_COUNT benefit may exceed state benefit.

### 8. `assignment_statement` / `assignment_expression` de-duplication — MED impact, LOW risk
**Gemini's unique insight.** The two rules are structurally identical; both reachable from `_statement` (one direct, one via `_expression_statement`). Every assignment forks GLR into two identical paths resolved by the `[$.assignment_statement, $.assignment_expression]` conflict.

- Delete `assignment_statement`, remove the conflict entry, and `alias($.assignment_expression, $.assignment_statement)` inside `_statement` to preserve the AST node name.
- Verify corpus trees unchanged (alias keeps the node name; field layout must match).
- Est: removes a per-assignment GLR fork + conflict overhead.

### 9. `_then_branch` / `_else_branch` hidden helpers — LOW/MED impact, MED risk
`field('then_branch', choice(code_block, _statement))` etc. repeated across `if_statement`, `preproc_split_if_statement`, `preproc_split_if_else_statement`.

- Extract `_then_branch` / `_else_branch` complete-unit choices.
- **Caution:** coupled to dangling-else conflict (`[$.if_statement, $._if_statement_no_else]`). Do after safer wins, diff trees carefully.
- Est: 50–150 states.

### 10. Trivial inline cleanup — TINY impact, LOW risk
`_field_source: $ => $._expression` and similar single-alias wrappers → add to `inline` array. Measure; revert if neutral. Do last.

---

## Anti-candidates (do NOT do)

- **Don't** make `procedure` reuse `_procedure_header` directly (attributes AST change).
- **Don't** retry plain hidden-rule `_preproc_var_begin` / `_preproc_if_header` extraction — proven to conflict. (The `inline` array variant in #5 is the only way to revisit.)
- **Don't** collapse the binary-expression rules into one visible `binary_expression` — changes AST shape unless every alt is aliased back, and then the win shrinks.
- **Don't** restructure to `_primary_expression`/`_postfix_expression` tiers this pass — high risk of rejecting currently-accepted constructs like `(a+b).Member`. Only behind a full parse-tree diff harness.
- **Don't** expect `supertypes` to reduce parser.c — helps query ergonomics, not LR state count.

## Suggested execution order

1. `_procedure_signature` (#1)
2. `_routine_body` (#2)
3. `_else_begin_block` + preproc complete-unit blocks (#3)
4. split-if opening units (#4)
5. `assignment_statement` de-dup (#8)
6. `_expression_list` (#6)
7. operator consolidation (#7) — *after deciding the casing question*
8. `inline` array experiment for partial prefixes (#5)
9. `_then_branch`/`_else_branch` (#9)
10. trivial inline cleanup (#10)

Per candidate, record: STATE_COUNT, SYMBOL_COUNT, parser.c size, offender report delta, corpus result, BC.History error count.

## Open question for the user

Candidate #7 (operator token consolidation): is widening accepted keyword casing (AL is case-insensitive anyway) acceptable, or must this pass be strict zero-change? This determines whether #7 uses `kw()` or exact-alternation regexes.
