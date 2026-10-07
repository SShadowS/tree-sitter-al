# B7b-1: conditional groups in strict delimited lists (design, rev 2)

Roadmap B7, sub-project B7b-1 (user decisions 2026-10-07: B7b order B7b-0 → B7b-1 list separators →
B7b-2 expression continuations → B7b-3 terminators; approach A, a shared generator with one
conditional node per host; the narrowed split, chosen as the thorough option — every list host is
fixed, each family in its own sub-project with its own schema and gates). Input: the B7a matrix
`docs/b7-separator-continuation-matrix.md`, probes `tools/alc_probe/cases/b7-audit/`, witnesses
`test/corpus/b7_gap_*_test.txt`. Rev 2 adopts both gpt-6.1-sol reviews (first design: 7 findings;
rev 1: 8 findings) — mapping at the end. Status: design, awaiting review.

## 1. Problem

The B7a audit found lists in which an `#if` group may not stand at a separator: alc accepts
`key(PK; A #if X , B #endif , C)` in every configuration and the parser ERRORs (GAP). Two patterns
exist — element-attached groups (`arguments`, `grammar.js:6600-6660`, no self-nesting, no
separator-only seam between two raw elements) and the run/group sequence (link, where, permissions,
`grammar.js:2255-2300`) — but most lists have neither. A generic conversion of every list was rejected:
property-value lists collide with whole-value `#if`, B11 runs, B13 fragments and option holes.

## 2. Scope and the route manifest

**Admission condition (per host route, per insertion boundary):** at this exact boundary, with the
enclosing delimiters fixed OUTSIDE the group, no alternative complete derivation (whole-value `#if`,
B11 run, B13 fragment, existing conditional) can own a group placed there; the list is homogeneous
with one separator kind and no holes; and every matrix cell of the route at that boundary is GAP, or
MIXED whose alc-accepted configurations are all GAP-shaped, with none SILENT or owned by B12/B13.
(Rev 1's "tokens that never take part in property-value routing" was too broad — sorting and OrderBy
values are property values; their INNER lists are still admissible because the keyword and parentheses
stay outside the group.)

**The manifest** `tools/b7_audit/b7b1-manifest.tsv` (committed before any grammar change, first plan
task) lists every matrix cell of every candidate family with a disposition — `admitted`, `excluded`
(reason) or `deferred` (owner) — and freezes, for admitted cells, the alc configuration vectors and
the expected verdict after the fix. Refreshing assertions after the change may never redefine away a
failed admitted cell or a new SILENT result: the gate compares against the frozen manifest.

**Dispositions already known (rev-1 review):**

| route | disposition |
|---|---|
| `field_list` in `key_declaration`, `preproc_split_key`, `fieldgroup_declaration`, `addlast_fieldgroup_modification` | admitted (inner list; `field_list` keeps its node, stays unfielded) |
| `field_list` in `addfirst_fieldgroup_modification` | **excluded**: alc rejects `addfirst` in tableextension fieldgroups (syntax, matrix "Not probed"); the shared rule may widen the existing over-acceptance — classify that effect, never count it as a fix |
| `sorting_value` inner field list (`grammar.js:~2205`) | admitted; the order/where suffixes and the complete sorting value are not; the B13 sorting/where seed stays B13 |
| `order_by_item` inner list (`~2556`) | admitted; the outer comma-separated `order_by_list` is property-value routing — **excluded** |
| `moveArgs` element list after the fixed `;` (`~91`) | admitted for groups at element separators only; cells whose group supplies or replaces the fixed `;` or the target are **excluded** (fixed-header separator/slot, B7b-3 territory) — the move family does NOT flip wholesale |
| `implements_clause` (`~1153`) | admitted |
| `variable_declaration` multi-name arm (`~4768`) | admitted, with §5 |
| `array_type` dimensions (`~3110`) | admitted (homogeneous integer list in `[ ]`) |
| `attribute_argument_list` (`~4812`) | admitted, with route cardinality (§4.2) |
| `dictionary_type` / `list_type` type arguments (`~3126-3144`) | **out of B7b-1**: fixed-arity positional slots (`key_type`, `value_type`), not a list; owner **B7b-1g** (fixed-arity slot adapter) — recorded in deferred-work with its witnesses |

