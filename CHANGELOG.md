# Changelog

All notable changes to `tree-sitter-al` are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); the project
uses [Semantic Versioning](https://semver.org/) where the parse-tree shape is the
public API — a change to node structure or field names is a **major** bump.

## [Unreleased]

### Changed

- **Every statement body and branch field now holds exactly one node instead of
  the statement plus its `;`.** `_statement` is a hidden rule that expands to
  `<statement> optional(';')`, so any `field(name, $._statement)` labelled the
  terminator as well. For `while i > 0 do i := 2;` a consumer calling
  `children_by_field_name('body')` received `[assignment_statement, ';']` — two
  nodes for one body, with `multiple: true`. The `;` was never *inside* the
  statement node; it was a loose sibling that inherited the field. All 14
  affected fields are now `multiple: false` over a single named node:
  `case_branch.body`, `for_statement.body`, `foreach_statement.body`,
  `while_statement.body`, `with_statement.body`,
  `if_statement.then_branch`, `if_statement.else_branch`,
  `preproc_guarded_statement.then_branch`, `preproc_split_case_branch.body`,
  `preproc_split_case_extended.body`,
  `preproc_split_if_statement.{then,else}_branch` and
  `preproc_split_if_else_statement.{then,else}_branch`.
  (`preproc_split_if_else_statement.then_branch` stays `multiple: true` for an
  unrelated and legitimate reason — that rule has one `then_branch` per
  `#if`/`#elif`/`#else` header — but it too no longer carries a `;`.) This
  makes the 14 consistent with `case_else_branch.body`, which was given the
  single-node shape earlier in this release for the textobject queries
  (issue #19); until now one construct honoured that invariant and fourteen
  siblings contradicted it. Implemented by splitting `_statement` into
  `_statement_inner` plus its terminator and fielding the inner statement at
  each site. **No parse tree changes** — this only removes a field label from a
  `;` that was already present, all 15,358 BC.History trees are byte-identical,
  and highlight/tag/textobject capture counts are unchanged to the site.

- **Seven fields that name a dotted reference no longer hand you the `.`
  separators.** `field('reference', $._namespaced_or_simple_ref)` wrapped the
  whole dotted name in a single `field()` call, so every separator inherited
  the field. On `Record System.Reflection.Field`, a consumer calling
  `children_by_field_name('reference')` received five nodes —
  `[System, '.', Reflection, '.', Field]` — and had to filter punctuation back
  out. It now receives the three name parts only. Affected:
  `record_type.reference`, `dotnet_type.reference`,
  `object_reference_type.reference`, `simple_table_relation.table`,
  `report_dataitem.table_name`, `query_dataitem.table_name` and
  `tabledata_permission.table_name`. `tabledata_permission.table_name`
  deliberately still admits the anonymous `*` — in `Permissions = tabledata *
  = RIMD` the wildcard *is* the table name, the same way an `operator` field's
  token is its value. **No parse tree changes**: this only removes a field
  label from punctuation that was already there, and all 15,358 BC.History
  trees stay byte-identical. Highlighting improves as a side effect: queries
  matching `reference:`/`table_name:` previously captured only the *first*
  segment of a namespaced name, so `Microsoft.Foundation.UOM."Unit of Measure
  Management"` had one `@type` site and now has four (0 capture sites lost,
  +82 gained across a 1,500-file sample). Implemented with a new
  `namespacedRefFielded()` helper in `grammar.js` plus one hidden variant per
  distinct field name; costs +1.4% parser states.

- **A negated `CalcFormula` is now one `aggregate_formula` node that includes
  its sign, instead of a loose `-` beside the formula.** `CalcFormula = -
  sum(...)` was built as `seq('-', $.aggregate_formula)` inside the *hidden*
  `_calc_formula_expression`, so the `-` landed as a direct child of
  `property` and inherited the `value` field:
  `children_by_field_name('value')` returned `['-', aggregate_formula]`, two
  nodes for one value. The optional sign now lives inside `aggregate_formula`
  itself, so the field holds exactly one node. **This moves trees** — the only
  tree movement in this change — extending the `aggregate_formula` node left
  to cover its sign: 103 node instances across 34 of 15,358 BC.History files.
  No node type is added, removed, or re-parented; a
  `negated_aggregate_formula` wrapper was deliberately *not* introduced,
  because a new node type risks an unhandled-variant failure in downstream
  consumers that switch exhaustively on node type.

- **Correction to two earlier entries in this release.** The `array_type.sizes`
  and `link_value.value` entries under *Fixed* below described those defects as
  affecting only the declared `node-types.json` surface and stated that the
  runtime field assignment "never produces that". **That is wrong, and the
  fixes were more valuable than recorded: both were reachable at runtime.**
  The claim was verified with `tree-sitter parse -c`, which cannot show field
  names on *anonymous* nodes at all — `additive_expression.operator` is a
  declared field over an anonymous `'+'`, and `-c` prints that `"+"` with no
  field either. Re-checked against the pre-fix parsers with a `TSTreeCursor`
  walk (the mechanism `children_by_field_name` actually uses),
  `array[10,20] of Integer` returned `sizes` = `[10, ',', 20]` and a dotted
  `DataItemLink` returned `value` = `[Parent, '.', "No."]`. The corrected
  shapes those entries describe, and the parse-tree evidence that no tree
  moved, are both unaffected. The sentences making the runtime claim have been
  amended in place.

- **Every keyword node now has the same shape: exactly one anonymous child,
  typed as the canonical lowercase spelling.**
  **This changes the anonymous layer of essentially every tree.** A named rule
  whose entire body is a single token collapses *into* that token, so the
  token's visibility decided the node's shape: `kw()` builds a
  `token(PATTERN)`, and tree-sitter renders anonymous *pattern* tokens as
  hidden `aux_sym_*` symbols (`.visible = false`), unlike anonymous *string*
  tokens such as `";"`, which are visible. The 84 keyword rules were split
  across four forms — 51 bare `kw()` (childless leaves), 18 `alias(kw(w), w)`,
  13 explicit case `choice()` (both with a visible anonymous child), and 2
  external tokens (childless). A consumer could not predict which shape a
  given keyword had, and `node-types.json` could not tell them: it lists
  anonymous children only when they sit inside a field, and none of these do,
  so all 84 looked childless there regardless of reality.
  Every grammar keyword rule is now `alias(kw('word'), 'word')`, or
  `kwCases('word', …)` for the 13 compound (CamelCase) keywords whose
  case-spelling whitelist is load-bearing and must not become a
  case-insensitive regex — `eNuM` is a legal AL variable name and is
  deliberately absent from `enum_keyword`'s list. `kwCases()` aliases each
  accepted spelling to the canonical lowercase form, so the child's type no
  longer depends on how the source spelled the keyword: `XmlPort` now yields
  `(xmlport_keyword "xmlport")` where it previously yielded
  `(xmlport_keyword "XmlPort")`. The node's own text is unchanged, so reading
  a keyword's text from the node itself — always the recommended approach —
  is unaffected.
  `node-types.json` **adds 50** anonymous types (`actions`, `analysisview`,
  `analysisviews`, `area`, `asserterror`, `column`, `cuegroup`, `customizes`,
  `dataitem`, `dataset`, `elements`, `entitlement`, `event`, `extends`,
  `fieldgroup`, `fieldgroups`, `fields`, `filter`, `fixed`, `grid`, `group`,
  `implements`, `interface`, `internal`, `key`, `keys`, `labels`, `layout`,
  `local`, `namespace`, `page`, `part`, `procedure`, `profile`, `protected`,
  `query`, `rendering`, `repeater`, `report`, `requestpage`, `schema`,
  `systempart`, `table`, `temporary`, `trigger`, `usercontrol`, `using`,
  `var`, `view`, `views`) and **removes 57** — every non-canonical case
  spelling of the 13 compound keywords (`CODEUNIT`, `CodeUnit`, `Codeunit`,
  `codeUnit`, `COdeunit`, `XMLPort`, `XmlPort`, `Enum`, `eNum`,
  `PermissionSet`, `ControlAddIn`, and so on), which now all collapse to their
  canonical lowercase type. **No named node type is added, removed, or
  moved**, and all 15,358 BC.History parse trees remain byte-identical at the
  named level. 50 named entries do change in place, all of them keyword rules:
  `{"type":"x_keyword","named":true}` becomes
  `{"type":"x_keyword","named":true,"fields":{}}`. If you detect a leaf node by
  the *absence* of a `fields` key rather than by child count, those 50 now read
  as non-leaf. The 2 external tokens (`begin_keyword`, `end_keyword`) cannot
  take a child and stay childless leaves. `_tabledata_keyword` is unchanged:
  it is a hidden token helper, not a keyword node.

- **`begin` and `end` inside a `#if` block are now `begin_keyword` /
  `end_keyword` nodes. Until now they were in no node at all.**
  **This changes the parse tree** for every `#if`-wrapped `begin … end` in the
  corpus. The scanner declined `BEGIN_KEYWORD`/`END_KEYWORD` whenever the
  `#if` depth counter was above zero and handed the text to an anonymous
  `kw('begin')`/`kw('end')` — but `kw()` builds a `token(PATTERN)`, and
  tree-sitter renders anonymous *pattern* tokens as hidden `aux_sym_*` symbols
  (`.visible = false`), unlike anonymous *string* tokens such as `";"`, which
  are visible. So the keyword was lexed and then dropped: `code_block` spanned
  the text while neither a named nor an anonymous child covered `begin` or
  `end`. The CST was not lossless over the source, and both keywords were
  unhighlightable inside every `#if` block — `queries/highlights.scm` matched
  nothing there. Present since before 3.3.0.
  The depth > 0 path now reads the keyword once, calls `mark_end`, then lets
  the split lookahead choose between `PREPROC_SPLIT_BEGIN` and `BEGIN_KEYWORD`
  within a single scan (a scan that returns false discards its advances and is
  not re-entered at the same position, so the two cannot be separate blocks).
  `PREPROC_SPLIT_BEGIN`/`PREPROC_SPLIT_END` keep first refusal at depth > 0,
  so no existing split construct changes shape.
  All 17 `kw('begin')`/`kw('end')` sites in `grammar.js` are gone: begin/end
  are now scanner-exclusive at every depth, the same way `#if`/`#endif` became
  scanner-exclusive in 3.2.0, leaving no scanner/literal pair for GLR to fork
  on. Measured against the 15,358-file BC.History corpus: 742 files change
  shape, adding 6,239 `begin_keyword` and 6,476 `end_keyword` nodes; **no node
  of any type is removed or moved anywhere in the corpus**. `node-types.json`
  gains `begin_keyword`/`end_keyword` as possible children of seven
  `preproc_split_*` rules and loses nothing — the removed `kw()` tokens were
  hidden, so they were never in the anonymous layer to begin with. Cost:
  `STATE_COUNT` 11,796 → 12,293, `parser.c` 23.3 → 24.8 MB.

- **`case … else` bodies now parse into a single `statement_block` node
  instead of a flat, individually-fielded run of statements.**
  **This changes the parse tree** for every `case … else` branch whose body
  is a bare statement list (one or more statements not already wrapped in
  `begin/end`) — it is the only change in this release that moves parse trees
  *at scale*, and consumers that walk `case_else_branch.body` must update.
  For the release as a whole: this change moves 757 of the 15,358 BC.History
  files, the `exit` fix below moves exactly one
  (`Sales/Document/SalesLineReserve.Codeunit.al`, the file that bullet cites),
  and the two declared-type corrections (`array_type.sizes`,
  `link_value.value`) move none.
  `case_else_branch` used `field('body', repeat($._statement))`, which fields
  *each* statement in the repeat individually, so `body` was `multiple: true`
  — the one scoped construct not honouring the single-node `body` invariant
  every other construct (and the textobject queries, issue #19) rely on.
  `repeat_statement` already wraps its repeat in `$.statement_block`;
  `case_else_branch` now does the same, matching `if_statement.then_branch`
  and friends: `body: (statement_block ...)` instead of one or more
  `body: (...)` siblings. An `else` immediately followed by `end` with no
  statements at all is unaffected — `body` is simply absent, exactly as
  before. Measured against the 15,358-file BC.History corpus: 757 files
  change shape, adding 1,316 `statement_block` nodes; no node type other
  than `statement_block` is added or removed anywhere in the corpus, and
  the `case_branch` count is identical (22,047 before and after). Guarded by
  a new row in `tools/check-field-types.py`.

- **A single-entry `DataItemLink` / `RunPageLink` / `SubPageLink` /
  `ColumnFilter` now parses as `link_value_list` → `link_value`, the same as a
  comma-separated one. Until now it did not reach `link_value` at all.** One
  entry is still a complete `A = B` expression, so
  `property_expression` → `comparison_expression` parsed it too; the tie
  survived to a GLR ambiguity, where static precedence does not apply, and the
  arbitrary tiebreak handed every single-entry site to `property_expression`.
  Two-or-more entries were never ambiguous — the comma rules
  `property_expression` out — so `link_value` only ever modelled the
  multi-entry case. A query written against `link_value` to find link
  relationships therefore missed the single-entry form, which is the majority
  shape for `DataItemLink` (342 of 603 sites in BC.History) and 100% of
  `ColumnFilter`.

  Before, for `DataItemLink = "Customer No." = Cust."No.";`:
  ```
  value: (property_expression
    (comparison_expression
      left: (quoted_identifier)          ; "Customer No."
      operator: (comparison_operator)    ; =
      right: (member_expression
        object: (identifier)             ; Cust
        member: (quoted_identifier))))   ; "No."
  ```
  After — identical to what two entries have always produced:
  ```
  value: (link_value_list
    (link_value
      field: (quoted_identifier)         ; "Customer No."
      value: (identifier)                ; Cust
      value: (quoted_identifier)))       ; "No."
  ```
  The `field(…)` / `const(…)` / `filter(…)` / `upperlimit(…)` forms move the
  same way: the `call_expression` + `argument_list` wrapper collapses into
  `link_value`'s own `value` field (and `filter_keyword` / `filter_value` for
  the filter form), matching the multi-entry shape exactly.

  **Scope.** Only the structured right-hand sides — `field()`, `const()`,
  `filter()`, `upperlimit()` and the dotted `DataItem.Field` reference — are
  routed this way. The *bare* form (`Prop = A = B` with a plain identifier or
  quoted identifier on the right) is deliberately left as it was: in
  production that shape is never a link, it is `Implementation` /
  `DefaultImplementation` / `UnknownValueImplementation` syntax or an ordinary
  boolean property expression such as `Visible = HideActions = false`, and
  routing it through `link_value` would have mislabelled 425 such sites.
  Note that this carve-out is an **empirical** guarantee over BC.History, not a
  structural one: nothing in the grammar prevents a hand-written
  `Enabled = X = field(Y)` from being labelled `link_value`. No such
  construct is semantically legal AL, and none occurs in the 15,358-file
  corpus, but the grammar does not enforce it.

  Across all 15,358 BC.History files this moves 880 files and exactly 1,677
  property sites — 873 `RunPageLink`, 384 `SubPageLink`, 342 `DataItemLink`,
  47 `DataItemTableFilter`, 16 `LinkFields`, 15 `ColumnFilter`, which is
  every remaining single-entry site of those properties. A node-instance
  set-difference (identity = node type + exact byte range) over all 15,358
  trees shows the delta is closed: `+1,677 link_value_list`,
  `+1,677 link_value`, `+20 filter_keyword`, `+16 filter_value` against
  `-1,677 property_expression`, `-1,677 comparison_expression`,
  `-1,677 comparison_operator`, `-1,529 call_expression`/`argument_list`/
  `identifier`, `-152 member_expression`, `-2 range_expression`. No node of
  any other type is added or removed. The `-1,529` is `1,525 + 4`: 1,525
  non-dotted structured sites each shed one `call_expression` wrapper, and 4
  nested `field(filter(…))` sites shed a second — the same 4 that make
  `+20 filter_keyword` exceed `+16 filter_value`. `node-types.json` is
  unchanged — the declared shapes already covered both readings; only which
  input reaches `link_value` changed.

  **Highlighting.** Because the `field`/`const`/`upperlimit` keyword inside
  `link_value` is a hidden token rather than a named `identifier` inside a
  `call_expression`, moved sites would otherwise have lost their
  `@function.call`, `@operator` and `@variable` captures. `queries/highlights.scm`
  gains four `link_value` rules covering all **6,983** link sites in the corpus
  — the 1,677 that moved and the 5,306 comma-separated ones, which never had
  these captures either: `@property` on the target field, `@operator` on the
  inner `=`, `@variable` on the dotted form's dataitem name, and `@property` on
  the source field. Literal arguments such as `const(0)` keep their own literal
  highlighting. The one capture that cannot be restored is `@function.call` on
  the `field`/`const`/`upperlimit` token itself: it is a hidden token and no
  query can match it. `queries/tags.scm` and `queries/locals.scm` are
  *improved* by the same mechanism — they no longer emit a spurious
  `reference.call` tag and `local.reference` named `field` for `field(Code)`,
  which were never real call sites.

### Fixed

- **`i := 1` and `i += 2` produced byte-identical trees; the assignment operator
  is now a node.** `_assignment_operator` was a *hidden* rule over a single
  token, so `field('operator', …)` on `assignment_statement` and
  `assignment_expression` had nothing visible to attach to and the field was
  dropped from `node-types.json` altogether — both types declared only `left`
  and `right`. Unlike a mislabelled field this had no text fallback either: the
  operator bytes belonged to **no node at all**, so a consumer could not recover
  the operator by reading source ranges. Any dataflow analysis read every
  compound assignment as a plain one. Renaming the rule to `assignment_operator`
  makes it visible; `operator` now appears on both types and carries the
  operator text.
  - **`queries/highlights.scm` could never highlight an assignment.** Its
    `":=" @operator` pattern matches the anonymous literal `':='`, which only
    `for_statement` uses — the assignment operator is a *different*, atomic
    token. Measured on a file with three assignments and one `for`: the shipped
    pattern captured **1** site, the for-statement one. It now also captures
    `(assignment_operator)`, taking that file from 1 to 4, and covers `+=`,
    `-=`, `*=` and `/=`, which no pattern matched before.
  - The `token()` wrapper is load-bearing and stays: it is what keeps this token
    distinct from `for_statement`'s literal `':='`. Dropping it to mirror
    `comparison_operator`'s shape makes the two collide and the grammar no
    longer generates.
  - **243,044 `assignment_operator` nodes gained across 8,559 of 15,358 files,
    nothing else changed** — no other node type, and no node instance removed.
    Corroborated against the raw text: 241,368 literal `:=` in 8,563 files, the
    surplus being the compound operators and the shortfall the `for` statements.
  - `STATE_COUNT` unchanged at 14,059 — this renames a rule rather than adding
    one.
  - `is_expression.operator` and `as_expression.operator` declare the same field
    over hidden tokens and are deliberately untouched: their node *types* already
    encode the operator, so nothing is recoverable that is not already there.

- **Six fields that wrapped a bare `kw()` were silently empty; they now carry a
  named keyword node.** `field('x', kw('word'))` declares a field over an
  anonymous *pattern* token, and tree-sitter renders those as hidden `aux_sym_*`
  symbols — the bytes are consumed and the field disappears. (An anonymous
  *string* token such as `";"` is visible; a pattern one is not.) Routing each
  alternative through a named `alias(kw('word'), 'word')` rule, the same shape as
  the 82 existing `*_keyword` rules, is what makes the field reachable.
  **29,770 node instances gained across 5,212 of 15,358 BC.History files, and
  none lost.** Three distinct manifestations:
  - **Field present but `None` on some branches.** `object_reference_type.object_type`
    already routed eight of its ten alternatives through named rules; only
    `testpage` and `testrequestpage` were bare, so `Page X` carried the field and
    `TestPage X` did not. 17,440 sites. `interface_declaration.access_value` had
    the same 2-of-3 shape (`internal_keyword` worked, `kw('public')` did not).
  - **Field DECLARED but absent on every real instance — the misleading case.**
    `area_section.type` and `action_area_section.type` end their alternative lists
    with `$.identifier` as future-proofing. That fallback kept the field alive in
    `node-types.json` with type `['identifier']` alone, so a consumer reading the
    schema was told the field exists and then got `None` for `area(content)` and
    every other real page, because no real page takes the fallback branch. The
    schema was *wrong*, not merely incomplete. Both now declare all their keyword
    types; the `$.identifier` fallbacks are deliberate and stay.
  - **Field absent entirely.** `xmlport_element.element_type` and
    `xmlport_attribute.attribute_type` have no fallback, so with every alternative
    bare the field never appeared in `node-types.json` at all — both types exposed
    only `['body', 'name', 'source']`.
  - 23 new `*_keyword` rules (82 → 105). `processing`, `prompting` and
    `systemactions` each appear in two of the sites and share one rule.
    Deliberately **not** `kwCases()`: that rule governs narrowing a keyword *from*
    an explicit spelling whitelist, whereas these alternatives were already bare
    `kw()` and already case-insensitive, so the alias changes visibility only and
    cannot claim a spelling that was not already being claimed.
  - **312 corpus fixtures across 149 files had been written against the trees
    where the keyword was invisible** and were updated. The update is provably
    inert beyond this change: 445 lines added, **0 removed**, and every added line
    is a `*_keyword` node.
  - Cost: `STATE_COUNT` 14,036 → 14,059 (+0.2%).

- **A `begin`/`end` pair separated from its block by a `#if` boundary is no longer
  lost.** Three shapes, all silent — zero ERROR nodes, stable tree hash, corpus
  green, `parse-al-parallel.sh` reporting 100%. In each, `begin` fell back to a
  bare `identifier`, `end;` reparsed as a `call_statement` (a call to a function
  named `end`), and **no `code_block` was produced at all**, so the bracketed
  statements became siblings of the `begin` instead of its children. Any consumer
  reading control flow got a different program.
  - **A complete block inside one branch** — `#if C … #else begin A(); end; #endif`.
    Nothing is split here, which is the clearest proof the cause was a grammar gap
    rather than split detection: `preproc_conditional_statement`'s branches were
    `repeat($._statement)`, and `code_block` is not a `_statement`, so a branch
    could not hold the block that the enclosing `case_else_branch` accepts
    directly. Branch content is now `_preproc_branch_statement`, a statement or a
    complete `code_block`.
  - **A block bracketing a whole conditional** — `#if C begin A(); #endif B();
    #if C end; #endif`. New rule `preproc_split_code_block_over_endif`, the
    sibling of `preproc_fragmented_else_tail` for when a statement follows the
    `begin`, so `PREPROC_SPLIT_BEGIN`'s lookahead declines and a plain
    `begin_keyword` arrives instead.
  - **`end else begin` inside a conditional with the else block's `end;` outside
    it** — `if C then begin A(); #if D end else begin B(); #endif end;`. New rule
    `preproc_split_else_begin_over_endif` in `code_block`'s ending choice;
    `preproc_split_code_block_end` declines because its `_preproc_end_branch`
    requires the else block to close inside the same conditional.
  - **Trees move, at exactly three files** of BC.History's 15,358 — the three real
    sites, one per shape. Enumerated by node-instance set difference (type + byte
    range): 13 instances removed, 12 added, every one an intended repair. Seven
    stray `identifier` nodes become `begin_keyword`/`else_keyword`/`end_keyword`,
    two misapplied `preproc_conditional_statement` wrappers and two `call_statement`
    misreads are replaced by the correct block or split node. No other file changes.
  - **Two shipped corpus fixtures asserted the broken tree** and were updated:
    "Case statement with preprocessor conditional in else branch" and "Nested case
    with multiple preprocessor conditions" both pinned `(identifier)` plus a loose
    `(call_statement)` where a `code_block` belongs. Error-count assertions are
    worthless for this class; the new fixtures pin node structure.
  - `code_block` was deliberately **not** added to `_statement_inner`, which would
    have been the more general statement of the same truth — alc 18.0.37.11445 does
    accept a bare `begin … end;` compound statement anywhere (verified). That makes
    every `while … do begin`, `if … then begin` and `for … do begin` ambiguous
    between "loop/branch body" and "standalone block", forcing a dangling-block
    conflict on each host and a GLR fork on every `begin` in the corpus. A bare
    compound statement outside a preprocessor branch therefore still produces an
    ERROR; that is a separate, pre-existing gap, recorded rather than fixed here.
  - Cost: `STATE_COUNT` 12,604 → 14,036 (+11.4%), `src/parser.c` 27.5 MB → 32.7 MB.
  - `call_statement` now occurs **nowhere** in BC.History. Both of its former
    instances were this defect; the rule itself stays valid for parenless calls
    (`Initialize;`) and is exercised by the corpus.

- **A partially matched keyword no longer eats the identifier behind it.** The
  scanner tried `begin`, then `end`, then `continue`, then `property_name`, each
  with its own read. `read_keyword_ci` stops on the first mismatching character
  with the matching prefix **already consumed**, and a scan cannot give
  characters back, so the next branch started in the middle of an identifier.
  Two consequences:
  - `b1 = 1;` was an ERROR where `x7 = 7;` in the identical position was a
    property. Parse states 20 and 22 — an object body just after a procedure
    header, of which an interface procedure with a return type is the common
    shape — offer `property_name` and `begin_keyword` together; the failed
    `begin` match ate the `b`, and `PROPERTY_NAME`'s identifier-*start* check
    then saw the `1` and declined. Every strict prefix of `begin` was affected
    (`b1`, `be2`, `beg3`, `begi4`, `begin5`) while `beginx` worked, because `x`
    is a legal identifier start — which is what made the shape look arbitrary.
  - a leading `b` was absorbed into a following `VAR_ATTRIBUTE_OPEN`, producing
    a two-column `[` token whose text was `b[`, with the identifier byte in no
    node at all.

  The four identifier-initial tokens now share **one** read
  (`read_identifier_word`) — the rule `peek_directive_ci_skip_extras` already
  applied to directive words — and `VAR_ATTRIBUTE_OPEN`, the only `[`-initial
  token, is dispatched ahead of them. This also retires the documented
  constraint that no parse state may offer `PREPROC_SPLIT_BEGIN` and
  `END_KEYWORD` at the same position: one read makes it moot.

- **The scanner and the grammar now agree on what counts as a directive.**
  `pragma`, `preproc_region`, `preproc_endregion`, `preproc_define` and
  `preproc_undef` are `(?i)#[ \t]*NAME[^\n\r]*` regexes, and `preproc_else` and
  `preproc_elif` are `(?i)#[ \t]*else`/`elif`. None carries a trailing word
  boundary, so the parser accepts `#regionX Foo`, `#pragmaX …`, `#elseX` and
  `#elifX`. The scanner's split-construct lookahead classified directive words
  whole-word only, declined, and `PREPROC_SPLIT_END` was never emitted: with any
  of those four between an `end;` and its continuation, the `end;` degraded to
  `(call_statement (identifier))` and the branch shredded into loose
  identifiers. Each directive now carries the match mode of the rule that
  produces it — prefix for the regex-matched ones, whole word for `#endif`,
  which only the scanner's own `#` dispatch can produce, so `#endifX` is still
  (correctly) not an `#endif`. An over-long directive word is no longer rejected
  outright either: `#regionAAAAAAAAAAAAAA` is a region to the parser. The BOM is
  now stepped over too, and so is the vertical tab — `grammar.js` declares both
  as extras, so the parser skips either anywhere, and a BOM or a `` between a
  split `end;` and its `#else` had been dropping the token the same way a comment
  once did. `is_extra_space()` now enumerates all seven single-character extras
  explicitly (` `, `	`, `
`, `
`, ``, ``, U+FEFF): the first version of
  that comment claimed to cover "the single-character members" while listing six
  of the seven, and an adjective is not a specification. The bound is exactly
  those seven — U+0085, U+00A0, U+1680, U+2000, U+2028, U+2029, U+202F, U+205F
  and U+3000 are rejected by the *parser* as well, since tree-sitter's `\s` is
  not Unicode-aware here, so they are a different failure and out of scope.
  - **This aligns the scanner with the grammar, and the grammar is over-permissive
    relative to the compiler.** alc 18.0.37.11445 rejects `#regionX`, `#pragmaX`,
    `#elseX` and `#elifX` with `AL0621`; `#region Foo` compiles clean. The root
    cause is the missing trailing word boundary in the seven regexes at
    `grammar.js:3025,3030,3355,3357,3359,3382,3384`, and `DirectiveMatch`'s
    `whole_word` flag exists only to model that defect faithfully. Aligning the
    scanner was the right local call — it was the only tree-neutral option, and
    changing the grammar's token boundaries was out of this change's scope — but
    it means four of the fixtures pin trees for input the compiler rejects.
    **Tightening those regexes to require a word boundary is an open follow-up**;
    doing it would retire `whole_word` entirely and make prefix-vs-whole-word a
    non-question. This entry is not a claim that the directive surface is
    correct, only that the two halves of the parser no longer disagree about it.

- **`#iendif` is no longer silently accepted as `#endif`.** The `#` dispatch tried
  `if` and then, on failure, `endif`, with two separate matches that walk the
  lexer. The defence written into the comment — that the two words differ at
  their first character, so a failed `if` consumes nothing — is a statement
  about the two *candidates* and says nothing about the *input*. On `#iendif`
  the `if` attempt matched the `i` before failing on `e`, leaving it consumed;
  the `endif` attempt then read the remaining `endif` and **returned true**.
  Result: a `preproc_close` node spanning all seven bytes of `#iendif`, the
  `#if` depth counter decremented, `tree-sitter parse` exiting 0 with no ERROR
  node — for a directive the grammar accepts nowhere. `#ifendif` did the same
  through `if`'s whole-word check. `#xendif` was always an honest ERROR, because
  `x` matches no prefix of `if` and so consumed nothing; that contrast is the
  whole mechanism. The dispatch now reads the directive word once and compares
  it whole, so a partial candidate match can neither leak into the next
  comparison nor return true. `#elif` and `#else` also burned a character on the
  failed `endif` attempt, but harmlessly — the next statement is `return false`,
  and tree-sitter discards a failed scan's advances.
  - With this, **no code in `src/scanner.c` matches a keyword against the live
    lexer any more.** Every comparison — directive words, `begin`/`end`/
    `continue`, the split lookaheads — goes through one buffered `read_word_ci`.
    The walking matcher that made all three variants of this defect possible has
    been deleted rather than documented.

- **A supplementary-plane identifier is no longer lexed as `begin` on Windows.**
  `lexer->lookahead` is `int32_t` and `wint_t` is 16 bits under MSVC, so every
  `towlower(lexer->lookahead)` truncated a codepoint above U+FFFF to its low 16
  bits (MSVC warned C4244 on all five call sites). U+20062 — a CJK Extension B
  ideograph, and an ordinary identifier start under the grammar's
  `[\p{L}_][\p{L}\p{N}_]*` — has low bits `0x62`, so `<U+20062>egin: Integer;`
  matched `begin` and the variable declaration was swallowed into a
  `begin_keyword`. The same file parsed correctly on Linux, where `wint_t` is
  32 bits: the parser disagreed with itself across platforms. Keyword and
  directive comparison now goes through `keyword_byte()`, which lowercases
  ASCII and folds every other codepoint to a byte no keyword contains.

- **The `#if` depth counter no longer wraps at 256.** It was a `uint8_t`, so the
  256th simultaneously-open `#if` reset it to 0 and every `state->depth > 0`
  guard read genuine nesting as "not nested": a split construct whose own `#if`
  was the 256th lost its `PREPROC_SPLIT_*` token. Measured exactly — with 255
  enclosing `#if` blocks the split `end;` degraded to a `call_statement`; at 254
  and at 256 it did not. The deepest nesting across BC.History's 15,358 files is
  3, so no real AL came close. It is now a `uint32_t` (serialized as 4 bytes),
  which no file that fits in memory can reach, with a compile-time assertion so
  a revert fails the build rather than one deeply nested file.

  These are scanner-only. **No parse tree changes**: all 15,358 BC.History trees
  are byte-identical to the pre-change snapshot.

- **`#elif` after a preprocessor-split `end;` no longer degrades the block.**
  `#if COND / end; / #elif COND / … / #endif` produced a wrong tree: the `end;`
  became `(call_statement (identifier))` and the following branch shredded into
  loose `(identifier)` nodes, all flattened into `preproc_conditional_statement`
  instead of forming one `preproc_split_code_block_end`. The identical source
  with `#else` had parsed correctly since 3.3.1. alc accepts the `#elif` form,
  so this was a wrong tree for valid AL.
  - **Unlike the other misparses in this release, this one was not silent.** It
    left a `MISSING end_keyword`, `tree-sitter parse` exited non-zero, and
    `parse-al-parallel.sh` did count it — that script greps every `\tParse:`
    line, which quiet mode emits for MISSING as well as ERROR. The error gate
    caught it, which is why no such file was ever able to reach BC.History's
    100% clean run. An earlier note recorded it as producing "zero ERROR nodes",
    which is true but incomplete: it checked ERROR without checking MISSING.
  - Two layers had to change. The scanner's `PREPROC_SPLIT_END` lookahead target
    set gained `"elif"` alongside `"else"`/`"endif"`, so the token is emitted at
    all; and `preproc_split_code_block_end` gained `#elif` branches, without
    which the emitted token had no rule to land in.
  - The rule is now branch-symmetric. Every `#if`/`#elif`/`#else` branch is an
    alternative completion of the same block, so each independently contributes
    either a bare `end;` or the longer `end … else begin … end;` tail, via a new
    hidden `_preproc_end_branch`. That symmetry also repaired two `#else` shapes
    — see the next entry.
  - Factoring the branch into one shared hidden rule made the parser **smaller**:
    `STATE_COUNT` 12709 → 12604 (-105), `parser.c` 27,593,402 → 27,490,081 bytes
    (-101 KB). No `conflicts` entry was needed. `node-types.json` changed by
    exactly one entry, 4 lines — `preproc_elif` added to
    `preproc_split_code_block_end`'s children — with the anonymous layer
    untouched, and all 15,358 BC.History parse trees stayed byte-identical.

- **Two `#else` split-code-block shapes were also degrading, and are fixed by the
  same change.** These sit on the path 3.3.1 was believed to have left sound.
  That release hardened this path's *lookahead* — making it step over comments,
  and reaching its previously-unreachable `#endif` arm — but it did not touch
  which branch **arrangements** the rule accepts, and these two were never
  accepted by it at all. Both produced a wrong tree with a `MISSING end_keyword`,
  identical to the `#elif` case above:
  - **A bare `end;` in the *final* branch** — `#if COND / end; / #else / end; / #endif`.
  - **The tail in the *first* branch** — `#if COND / end else begin … end; / #else / end; / #endif`.

  Only one arrangement previously parsed: the bare `end;` first and the
  `end … else begin … end;` tail last. That asymmetry was the defect — nothing
  in AL requires the branches to be ordered that way, since each is an
  alternative completion of the same block. Making
  `preproc_split_code_block_end` branch-symmetric fixed `#elif` and both of
  these together. Found by measuring the `#else` analogue of every `#elif`
  variant before designing the fix, rather than assuming the `#else` path was
  sound. All five `#elif` shapes and both `#else` shapes are pinned in
  `test/corpus/preproc_split_code_block_end_elif_test.txt` — 7 fixtures.

- **`tools/tree-harness.sh` is 2-7x faster and can no longer report a clean run
  it did not earn.** Measured on BC.History (15,358 files, `NUM_THREADS=16`):
  `snapshot` 44.1s → 16.1s, a clean `verify` 24.6s → 11.2s, a 20-file delta
  30.9s → 15.3s, and a 757-file delta **2m56s → 22.3s**. The mismatch report was
  spending ~230ms per changed file on process creation — one `diff` spawn each —
  so it now runs a single `diff -r` over the changed trees; report output is
  byte-identical (`cmp -s` against the previous implementation at both delta
  sizes: 10,041 bytes / 20 headers and 422,909 bytes / 757 headers). `build_trees`
  no longer materialises 15,358 individual tree files, hashes them in a second
  pass and tars them in a third: `tree-sitter parse` already concatenates each
  chunk's trees, so that blob is kept as-is and the new `tools/tree_blob.py`
  splits and hashes it in-process. Tree boundaries and hashes are unchanged — a
  snapshot taken by either implementation has the same `manifest sha256`.
  Snapshots taken before this change still verify; their archive is read through
  a legacy path rather than being stranded.
  Every route to a false clean is now asserted shut, each demonstrated by
  deliberately provoking it: a chunk that returns no trees names the chunk,
  its `tree-sitter` exit status and the first lines of its output, and preserves
  them on disk (the old code's `|| true` plus `rm -f` destroyed the evidence, and
  its global count could be fooled by two chunks losing and gaining the same
  number); manifests that differ while no path disagrees on its hash now abort
  instead of printing "0 file(s) changed"; an extraction that yields nothing
  aborts; and an empty file list aborts. Two latent traps in the extraction are
  gone with the `tar` it replaced: an empty member list extracted the **entire**
  archive (confirmed: 280 of 280 members) and now extracts nothing, and a member
  missing from the archive aborted the whole extraction and now degrades to a
  note against that one file. Tooling only — no grammar, parser or query change.

- **`VAR_ATTRIBUTE_OPEN`'s remaining skips are no longer comment- and
  newline-blind — this completes the work 3.3.1 started.** 3.3.1 fixed the
  bracket-scan's comment-blindness and the name-list's quoted-name/`,`
  structure, but left four other hand-rolled whitespace loops in the same
  block untouched: the skip after the closing `]`, the inter-attribute skip
  in the chained-attribute loop, and the two name-list skips (before `:` and
  after `,`) — all comment-blind, and the two name-list skips newline-blind
  too since they only listed `' '`/`'\t'`. Six shapes each gave 3 ERROR nodes,
  identical before and after 3.3.1: a comment after the `]`, a comment inside
  the name list, a comment before the `:`, a newline after the `,`, a newline
  before the `:`, and `[InDataSet]` then `"My Var",` newline `Other:
  Boolean;` — the last of which means 3.3.1's quoted-name fix was **partial**:
  it made `"My Var", Other: Boolean;` work on one line but not across a
  newline, while the grammar itself already parses `Alpha,` newline `Beta:
  Boolean;` cleanly with no attribute present, so the scanner was internally
  inconsistent with its own grammar. All four skips now route through the
  `skip_whitespace_and_comments` helper 3.3.1 introduced, in both the main
  bracket-scan loop and the chained-attribute loop (`[A][B] Name: Type` with
  a comment between the two attributes is covered by a dedicated test).
  Every one of these skips runs after `mark_end` has pinned the token to the
  `[`, so all route through the non-marking form; none regress to
  `skip_whitespace`'s marking `advance(lexer, true)`, which would collapse
  the token to zero width. All six shapes produced ERROR nodes before this
  fix, so no currently-clean BC.History tree can depend on them — the harness
  reports 0 changed files.

- **Control-flow keywords and word operators are now genuinely
  case-insensitive.** AL is a fully case-insensitive language, but the Tier-1
  keyword rules and the word-operator rules spelled out exactly three casings
  (`'if'`, `'IF'`, `'If'`). Every other casing failed, and because `_statement`
  carries `optional(';')` the failure was **silent**:
  `iF x = 0 tHEN x := 1 eLSe x := 2;` compiles under alc, but parsed into a
  flat run of `(identifier)` and `(assignment_statement)` nodes with the entire
  if-structure gone and **zero ERROR or MISSING nodes** — a consumer had no way
  to detect that it had been handed the wrong tree. The 19 Tier-1 keywords
  (`if`, `then`, `else`, `case`, `of`, `for`, `foreach`, `while`, `do`,
  `repeat`, `until`, `exit`, `continue`, `break`, `with`, `asserterror`, `in`,
  `to`, `downto`), the word operators (`and`, `or`, `xor`, `not`, `div`, `mod`)
  and the preprocessor `not` now use the case-insensitive `kw()` regex form
  that most of the grammar already used.
  The **named** parse tree is unchanged: all 15,358 BC.History trees are
  byte-identical to the pre-change snapshot. The parser also got *smaller*
  (`STATE_COUNT` 11,879 → 11,796, `parser.c` 23.5 → 22.2 MB), since one regex
  token replaces three string literals per keyword.

  **Anonymous node types removed — action required for some queries.** Each
  keyword and word operator previously contributed one anonymous node type per
  spelled-out casing; it now contributes exactly one, lowercase, whatever the
  source casing. **48 anonymous node types are removed and none are added:**
  the 36 upper- and title-case Tier-1 keyword forms (`"IF"`, `"If"`, `"THEN"`,
  `"Then"`, … for all 18 of `if`, `then`, `else`, `case`, `of`, `for`,
  `foreach`, `while`, `do`, `repeat`, `until`, `exit`, `continue`, `break`,
  `with`, `in`, `to`, `downto`) and the 12 upper- and title-case operator forms
  (`"AND"`, `"And"`, `"OR"`, `"Or"`, `"XOR"`, `"Xor"`, `"NOT"`, `"Not"`,
  `"DIV"`, `"Div"`, `"MOD"`, `"Mod"`). **Every lowercase name is retained** —
  `"if"`, `"then"`, `"exit"`, `"and"`, `"div"` and the rest all still exist and
  now match every casing. A query referencing a lowercase name keeps working
  unchanged and gains coverage; a query referencing an uppercase or title-case
  name **fails to compile** with `Invalid node type` and must drop it.
  `queries/highlights.scm` is updated accordingly. `in` is additionally
  matchable via the named `(in_keyword)` node.

  For a consumer reading the full CST, the anonymous child under a keyword node
  is now normalised to lowercase: source `IF` yields `(if_keyword "if")` where
  it previously yielded `(if_keyword "IF")`. The node text is untouched — only
  the type name normalises — and the named tree is unaffected, which is why the
  harness reports no change. As an upper bound, 3,072 of 15,358 BC.History
  files (20%) contain a non-lowercase spelling of one of these words somewhere
  in the file; the true figure is lower, since that count also matches comments,
  string literals and identifiers such as `IfBlank`.
  - The `10` precedence on the Tier-1 keywords stays *outside* `kw()`, so it
    remains parse precedence. Moving it inside `token()` would make it
    lexical, where it outranks the prec-0 `integer` token in the keyword lexer
    and stops `Integer` from ever matching past `In` — silently demoting
    `basic_type` to `identifier`. Identifiers that merely begin with a keyword
    (`ifCondition`, `Then`, `NotFlag`, `Divisor`, `Order`, `Modify`) are
    unaffected and covered by a regression test.

- **`exit` followed by whitespace before its `(...)` no longer silently drops
  the return value.** `exit_statement` used `token.immediate('(')`, so any
  whitespace — a space, or the parenthesis on the next source line — split the
  statement into a bare `(exit_statement (exit_keyword))` plus a detached
  sibling `(parenthesized_expression ...)`. **No ERROR node.** alc accepts the
  whitespace freely; AL tokenization is whitespace-insensitive between tokens.
  Confirmed against real shipped Microsoft code, not just a synthetic case:
  `BaseApp/Source/Base Application/Sales/Document/SalesLineReserve.Codeunit.al`,
  `VerifyPickedQtyReservToInventory`, has `exit` with its parenthesised
  three-line boolean condition starting on the *next* source line — every
  release through v3.3.1 silently dropped that entire return condition from
  the parse tree with zero ERROR nodes. `'('` is now a plain literal, and
  `exit_statement` is a `choice` of two `prec`-differentiated alternatives
  (parenthesised form higher) rather than one `seq` with an optional trailing
  group, because `exit` followed by `(` is a genuine shift/reduce ambiguity —
  continue the exit vs. reduce and start a new parenthesized-expression
  statement — that a `prec` nested inside `optional()` does not resolve.
  - **Behaviour change worth calling out:** `exit (x + y) * 2;` now produces an
    ERROR node where it previously produced a *silent* wrong tree. This is the
    correct outcome, not a regression — alc rejects that form (`'end' expected`),
    and the unspaced `exit(x + y) * 2;` has always errored. The spaced and
    unspaced forms now agree with each other and with the compiler. Code that
    means to return the product must parenthesise it: `exit((x + y) * 2);`.

- **A call to a quoted-identifier procedure, e.g. `"My Proc"(42);`, no longer
  splits silently.** `call_expression`'s `function` field choice omitted
  `quoted_identifier`, even though the parenless `call_statement` already
  accepted it. With an argument, the call split into a bare
  `(quoted_identifier)` sibling followed by a detached
  `(parenthesized_expression (integer))` — **no ERROR node**. With no
  arguments, `"My Proc"();` produced a `(MISSING identifier)` inside the
  parenthesized expression. alc accepts both forms; `quoted_identifier` is
  now a valid `call_expression` function alongside `identifier`,
  `member_expression`, `qualified_enum_value`, `keyword_identifier`, and
  `subscript_expression`.

- **Parenthesized preprocessor conditions no longer produce an ERROR node.**
  `#if (FOO)` and `#if not (FOO and BAR)` both compile under alc, but
  `_preproc_expression` only accepted a bare `identifier` as an atom — the
  `(` became an `ERROR` node, the condition fell back to reading whatever
  identifier followed, and the trailing `)` leaked into the branch body as a
  detached expression statement. Added `preproc_parenthesized_expression`
  (`'(' _preproc_expression ')'`) as a new alternative in
  `_preproc_expression`, alongside `identifier`, `preproc_not_expression`,
  `preproc_or_expression`, and `preproc_and_expression`.

- **`#elif`/`#else` now tolerate any amount of horizontal whitespace after the
  `#`, not just zero or one space.** `preproc_elif`/`preproc_else` spelled out
  literal zero-space and one-space alternatives, while scanner-owned
  `#if`/`#endif` already accept `[ \t]*`. `#  elif BAR` (two spaces) and
  `#\telse` (a tab) are legal AL — alc accepts both — but were an ERROR.
  Replaced the literal-choice lists with `(?i)#[ \t]*elif` /
  `(?i)#[ \t]*else` regexes; `elif`/`else` carry no external-scanner token and
  touch no `#if`/`#endif` depth state, so this is a plain literal-vs-regex
  swap with no scanner interaction.

- **`node-types.json` no longer declares that `array_type.sizes` can contain a
  comma.** A multi-dimensional declaration like `array[10,20] of Integer`
  wrapped its whole comma-separated size list in one `field('sizes',
  seq($.integer, repeat(seq(',', $.integer))))`. That single `field()` call
  made the generated `node-types.json` record `sizes` as `multiple: true` with
  type set `[',', 'integer']` — declaring the anonymous `,` as a possible
  member of the field. The compiled parser produced that too: at runtime
  `children_by_field_name('sizes')` on `array[10,20] of Integer` returned
  `[10, ',', 20]`, the comma included. (An earlier revision of this entry
  claimed the runtime was unaffected, on the strength of `tree-sitter parse
  -c`; that tool cannot display field names on anonymous nodes, so it could
  not have shown the comma either way. Corrected after re-checking the pre-fix
  parser with a `TSTreeCursor` walk.) The parse-tree harness still shows 0 of
  15,358 BC.History production trees changed, because a field label is not
  part of the tree. It matters because typed bindings (Rust, TypeScript) and other
  tooling generate their `sizes` accessor type from `node-types.json`, not
  from a live parse, and would have exposed a `sizes` accessor typed to
  include a comma the fix removes. Each size dimension
  now carries its own `field('sizes', $.integer)`; the declared `sizes` type
  set is `['integer']` only, matching what the parser actually produces.
  Guarded by `tools/check-field-types.py`, run as part of
  `./validate-grammar.sh`.

- **`node-types.json` no longer declares that `link_value.value` can contain a
  `.`.** The `DataItem.FieldName` dotted reference form of `link_value`
  (used by `DataItemLink`, `SubPageLink`, etc.) wrapped both identifiers and
  the `.` between them in one `field('value', seq(id, '.', id))`. That single
  `field()` call made the generated `node-types.json` record `value` with
  type set including `.`. The compiled parser produced that too: at runtime
  `children_by_field_name('value')` on a dotted `DataItemLink` returned
  `[Parent, '.', "No."]`, the dot included. (As with `array_type.sizes` above,
  an earlier revision of this entry claimed the runtime was unaffected on the
  strength of `tree-sitter parse -c`, which cannot display field names on
  anonymous nodes; corrected after re-checking the pre-fix parser with a
  `TSTreeCursor` walk.) The parse-tree harness still shows 0 of 15,358
  BC.History production trees changed, because a field label is not part of
  the tree. Same class of bug as the `array_type.sizes` fix above, and it
  matters for the same reason: typed bindings and tooling generate their `value`
  accessor type from `node-types.json`, not from a live parse. Each
  identifier now carries its own `field('value', $._identifier_or_quoted)`;
  the declared `value` type set no longer includes `.`. Guarded by a new row
  in `tools/check-field-types.py`.

- **`validate-grammar.sh`'s Step 5 duplicate check now examines the whole
  grammar instead of almost nothing.** `tools/analyze_duplicates.py` only
  ever inspected rules matching `*_property` — 2 of them in the V2 grammar,
  where V1 had 291 — so the step always printed "no duplicates found" having
  checked 2 of grammar.js's 442 rule definitions. It could not have caught
  the very bug it exists to catch: `grammar.js`'s `rules: { ... }` is one
  JavaScript object literal, and a repeated key is valid syntax that
  JavaScript resolves by silently keeping the *last* value and discarding the
  rest. Task 10 (see "Removed" below) found exactly this — `empty_statement`
  defined twice, identically, in two different places in the file — by a
  human reading the file, because nothing else did. Repurposed the script to
  parse `rules: { ... }` well enough to recover every top-level `key: value`
  entry (a small hand-rolled scanner: comment/string/regex-aware
  bracket-depth counting, not a full JS parser) and report any key that
  appears more than once, distinguishing two cases that matter differently:
  an IDENTICAL duplicate (both definitions agree byte-for-byte — harmless in
  that the grammar behaves as written, but dead weight and a trap for whoever
  next edits only one copy) from a DIFFERING one (a live bug — the earlier
  definition is silently discarded, so the grammar does not do what it says).
  Both fail the check: an "identical, so it's harmless" duplicate is exactly
  the kind of thing that goes unnoticed and later bit-rots into a differing
  one. Verified by temporarily reintroducing both cases (an identical and a
  differing duplicate of the `integer` rule, plus a mid-file duplicate of the
  `identifier` rule to exercise the raw regex-literal handling) and
  confirming each is reported and fails the script, then reverting — no
  grammar change, `git status --short src/` stayed empty throughout.

- **`validate-grammar.sh`'s Step 8 grammar health check now fails when it has
  nothing to compare against, instead of reporting a pass.** `check_grammar_health.py
  --ci` exited 0 whenever `.grammar_baseline.json` was absent — the state of
  the repo before this fix — because `compare_to_baseline(None)` returns an
  empty `regressions` list, and an empty list read as "no regressions" instead
  of "nothing was checked." Step 8 then printed `✓ Health check passed`, so
  one of the script's eight steps was green because it had run zero
  comparisons. The health checker now treats a missing baseline as
  `STATUS: FAILED` and returns exit 1 under `--ci`; Step 8 reports a specific,
  actionable error ("Grammar health baseline missing... run --save-baseline")
  instead of the generic "regressions detected" message. `.grammar_baseline.json`
  is now tracked in git — it was previously neither tracked nor ignored, the
  same class of defect as `grammar_analysis.json` before it was gitignored
  above. A baseline that lives only on one machine cannot detect drift across
  commits, which is the entire point of the check; tracking it means a fresh
  clone always has one, so a missing baseline signals a broken checkout, not a
  routine first run, and failing loudly on it is safe rather than a nuisance.
  Self-seeding on first run was considered and rejected: it would silently
  bless whatever state happens to be on disk — possibly already regressed — as
  the new "good" baseline, with nobody the wiser.
  Making the exit code real also exposed that Step 8's own output capture was
  dead code: `HEALTH_OUTPUT=$(python3 tools/check_grammar_health.py --ci 2>&1)`
  is a bare assignment, and under `set -e` a non-zero exit from that command
  substitution aborted the whole script on that line, before `HEALTH_EXIT_CODE`
  was even read — skipping the new error message and every step after it.
  Rewritten as `cmd && VAR=0 || VAR=$?` so the step's own handling actually
  runs. (Steps 2, 4, 5, 5b and 5c capture their tool output the same fragile
  way — a bare `VAR=$(cmd)` followed by a `$?` check; Step 6 looks similar but
  does not read `$?` at all, so it is not in this class, though it has its own
  problems, tracked separately. None of the five were touched here — out of
  scope for this task, flagged as a follow-up.) Also fixed:
  `tools/find_unused_definitions.py` was missing its trailing newline.
  Demonstrated three ways: `validate-grammar.sh` exits 1 with the
  missing-baseline message when `.grammar_baseline.json` is absent; exits 0
  with "No regressions from baseline" once the baseline exists; and a
  temporary, non-committed edit to a copy of the baseline (dropping one
  already-known missing definition) reproduces a genuine
  `[ERROR] New missing definitions` regression and exit 1 — proving the
  comparison logic itself works, not just the present/absent gate. No grammar
  change — `git status --short src/` stayed empty throughout.

### Removed

- **Dead code cleanup: no parse tree changes.** Dropped `chartpart_keyword`
  (referenced nowhere but its own definition and absent from
  `node-types.json`, so it could never appear in a tree), the `_named_section`
  helper function (never called), and the first of two identical
  `empty_statement` definitions (the second silently shadowed it, so the rule
  itself was unaffected). Also corrected a misleading comment on
  `variable_declaration`'s Label arm: it said the type "must be" `Label`, but
  the rule accepts any `basic_type` — parse structure, don't validate; the
  "must" is a linter's job. Confirmed via `tools/tree-harness.sh verify`: all
  15,358 BC.History parse trees byte-identical before and after.

## [3.3.1] — 2026-08-09

Six external-scanner defects, all pre-existing and all found by a review of
`src/scanner.c` rather than by the corpus — BC.History and DO.Support-Agents
contain no instance of any of them, which is why 100% parse success never
flagged them.

### Fixed

- **Lookaheads now step over comments, not just directives.** Comments are
  `extras` exactly like `#pragma`/`#region`, but every hand-rolled lookahead in
  the scanner treated only directives as transparent. Two concrete failures:

  - `PREPROC_SPLIT_BEGIN` declined on a trailing comment, so
    `if not Ok then begin // note` before `#endif` produced 4 ERROR nodes where
    the identical file without the comment parsed as
    `preproc_split_if_begin_asymmetric`.
  - `PREPROC_SPLIT_END` skipped nothing at all — neither comments nor
    `#pragma`. **This one failed silently**: `end; // note` before `#else`
    dropped the token and reparsed the run as `(call_statement (identifier))`
    with **zero** ERROR nodes, so neither `parse-al-parallel.sh` nor
    `validate-grammar.sh` could see it. Both gates are error-count based and
    structurally cannot catch this class.

  New `skip_comment` and `skip_whitespace_and_comments` helpers handle `//` and
  `/* */`, and both split lookaheads now route through
  `peek_directive_ci_skip_extras`.

- **`PREPROC_SPLIT_END`'s `#endif` arm was unreachable** (no observable change
  today — see below). `read_keyword_ci(lexer, "else") || read_keyword_ci(lexer,
  "endif")` consumes the shared `e` on the failed `else` attempt, so the `endif`
  attempt started at `n` and could never match. `scanner.c`, `grammar.js` and
  the docs all describe `end; #endif` as producing the token; it could not.
  Nothing depends on that today — the only consumer,
  `preproc_split_code_block_end`, requires a `#else` after the token, and
  `end; #endif` is served by `_preproc_end_guard` — so parse trees are identical
  before and after. The value is that the branch is no longer silently dead: the
  rewritten helper takes a target *set* and tests all of them against one
  buffered read of the directive word, so a future rule relying on the
  `end; #endif` form will actually work. This is the same shared-prefix hazard
  documented for the `#endif`/`#endregion` pair in 3.3.0, which was sitting live
  twenty lines away.

- **`VAR_ATTRIBUTE_OPEN` declined a quoted name leading a multi-name
  declaration.** `[InDataSet]` followed by `"My Var", Other: Boolean;` gave 4
  ERROR/MISSING nodes; `Other, "My Var": Boolean;` was fine. The quoted branch
  checked only for `:` and had no `,` continuation. Quoted and bare names are
  now handled by one loop, so either may appear in any position.

- **`VAR_ATTRIBUTE_OPEN`'s bracket scan was comment-blind.** A `]` inside a
  comment within an attribute closed the scan early and declined the token.

- **`PROPERTY_NAME` rejected a newline before `=`.** The identifier-to-`=`
  whitespace skip listed `' '`, `'\t'`, `'\r'` and `'\f'` but not `'\n'`, while
  the leading skip did include it. `Caption` with `= 'Test';` on the next line
  produced 2 ERROR nodes; **alc accepts it** (verified). Comments between the
  name and the `=` are skipped too.

### Removed

- `peek_keyword_ci` — defined, never called.
- `paren_depth` in `VAR_ATTRIBUTE_OPEN` — incremented and decremented, never
  read, with a comment claiming it mattered.
- A comment in `CONTINUE_AS_IDENTIFIER` claiming "the scanner will be called
  again for the same position if we return false". It is not: tree-sitter
  discards the advances and runs the internal lexer. Replaced with the actual
  invariant that makes the early return safe.

## [3.3.0] — 2026-08-09

Additive-only — no previously-valid parse tree changes shape (verified via
`tools/tree-harness.sh`: all 15,358 BC.History `.al` files byte-identical to
the pre-change baseline; `parse-al-parallel.sh` re-confirms 15358/15358, 0
errors, 100%; `tree-sitter test` 1482/1482).

### Added

- **`#define` and `#undef` are now recognized**, as the new node types
  `preproc_define` and `preproc_undef`. Both are single-line regex tokens in
  `extras`, alongside `pragma`/`preproc_region`/`preproc_endregion`: they are
  line-level, take a single symbol name, and never touch the external scanner's
  `#if`/`#endif` depth counter. Case-insensitive, and tolerant of horizontal
  whitespace between `#` and the keyword (`# define`), matching the other
  directives.

  Microsoft documents both directives, and Microsoft's own Highlight.js AL
  grammar lists them, but BC.History contains zero occurrences — the base
  application declares its symbols via `preprocessorSymbols` in `app.json`
  rather than in source — so the gap went unnoticed and the fixtures in
  `test/corpus/preproc_define_undef_test.txt` are synthetic.

  The `extras` placement is deliberately more permissive than the compiler,
  which accepts these directives ONLY before the first real token of a file
  (`error AL0625`); comments, `#pragma`, `#region` and whole `#if`/`#endif`
  blocks may still precede or wrap them. Per "parse structure, don't validate",
  that positional rule belongs in a linter. `docs/preproc-define-undef.md`
  records the full compiler-verified accept/reject matrix (alc 18.0.37).

  `queries/highlights.scm` captures both as `@keyword.directive`. They are not
  added to `queries/folds.scm` — single-line directives that open nothing.

### Changed

- **The external scanner's `#endif` lookahead now steps over every transparent
  directive, not just `#pragma`.** `peek_keyword_ci_skip_pragma` is renamed
  `peek_keyword_ci_skip_extras` and skips `#pragma`, `#region`, `#endregion`,
  `#define` and `#undef` (`TRANSPARENT_DIRECTIVES`, kept in sync with the
  `extras` array). It now reads the directive word after `#` once into a buffer
  and classifies it, rather than trying candidate keywords in sequence —
  consuming `#` is irreversible within one scan, and so is consuming the `end`
  prefix shared by `endif` and `endregion`.

  Beyond the new directives this fixes `#region`/`#endregion` between a split
  `begin` and its `#endif`, which previously blocked `PREPROC_SPLIT_BEGIN`. No
  BC.History file relied on the old behaviour (tree harness: byte-identical).

## [3.2.0] — 2026-07-05

Additive-only — no previously-valid parse tree changes shape (verified via
`tools/tree-harness.sh` before/after on the full BC.History corpus [16,898
`.al` files], run TWICE from a clean `tree-sitter` build cache, manifest
sha256 identical both times: byte-identical to the pre-change baseline;
`parse-al-parallel.sh` re-confirms 16898/16898, 0 errors, 100% both runs;
`tree-sitter test` 1469/1469, confirmed byte-stable across 5 repeated
clean-cache runs).

### Fixed

- **`# if` / `# endif` (a single horizontal space between `#` and the
  keyword) is now recognized** — closing the limitation 3.1.0 documented and
  reviewed-and-rejected (see that entry's "Not supported" note below, now
  resolved). The external scanner's `PREPROC_OPEN`/`PREPROC_CLOSE` consume
  `#`, then optional horizontal whitespace (`' '`/`'\t'` only, via
  `lexer->advance(lexer, false)` so it counts as part of the token — never
  skipped as an extra, never a bare `isspace()`/`\s` test that could span a
  newline), then the case-insensitive keyword, as ONE token — so a spaced
  open/close increments/decrements the scanner's depth counter exactly like
  the unspaced form. **Scanner-exclusive ownership**: the grammar's
  `preproc_if`/`preproc_endif` rules now carry ONLY `$.preproc_open`/
  `$.preproc_close` — every grammar-literal fallback (`'#if'`, `'#IF'`,
  `'#If'`, `'#endif'`, `'#ENDIF'`, `'#Endif'`, `'# endif'`, `'# ENDIF'`,
  `'# Endif'`) is REMOVED. This retires a latent bug the old `'# endif'`
  literal fallback carried since its introduction (commit `500c1eb`): matching
  a spaced close via the grammar literal bypassed the scanner entirely, so the
  depth counter never decremented for it — a `# endif` anywhere in a real file
  would have silently corrupted `begin`/`end` keyword naming for the rest of
  the file. No corpus instance of this ever fired (BC.History has zero spaced
  `#endif` occurrences), so nothing was silently wrong in production, but the
  bug was real and is now closed at the root by making the scanner the sole,
  depth-correct route.
- **`# elif` (a single horizontal space)** is now recognized too — added as a
  plain grammar-literal variant (`'# elif'`, `'# ELIF'`, `'# Elif'`), mirroring
  the pre-existing, long-safe `preproc_else` spaced-literal pattern. `elif`
  carries no external-scanner token and touches no depth state (unlike
  `if`/`endif`), so this is a literal-vs-literal addition, not a
  scanner/literal split — there is no scanner token for elif to fork against.

### Why this is safe (the reverted 3.1.0 attempt was not)

The 3.1.0 attempt added `# if`/`# elif` as NEW grammar-literal alternatives
running ALONGSIDE the existing (already scanner-owned, for `if`) or
literal-only (for `elif`) routes — a genuine scanner/literal split for `if`,
which is a categorical GLR trap (two token-production routes for overlapping
text let the parser's conflict resolution fork non-deterministically across
process states). This time, `if`/`endif` are made **scanner-exclusive** (the
literal alternatives are REMOVED, not added-to) — there is only ONE route to
either token, spaced or not, so there is nothing for GLR to fork on. `elif`
(and `else`) never had a scanner token to fork against in the first place, so
adding their spaced literal is the same safe shape as the pre-existing,
long-working `preproc_else` variants.

Validation:
- `tree-sitter test`: 1469/1469 (1459 pre-existing + 10 new/updated: 9 in
  `test/corpus/preproc_if_elif_whitespace_tolerance_test.txt` [renamed from
  `..._not_recognized_test.txt` — the honest-rejection fixtures flip to
  positives, including the depth-correctness nesting proof, a
  case-insensitivity check, an unspaced regression control, a `# ifx`
  non-directive negative, and the cross-line negatives which STAY errors] + 1
  new GLR-stability repro appended to
  `preproc_split_if_then_begin_else_shared.txt` [the exact reviewer repro
  construct from 3.1.0, now with a spaced open] + 1 pre-existing test in
  `preproc_compound_conditions.txt` ("Preprocessor with spaced endif")
  corrected from the old buggy depth-bypassing shape to the new depth-correct
  one). Confirmed byte-stable across 5 repeated clean-cache
  `tree-sitter test` runs (identical 1469/1469 every time) and 5 repeated
  clean-cache parses of the GLR-stability repro and the nesting-depth-proof
  repro (md5-identical tree output every time — the non-determinism class
  from 3.1.0 does not reproduce).
- `tools/tree-harness.sh`: BC.History (16,898 `.al` files) manifest sha256 is
  IDENTICAL before/after this change
  (`d96393c178907dcc405b0e5b410fe4d86b82a86122af726e585c094fda72d60b`),
  confirmed on 2 separate clean-cache runs — proves zero shape change to any
  previously-valid tree and zero spaced-directive corpus hits (expected: BC
  source doesn't use this spacing style).
- `parse-al-parallel.sh`: 16898/16898, 0 errors, 100.0% success, both before
  and after (2 clean-cache runs post-change).
- Serialization untouched: the scanner's `ScannerState` (a 1-byte `depth`
  counter) and its `serialize`/`deserialize` lifecycle functions are
  byte-for-byte unchanged — only the token-matching body of
  `tree_sitter_al_external_scanner_scan` gained the whitespace-consuming loop.

Version 3.1.0 -> 3.2.0 (additive-only, minor bump per the v2.5.2->v2.6.0 /
v3.0.1->v3.1.0 precedent).

## [3.1.0] — 2026-07-04

Additive-only — no previously-valid parse tree changes shape (verified via
`tools/tree-harness.sh` before/after on the CDO source corpus + zero
divergence in the consuming engine's `cargo test --workspace` and the full
CDO resolution harness; `tree-sitter test` 1463/1463, confirmed byte-stable
across 5 repeated clean-cache runs — see the review note at the end of this
entry).

### Fixed

- **`OptionMembers = TableData,...` first-position collision.** Bare, unquoted
  `TableData` as the FIRST `OptionMembers` member case-insensitively collided
  with the `tabledata` keyword that starts `tabledata_permission` — GLR chose
  the keyword read, so the option list restarted from the second member and
  the first was dropped as an ERROR (a real production hit: MS `System`'s
  `Object.Table.al`, `NAVAppObjectPrerequisites.Table.al`,
  `DatabaseLocks.Table.al` all define an `Option` field whose first member is
  `TableData`). Fixed via a hidden `_tabledata_keyword` rule shared between
  `tabledata_permission` (unchanged shape — the token was already anonymous)
  and a new `alias($._tabledata_keyword, $.identifier)` arm in `option_member`
  (mirrors the existing `table_keyword`-via-`keyword_as_identifier` route for
  the same class of keyword-as-option-member). No new visible node kind; after
  the spaced-if revert `node-types.json` is byte-identical to the previous
  release (the `# pragma`/`# region` fixes are regex-value changes with no
  node-types entry).
- **`# pragma` (a space between `#` and `pragma`) not recognized at all.**
  `pragma` was `#pragma[^\n\r]*` with zero whitespace tolerance (a real
  production hit: Continia System Application's `Http.Codeunit.al`). Now
  `#[ \t]*pragma[^\n\r]*` — HORIZONTAL whitespace only (never `\s*`, which
  would let the extras token span a newline and silently swallow the next
  line's real source — see the region audit below, which found exactly that
  latent bug already present elsewhere in the grammar). Negative tests
  confirm `#\npragma` still does not match.
- **`preproc_region`/`preproc_endregion` cross-line hazard (audit).** Both used
  `#\s*region[^\n\r]*` / `#\s*endregion[^\n\r]*` — the regex crate's `\s`
  matches `\n`/`\r`, so `#` at the end of one line followed by `region`/
  `endregion` on the NEXT line was silently accepted as a single directive
  spanning both lines, swallowing whatever the `#` actually belonged to.
  Confirmed pre-fix via a scratch fixture. Tightened to `[ \t]*`
  (horizontal-only) alongside the pragma fix, closing the same bug class in
  the one other place it existed. The already-accepted single-horizontal-space
  form (`# region`, `# endregion`) is unaffected.

### Not supported (reviewed and explicitly rejected)

- **`# if` / `# elif`** (single horizontal space) — a preventive literal-variant
  fix (mirroring the pre-existing `# else`/`# endif` variants) was drafted and
  then DROPPED after empirical review found it introduced (a) genuine GLR
  non-determinism: the pre-existing `preproc_split_if_then_begin_else_shared`
  construct, fed a spaced `#if`-equivalent open, produced two mutually-
  exclusive stable parses across process states for byte-identical input (a
  small localized `ERROR` vs. a giant procedure-swallowing `ERROR`) — even
  `tree-sitter test`'s own pass count flapped (1453 ↔ 1463) with zero source
  change; and (b) a silent no-`ERROR` shape defect under `#if`-nesting: the
  literal-variant token doesn't participate in the external scanner's depth
  counter (the same trade-off `# else`/`# endif` already accept, which is
  fine for THEM since they carry no nesting-sensitive payload), so a spaced
  `# if` nested inside a real `#if` undercounted depth and the enclosing
  `code_block` silently lost its `begin_keyword`/`end_keyword` naming. The
  feature had zero corpus instances (purely preventive), so removing it costs
  nothing real. **Current, intentional behavior:** a spaced `# if`/`# elif` is
  NOT recognized as a preprocessor directive at all — the file `Recover`s
  (parses with an honest `ERROR` node) rather than silently producing a wrong
  or non-deterministic tree. The consuming engine's `ParseStatus::Recovered`
  diagnostic is the designed detection path: if a real corpus instance ever
  surfaces, it will be flagged for triage instead of passing silently. See
  `test/corpus/preproc_if_elif_whitespace_not_recognized_test.txt` for the
  documented-non-support fixtures (including the honest recovery shape). A
  future fix, if warranted by a real corpus hit, belongs in the external
  scanner (so it participates in the depth counter) — NOT another literal
  variant.

  **RESOLVED in 3.2.0** (2026-07-05): the external-scanner route this note
  called for has landed — `PREPROC_OPEN`/`PREPROC_CLOSE` now consume optional
  horizontal whitespace as part of the token, participating in the depth
  counter exactly as this note anticipated. Scanner-exclusive ownership (the
  grammar-literal fallback for `if`/`endif` is REMOVED, not extended)
  eliminates the scanner/literal split that caused the GLR non-determinism
  described above. See the [3.2.0] entry. The renamed fixture file is
  `test/corpus/preproc_if_elif_whitespace_tolerance_test.txt`.

## [3.0.1] — 2026-06-17

### Added

- Rust binding now exports `TEXTOBJECTS_QUERY` (alongside `HIGHLIGHTS_QUERY`,
  `LOCALS_QUERY`, `TAGS_QUERY`, `FOLDS_QUERY`, `INDENTS_QUERY`) so Rust consumers can
  load `queries/textobjects.scm` directly. The query file shipped in 3.0.0 but was not
  exposed as a crate constant.

No grammar or parse-tree changes — parser is byte-identical to 3.0.0.

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