**Out of B7b-1, later sub-projects:** B7b-1b parameters (`;`, attribute bundles, empty list); B7b-1c
ML/Namespaces pair interiors and list literals (whole-value ownership table); B7b-1d report-label and
label-variable attribute tails, caption sub-fields (heterogeneous tails, unwrap); B7b-1e OptionMembers
(holes, witness policy); B7b-1f Permissions and link lists; B7b-1g fixed-arity type slots. B13 overlaps
stay B13 unless a later sub-spec reassigns them occurrence by occurrence.

## 3. Generator: the seam factoring

Rev 1's shape (element + attached groups; branch = `[sep] run`) cannot parse a separator-only arm
between two raw elements (`A #if X , #else , #endif B`) or an arm holding both separators
(`A #if X , B , #else , #endif C`), both committed witnesses. Rev 2 uses a single hidden **seam unit**
that holds successive raw elements joined by conditional groups. For family `F`, separator `s`, raw
item `atom` (individually fielded where the host fields its items):

```js
_F_list:   $ => seq($._F_e, repeat(seq(s, $._F_e))),
_F_e:      $ => choice(seq(atom, optional($._F_t)), $._F_t),
_F_t:      $ => seq($.preproc_conditional_F, optional($._F_e)),
preproc_conditional_F: $ => seq(
  $.preproc_if, optional($._F_b),
  repeat(seq($.preproc_elif, optional($._F_b))),
  optional(seq($.preproc_else, optional($._F_b))),
  $.preproc_endif),
_F_b:      $ => choice(seq(s, optional($._F_r)), $._F_r),
_F_r:      $ => seq($._F_e, repeat(seq(s, $._F_e)), optional(s)),
```

- No rule matches empty: `_F_e` consumes an atom or a group, `_F_t` a group, `_F_b` a separator or a run.
- `A G B`, `G A`, `A G G B`, a separator-only arm, a both-in-arm arm and recursive groups inside a
  branch are all one family-local derivation. A trailing separator in a branch is shifted first, then
  another `_F_e` or a directive decides — no competing partial-prefix run, no two-token lookahead.
- All helpers are hidden; "attached to the previous element" vs "opening the next" is not a public
  contract. The visible tree is the host with `preproc_conditional_F` children in source order.
- The factoring admits conditional streams some of whose configurations are invalid AL; correctness of
  each configuration is the oracle's configured-stream check (§6), and an all-configurations-invalid
  form keeping an ERROR is not required of the parser (the matrix's REJECTED cells say which are
  syntax-invalid; a parser that accepts one becomes an over-acceptance to classify, not a gate failure,
  unless it was clean-ERROR before and alc rejects every configuration — then it is a regression).
- Generation result and conflicts are measured in a spike (first grammar task) before any host
  conversion; the spike may refine the factoring but must keep every property above.

## 4. Tree shape, fields and preservation

### 4.1 Fields (node API)
Field labels are parent-child relations: an item inside `preproc_conditional_F` is NOT seen by a
query on the host's field. Consequences, stated as the contract:
- The new nodes field their raw items with the host's item field name (`element`, `interface`,
  `name`, `size`…) — `multiple: true`, `required: false` (groups may be empty or hold only groups).
- A host field may become `required: false` in node-types.json where every raw item can sit in a
  group; that is an intentional API change, listed per host in the CHANGELOG.
- Unfielded hosts (`field_list`, sorting and order-by interiors, attribute arguments) stay unfielded;
  `_F_e`/`_F_list` are never fielded wholesale.
- `tools/check-field-types.py` gains the new nodes AND the `required` dimension for affected existing
  hosts.
- var-names: the multi-name arm and the regular declaration arm are merged into one ordinary-type arm
  over `_F_list` (a declaration whose only comma is conditional must parse), with the label arm and
  TextConst arm unchanged; the existing trees of all valid declarations stay identical (§4.3).

### 4.2 Route cardinality (empty lists)
Strictness does not imply non-emptiness. Per route the manifest records one of:
1. **empty interior, delimiters kept** (e.g. `sorting(#if X K,N #endif)` — a committed GAP witness):
   the configuration's flat text `sorting()` is judged by alc; the matrix says accepted → the route
   allows an empty selected interior;
2. **optional wrapper removed**: `attribute_arguments: '(' optional(attribute_argument_list) ')'` —
   flat parsing of an emptied configuration has no `attribute_argument_list`; the oracle needs the
   named rewrite `optional-list-removed:<kind>` (not the generic `empty-node` error);
3. **empty rejected as syntax** (alc syntax code) — the configuration is invalid; the split tree may
   still parse (MIXED);
4. **empty rejected semantically only** — same parse policy as 3, recorded separately.
A flat empty form that is wrong today (if any is found) gets an explicit disposition in the manifest,
never silent preservation.

### 4.3 Preservation
- **Four-corpus full cursor-tree parity** (BC.History, DC, BC28.1, BCApps-29.0) with `tools.perf ab`'s
  tree comparison (anonymous nodes, fields, spans, grammar names) — required on all four.
- **Preservation fixtures** with HAND-WRITTEN expected trees (not taken from the new CLI) for valid
  shapes no corpus holds: per host plain lists, quoted (incl. escaped `""`) and contextual-keyword
  elements, comments at every boundary, the host inside an enclosing whole-declaration `#if`, the host's
  list wholly inside one arm of an enclosing conditional, and every existing flat empty form.

## 5. Var-names and the variable-attribute scanner

`var_attribute_open` is decided by a lookahead that reads `name (',' name)* ':'`
(`src/scanner.c:~900-935`) and declines on anything else; it also stops a quoted name at the first
`"`, unlike `quoted_identifier` (escaped `""`).

1. **alc first, syntax vs semantic separated:** probes for attributed multi-name declarations with a
   group at each separator placement, separator-only groups, a group before the first name
   (first-name replacement), nested groups, `#elif`, adjacent groups, escaped-quote and Unicode /
   contextual names, malformed directive prefixes, unterminated groups, directives inside comments and
   quotes — plus the procedure-attribute counterparts. Diagnostics are classified syntax vs semantic
   with compiler controls; a semantic restriction never justifies a scanner rejection.
2. **The recognizer** (if alc accepts the forms syntactically): the lookahead recognises a
   **conditional name/separator stream ending at the shared `:`** — names, commas, balanced
   `#if`/`#elif`/`#else`/`#endif` (directive lines read whole, conditions skipped to end of line,
   branch payload restricted to names and commas), comments and directive extras — and fails at `(`,
   `;`, `{`, `}`, a procedure keyword or EOF. It is a local peek: it never mutates `ScannerState.depth`,
   the token end stays at the original `[` (`mark_end` before peeking; non-marking advances after — the
   reason is documented at `scanner.c:~379-389`), and the escaped-quote mismatch is fixed in the same
   lookahead.
3. **Tests:** corpus cases pinning which node owns `[` for every probed shape; a `has_error` pytest;
   incremental edits of names/directives after an unchanged attribute prefix (long-range lookahead
   invalidation).

## 6. Config oracle

A **family schema registry** plus **original split-tree validation**:

1. **Before selection** (on the multi-configuration tree): each `preproc_conditional_F` occurs only in
   its permitted parent/slot (and recursively in itself), is unfielded, its span lies inside the
   family's list region and inside the enclosing arm; source order and containment hold; no group in a
   move target, a type, a sorting suffix or an outer OrderBy list.
2. **Region adapters** per family: `field_list` and `attribute_argument_list` do not own their
   delimiters; the move list is the part after the fixed `;`; var names end at `:`; sorting excludes
   the order/where suffixes.
3. **Fragment vs complete policy:** a selected branch may emit a leading separator, a trailing one or
   a separator alone; alternation `item (sep item)*` is validated only on the reconstructed complete
   region, never per fragment. The new validator replaces `_check_alternation` for these families
   (that one ignores brackets anywhere, treats non-comma as item and drops a trailing `;`).
4. **Empty policy** from §4.2, with the named rewrite `optional-list-removed:<kind>`.
5. Every new node registered in `contracts.py`, `traversal/policy.json` (F0 census) and query coverage.

**Tests:** independent expected split CSTs for the focused fixtures (hand-written); every feasible
configuration of each fixture exercised; mutation cases — attachment, field name, separator count,
element order, nesting, empty groups, unselected arms, wrong outer-arm ownership, neighbouring
same-family nested regions — each must fail. Gates: oracle unit tests, `replay`, quick tier, full tier
over four corpora with 0 discrepancies; "no new unclassified refusals" is necessary, not sufficient —
the focused fixtures must show the new families LOWERED (status pass), not classified away.

## 7. Proof and gates

- **Frozen baseline:** the manifest (§2) is committed before the grammar change; after the change,
  every admitted cell must reach its frozen expected verdict on a full re-run; excluded/deferred cells
  must not change verdict except as classified in the manifest.
- **Witnesses:** admitted `b7_gap_*` cases become positive fixtures with HAND-WRITTEN trees (checked
  against the 0.27 CLI, not copied from it) covering both separator placements per route, nested
  groups, separator-only and both-in-arm arms, adjacent complementary and independent groups, empty
  arms, comments, polarity; excluded cases stay `:error` witnesses; assertions, fixture-classes,
  deliberate-negative membership and census updated together.
- **MIXED kept apart:** compiler rejection vectors, split-parser acceptance and configured validity are
  reported separately; a MIXED source may have a positive split CST while an invalid configuration
  stays invalid.
- **Incremental:** fresh vs incremental full cursor trees for edits moving a separator into and out of
  an arm, deleting `#else`, adding/removing groups, and (var-names) edits after an unchanged attribute
  prefix.
- `has_error` sweeps (four corpora + fixtures); `validate-grammar.sh --full`; traversal census; query
  coverage; field invariants incl. `required`.
- **Cost per host:** STATE_COUNT, LARGE_STATE_COUNT, SYMBOL_COUNT, parser.c bytes, generation time,
  conflicts — standalone marginal (stub-and-regenerate) and cumulative; guidelines, not caps.
- **Performance:** `tools.perf ab` over DC on the identical-tree corpus (24 rounds, repeated); for
  repaired inputs (trees differ, `ab` refuses) a **candidate-only scaling benchmark** — synthetic files
  growing in list length and nesting depth, with explicit time and memory limits, checking near-linear
  growth (pathological GLR behaviour shows as super-linear).

## 8. Review mapping

First design (gpt-6.1-sol): 1 B13 collision → §2 out-of-scope + B13 default; 2 whole-value theft →
boundary admission condition §2; 3 nesting/holes → §3 recursive seam, holes out; 4 oracle → §6 schemas;
5 scanner → §5; 6 preservation → §4.3; 7 inventory → §2 manifest.
Rev 1 (gpt-6.1-sol): 1 separator-only/both-in-arm seams → §3 seam factoring; 2 empty lists → §4.2 route
cardinality; 3 scanner recognizer → §5.2 and syntax-vs-semantic probes; 4 attachment validation → §6.1-6.4
and independent CSTs; 5 inventory → §2 known dispositions (move fixed `;`, addfirst, outer OrderBy,
sorting suffixes) and the manifest; 6 field API → §4.1; 7 type arguments → out, owner B7b-1g;
8 gates → §7 frozen baseline, hand-written trees, scaling benchmark, incremental attribute edits.

## Rev 2 execution amendments (2026-10-07)

Recorded at the end of execution (plan `docs/superpowers/plans/2026-10-07-b7b-1-strict-conditional-lists.md`, Task 14).
The sections above are left as reviewed; where they differ from what shipped, these amendments and their controller
rulings govern.

1. **§3, the generator: `_F_list` is not a rule.** The host inlines the list body with `...strictListBody($, family,
   sep)`; `strictConditionalList(family, atom, sep)` returns the factories `_F_e`, `_F_t`, `preproc_conditional_F`,
   `_F_b`, `_F_r`. Ruling (Task 4): a hidden list rule moves every separator's B7a census key (`occ:<host>:<path>`) and
   orphans the frozen manifest's cell ids; inlining keeps the keys, the language and the tree identical. Separators
   inside group arms register as `equiv occ:<host>:<path>` rows in `tools/b7_audit/registry.tsv`, with no new cells.
2. **§3, optional fourth parameter `groupDynamic`** (Task 11): a dynamic precedence on the visible group, for a host
   where a group may also be read as a neighbouring conditional and both readings complete. Only var names use it
   (-1): an empty group before a declaration at `var_body` top level, with or without a preceding attribute, stays a
   sibling `preproc_conditional_var`; inside a `preproc_conditional_var` arm, in a split var section tail, or nested in
   a group at top level it is the next declaration's leading `preproc_conditional_var_names`. The var-names conversion added 10 GLR conflicts
   (a declaration may now start with `#if`), each required (removing one fails generate); 0 new forks on production.
3. **§4.1, var names: the arms are not merged.** Ruling (Task 11): arm 3 (the regular single-name arm) is kept and the
   multi-name arm inlines `strictListBody`; the language and the visible tree are the same as the merge would give.
   Deleting arm 3 ERRORs single-name declarations, because the label-vs-ordinary choice needs it or a per-declaration
   GLR conflict.
4. **§4.2 and §6.4, cardinality is evidence, not policy.** Ruling (Task 5): `Family.cardinality` records alc's verdict
   in the manifest vocabulary (`empty-interior | optional-wrapper | empty-syntax-rejected | empty-semantic-rejected`) and
   has no effect on lowering. An emptied region lowers by the flat grammar: a configuration whose flat text does not
   parse is a reference-error (classified invalid-config); otherwise it is lowered structurally (or removed as
   `optional-list-removed:<kind>`) and the comparison decides. Where alc accepts an empty interior the grammar now does
   too (rulings Tasks 6 and 7): `addlast(X; )`, `sorting()`, `ascending()` / `descending()`.
5. **§3, the regression clause scopes to the manifest cells.** Ruling (Task 6): an unmanifested conditional form invalid
   in every configuration that now parses clean is a classified over-acceptance, not a regression (keeping its ERROR
   needs per-arm separator tracking, which §3 does not require). Recorded with its inputs in `docs/deferred-work.md`
   item 44.
6. **§7, the scaling gate** (Task 13): the time ratio per doubling must stay below 2.5 measured two ways, fitted over
   every point (least-squares slope of log t over log x) and at the last doubling step, instead of at every single
   step; the worst single step is reported only, because on a shared machine sub-millisecond steps reached 2.5-2.9 while
   the mean stayed about 2.0. The depth series puts 200 nests of depth D in one list, so its input bytes grow with D: a
   ratio near 2.0 there means time linear in input size, not constant per nest. `python -m tools.perf.strict_lists_scaling`.
7. **§7, matrix refresh once per branch** (Task 5): `assert --refresh`, a full `run` and `report` ran once, in Task 13,
   not after each host task. The 1,422 assertion rows that close the admitted and header cells come from a model of each
   cell's hole text, never from the parser (`tools/b7_audit/strict_list_assertions.py`). The frozen manifest
   (`tools/b7_audit/b7b1-manifest.tsv`) was amended once after the freeze: in `dc240b0` (Task 6) the `reason` of
   `route:occ:field_list:1.0.0@addfirst_fieldgroup_modification` gained the sentence "Task 6 measured: it does; addfirst now
   parses a #if group in its field list clean (...), classified OVER-ACCEPTANCE (...), not a fix; its field list stays
   required"; its disposition (`excluded`), owner, cardinality and verdict are unchanged.
