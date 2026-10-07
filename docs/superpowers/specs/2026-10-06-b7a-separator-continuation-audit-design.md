# B7a: the separator and continuation audit (design, rev 2)

Roadmap row B7, first sub-project (user decision 2026-10-06: audit first, then one bounded fix per defect
family, ordered by this audit). Deferred-work items 1, 2, 30, 37, 38 and 39 feed it. Status: design,
awaiting review. Rev 2 adopts the gpt-6.1-sol review of rev 1 (all eight P1 and both P2 findings; see
the end of this document for the mapping).

## 1. Why

`812ace7` (4.0.0) made comma-separated lists a sequence of runs with `#if` groups between them, so an arm
can supply the separator its neighbour lacks. An audit then listed 26 separator sites and six positions
without a preprocessor host (deferred-work item 1). That list was never re-verified. Item 2 showed that
a rule existing is not the same as a shape being covered (`X, #if FOO Y #endif` parses, `X #if FOO , Y
#endif` ERRORs). B6 left two valid split shapes as loud ERRORs because their hosts have no continuation
(item 39). Fixing hosts from a stale hand list repeats the 4.0.0 mistake: which boundaries exist, which
hosts reach them, and the fix order must come from a reproducible measurement.

B7a measures and records. It changes no grammar rule, no `src/` file and no existing expected tree.

## 2. What the audit can and cannot claim

- **Completeness over the grammar** is checked mechanically: every structural punctuation occurrence and
  every expression boundary in `src/grammar.json`, and every host route that reaches it, has a classified
  registry row (section 3, 4). A new helper, caller or punctuation occurrence fails the gate.
- **Completeness over the language** cannot come from the grammar alone. It is approximated by a seed
  inventory (section 5) of shapes from the backlog, the compiler probes already committed, and the
  production corpora.
- **Correctness of a clean tree** is not proven by the oracle. A pass proves the split tree is
  CONSISTENT with the flat parses under the oracle's checks; a defect shared by both is invisible. Every
  cell the audit calls correct also carries an independent structural assertion (section 7.3).

## 3. Census

`tools/b7_audit/census.py` reads `src/grammar.json` and emits three lists. It is pure (grammar.json in,
lists out) and has unit tests on a hand-written mini grammar covering REPEAT, right recursion, helper
SEQs repeated by a caller, `optional` separators outside a REPEAT, cycles, aliases and `inline`.

### 3.1 Boundary occurrences

Every `STRING` among `,` `;` `..` `.` `::` `:` and every `CHOICE`/`optional` of them, at any nesting
depth, outside atomic lexical constructs (`token`, `IMMEDIATE_TOKEN`, `PATTERN`), keyed
`(rule, path)`. Each occurrence carries its structural context, computed through rule references with
cycle detection: inside a REPEAT/REPEAT1, inside a right-recursive rule, inside a helper SEQ that a
caller repeats, optional, or fixed. Lexical punctuation is listed as `lexical` and out of scope, never
dropped.

### 3.2 Expression boundaries

Every position where an `_expression` (directly, or through one hidden rule) begins or ends inside a
host: keyed `(rule, field or path, edge)` with `edge` one of `start`, `end`, `between` (for repeated
elements such as later subscript indices). Each records which continuation mechanisms are offered at
that edge, read from the grammar: `preproc_conditional_expression_tail` (suffix, operator-led arms),
its operator-only form, `preproc_operand_prefix` (prefix, operand-led arms after a dangling operator),
and whether the mechanism is required or optional. The rev-1 claim "9 rules have a tail" is replaced by
this per-edge table (e.g. `for_statement` has a tail after `end`, not `start`; `subscript_expression`
after the first index only; `_property_value_with_split`'s tail is required).

### 3.3 Host routes

For every occurrence and boundary, the visible user-written hosts that reach it (`field_list` → keys,
fieldgroups, fieldgroup modifications; `parameter_list` → procedures, interface procedures, triggers,
ControlAddIn events; `ml_value_list` → keyed ML properties, TextConst declarations; `option_member_list`
→ generic property values, Option types; the link union → its six property names). A route is the
chain of rules from a host rule to the occurrence.

## 4. Registry and its gate

`tools/b7_audit/registry.tsv`, one row per (occurrence or boundary, host route):

| column | meaning |
|---|---|
| `key`, `route` | from the census |
| `role` | `list-separator`, `edge-separator` (leading, trailing, empty slot), `fixed-separator`, `terminator`, `qualifier` (`.`, `::`, `..`, `:`), `continuation`, `lexical`, `na` |
| `family` | the defect family a fix would touch (section 8); several rows share one |
| `template` | AL source with one `⟨HOLE⟩`, self-contained and compilable (no Base App symbols), typed for the slot (Boolean slots get Boolean operands, lvalue slots an lvalue) |
| `equiv` | `same-as <row>` with an argument covering host context (same precedence, same scanner states, same conditional attachment), or empty |
| `reason` | required for `na`, `lexical` and `equiv` |

Gate: `python -m tools.b7_audit census --check` (new validate-grammar.sh step and a CI step): exit 1 when
a census occurrence, boundary or route has no row, or a row matches nothing (stale); exit 2 when
grammar.json is missing. New callers are gated as well as new punctuation.

## 5. Seed inventory

`tools/b7_audit/seeds/`, AL files each holding one shape that must be in the matrix, with its source:

- deferred items 1, 2, 30, 39 reproducers verbatim (item 39's assignment keeps its `Foo();` after the
  selected terminator, which is what makes ownership worth testing);
- the B13 gap file `test/corpus/property_value_run_b13_gap_test.txt` and item 38's shape;
- the committed alc cases that involve a separator or a continuation
  (`tools/alc_probe/cases/{g11-*,link-keying,pair-list-keying,value-runs,expression-statement}`);
- production shapes: every distinct `(host route, placement class)` pair found by a tree walk of the four
  corpora (BC.History, DC, BC28.1, BCApps-29.0) where a `#if` group sits next to a separator or an
  expression edge, with the count of sites.

A seed is a cell like any other (section 6.3) and cannot be dropped from the matrix.

## 6. Placements

Every expansion is written literally in `tools/b7_audit/placements.py`, each with its intended
configuration-validity vector (which symbol assignments are meant to be valid AL), so a generated input
that is invalid in every configuration by construction is a generator bug, not a verdict.

### 6.1 Separator placements (elements `A B C D`, separator `s`)

| id | shape (directives on own lines) | intended valid |
|---|---|---|
| `sep-after` | `A s #if X B s #endif C` | all |
| `sep-before` | `A #if X s B #endif s C` | all |
| `sep-before-end` | `A #if X s B #endif` | all |
| `first-replace` | `#if X A #else B #endif s C` | all |
| `lead-optional` | `#if X A s #endif B` | all |
| `count-differs` | `A #if X s B s C #else s D #endif` | all |
| `both-in-arm` | `A #if X s B s #else s #endif C` | all |
| `sep-only` | `A #if X s #else s #endif B` | all |
| `empty` | `A s #if X #endif B` | all |
| `adjacent` | two groups in a row, independent (`X`, `Y`) and complementary (`X`, `not X`) | all |
| `elif` | `sep-before` plus an `#elif Y s C` arm | all |
| `nested` | `A #if X s B #if Y s C #endif #endif s D` (each nested arm owns its separator) | all |
| `one-elem` / `empty-list` | the list reduced to one element / none inside an arm, where the host allows | per host |
| `holes` | leading, consecutive, trailing separator (option members keep ordinals) | per host |
| `trail` | `A s #if X B #endif` | X only, unless the host allows a trailing separator |
| `comments` | each of the above with a `//` and a `/* */` comment at every boundary | as base |
| `polarity` | each of the above with `#if not X` | as base |

Element samples include a quoted identifier and a contextual keyword where the host allows, and an
element that resembles a sibling property or declaration, to expose attachment ambiguity.

### 6.2 Continuation placements

Per boundary edge, per operator family (arithmetic `+ * div mod`, comparison `= <>`, logical
`and or xor not`, membership/type `in is as`), with typed operands:

| id | shape | intended valid |
|---|---|---|
| `suffix` | `E #if X op F #endif` | all |
| `suffix-else` | `E #if X op F #else op2 G #endif` (different operators per arm) | all |
| `op-only` | `E #if X op #endif F` | X only (as B3's `split-operator.al`) |
| `prefix` | `E op #if X F op #endif G` (`preproc_operand_prefix`'s shape) | all |
| `whole-operand` | `E op #if X F #else G #endif` | all |
| `first` | `#if X E op #endif F` and a conditional only expression | all / per host |
| `chain` | `E * F #if X + G #endif * H` and `E or F #if X and G #endif or H` (grouping discriminates) | all |
| `consecutive` / `nested` | two continuation groups in a row; one inside another | all |
| `unary-paren` | an arm opening `(`, `-`, `not` | per operator |
| `semi-in-arms` | `E #if X op F; Foo(); #else ; #endif` | all, ONLY where the host is a statement whose expression may end the statement (assignment, call, exit with value); never an `if`/`while`/`for` header |
| `signed` | operand a signed literal (`-1`), exposing the signed-literal one-reading refusal | per host |

## 7. Judging a cell

### 7.1 Evidence

For each cell the runner records, per symbol assignment, a configuration vector:

- alc split and flat verdicts with diagnostic codes (via `tools.alc_probe`, controls first; a `BROKEN`
  project or an alc split/flat `MISMATCH` fails the run);
- whether alc's rejection is syntax (AL0104/AL0107/AL0111/AL0224 class) or semantic (everything else),
  from a typed flat control that compiles the same configuration's text with a known-valid element;
- the parser's `has_error` on the split source, and whether ERROR/MISSING lies inside the cell's hole;
- the oracle record per configuration from `tools.config_oracle.runner.check_input`: `pass`,
  `discrepancy`, `representation-violation`, `directive-mismatch`, or `cannot-validate` with its reason
  (unsupported type/host, one-reading, contract shape, accounting, unconsumed fragment, alternation).
  An `internal-error` item fails the run; it is never a verdict and never reviewed by hand.

### 7.2 Verdicts

| verdict | condition |
|---|---|
| `CONSISTENT` | alc accepts every configuration; parser clean; oracle `pass` for every configuration; structural assertion holds |
| `GAP` | alc accepts every configuration; parser ERRORs |
| `SILENT` | alc accepts every configuration; parser clean; oracle `discrepancy` or `representation-violation`, or the structural assertion fails |
| `MIXED` | alc accepts some configurations and rejects others (split constructs such as B3's `op-only`); judged per accepted configuration as above, recorded with the vector |
| `REJECTED` | alc rejects every configuration; sub-verdict `syntax` or `semantic` from the typed control; parser ERROR is `agrees`, parser clean is `over-accepts` (a syntax over-acceptance is a finding; a semantic one is out of scope by project policy) |
| `UNCHECKED` | alc accepts; parser clean; oracle `cannot-validate` for some configuration and no structural assertion yet |

`UNCHECKED` is never folded into `CONSISTENT`. Each `UNCHECKED` cell is closed by a structural assertion
(7.3) or stays listed as unchecked in the matrix with its refusal reason.

### 7.3 Structural assertions

`tools/b7_audit/assertions.tsv`: per cell (or per placement class and family, when the shape is
uniform), an expected-tree fragment written by hand from the flat reading of each configuration: which
node owns each element, the separator and the continuation, with fields. A cell's assertion is checked
against the split tree. Each assertion row carries fingerprints (sha256 of the cell source, of
`src/parser.c`, of `src/scanner.c`, of the oracle package) so a grammar change re-opens it.
A mutation check (rename a field to `bogus`, drop an element) proves each assertion class can fail.

## 8. Outputs

- **Canonical evidence**: `tools/b7_audit/evidence.jsonl`, one sorted record per cell and configuration
  (source hash, verdict inputs, diagnostic codes, oracle items), with execution metadata (alc
  version and assembly hashes, runtime, corpus manifests with HEADs, parser hashes) in a separate
  header record. Paths normalised, LF line ends.
- **Matrix**: `docs/b7-separator-continuation-matrix.md`, generated deterministically by
  `python -m tools.b7_audit report` from the committed evidence (byte-identical on any machine).
  `python -m tools.b7_audit run --check` re-measures and fails when a verdict differs from the evidence;
  it requires every corpus root present and refuses a different alc identity unless `--accept-tool`.
- **Fixtures**: `GAP` and `REJECTED/over-accepts(syntax)` cells get a committed alc probe under
  `tools/alc_probe/cases/b7-audit/` (`--check` clean) and a corpus fixture pinning today's tree
  (deliberate negative for GAP, oracle `debt(B7)`; the over-acceptance fixture's header names the
  defect). `SILENT` cells do NOT go into `test/corpus/`: the quick tier reads corpus sources and a
  discrepancy cannot be classified. They go into `tools/b7_audit/tests/test_silent.py`, which asserts
  each cell's current oracle finding and is flipped to require `pass` by the fix.
- **Defect families**: cells deduplicated into families (one grammar cause, possibly many cells),
  each with: the cells, the hosts, the observed defective production sites (from the seed tree walk,
  not host prevalence), dependencies (e.g. the comma-leading link list depends on the link/property
  ambiguity matrix, roadmap B7), and owner. Cells overlapping B12/B13 (deferred items 36, 37, 38) are
  assigned there explicitly.
- **Ranked fix list for B7b+**: by `SILENT` families first, then `GAP` and syntax `over-accepts`
  families by defective production sites, then by dependency order; `UNCHECKED` listed separately,
  never ranked as clean.
- Deferred items 1 and 2 rewritten from the matrix; items 30 and 39 cross-referenced to their cells.

## 9. Gates

- `census --check` exit 0 (validate-grammar.sh and CI).
- `report` regenerates the committed matrix byte-for-byte from the committed evidence.
- `run --check` exit 0 on the author's machine against the recorded alc identity and corpus manifests
  (a slow gate; not in validate-grammar.sh quick mode).
- alc_probe `--check` over the new cases clean; `tree-sitter test` total moves by exactly the cases
  added; has_error sweep over the corpus fixtures clean; oracle quick tier exit 0 with the new `debt(B7)`
  entries; `validate-grammar.sh --full` green.
- No change to `grammar.js`, `src/`, or any existing expected tree.

## 10. Cost and shape of the run

The parser and the oracle check every cell (seconds for the whole matrix). alc runs per cell and
configuration, split and flat, with `tools.alc_probe`'s worker pool (default six), cached by
(exact source, configuration, runtime, compiler identity). Rough size: about 2,800 compiles for the
generic placements before the semicolon cells and the seeds, so a cold run is a few hours of
compiler time; `run --only <family|row>` re-runs a slice, and the cache makes re-runs cheap. Proven
equivalent rows (`equiv`) share cells but keep one host-parity witness each.

## Execution amendments (2026-10-07)

Rulings taken while building and running the audit that change the design above. Each is recorded in the
B7a ledger (`.superpowers/sdd/2026-10-06-b7a-separator-continuation-audit/progress.md`); the code is the
reference.

1. **Evidence is `tools/b7_audit/evidence.jsonl.gz`** (gzip, mtime 0, byte-deterministic), not the plain
   `.jsonl` of §8; records keep the oracle status and the sorted item reason prefixes (text before
   `@offset`), the verbatim items stay in the uncommitted `.cache/b7_audit/oracle-items.jsonl`.
2. **Tiered alc, class-sampled cells** (§7.1, §10): the parser and the oracle check every cell; alc
   compiles a cell only when it is a seed, its parser/oracle outcome is not clean+pass, its intended
   vector excludes an assignment, or it is its (role, family, placement) class's representative. Every
   other cell is `class-sampled` and is judged through its representative, `UNCHECKED` (`representative
   vector mismatch`) when the representative's alc acceptance differs from the intended vector.
   `run --only X` re-observes parser and oracle for EVERY cell and compiles only the slice; the other
   measured cells read the alc cache (a miss is exit 2).
3. **Group witnesses** (§8 Fixtures): one alc probe, corpus case or SILENT test per (family, base
   placement, verdict) group, made from its lexicographically first cell, not one per cell; the base
   placement drops `+comments`, `+not`, `@Name` and the operator class.
4. **`:error` GAP witnesses**: the GAP corpus cases use tree-sitter's `:error` attribute (an error exists,
   no recovery tree pinned); syntax over-accepts witnesses stay pinned as trees.
5. **`empty_statement`**: an arm's lone `;` read as an `empty_statement` is CONSISTENT only where the
   oracle normalises it (a top-level `statement_block`); in nested and split hosts the cell is SILENT,
   and the report files those SILENT cells under their own family `empty-statement-ownership`, ranked in
   the SILENT tier with "ruling first": B7b decides who owns the `;` before it is a fix.
   **Superseded 2026-10-07 by the user ruling (Option A, B7b-0):** the arm's `;` is its own `empty_statement` in every
   host; the oracle lowers it as the preceding statement's separator (`arm-terminator`) and the family is gone.
6. **Assertions close cannot-validate cells** (§7.2, §7.3): a fresh holding assertion turns an oracle
   `cannot-validate` into CONSISTENT with detail `assertion-closed: <refusal reasons>`; a failing one is
   SILENT. Each row also records `holds`, its truth at its fingerprints, so `assert --refresh` can
   re-fingerprint unchanged rows after a parser or oracle change and list flipped ones. The committed
   matrix is valid only at the recorded hashes.
7. **Link names**: `RunPageLink` and `ColumnFilter` have no registry container (page action, query
   column); they are covered by the committed link-keying alc cases as seeds, and the generated link
   variants cover only names sharing the witness template's value grammar.
8. **Qualifier rows** (`.`, `::`, `..`, `:`) generate no placements (§6 defines none); the matrix lists
   them under "Not probed". Every other registry row without evidence is listed there with its real
   skip reasons (`placements.skipped_for`); not every host is probed at every placement.
9. **Multi-host registry rows**: the `route` column may hold an explicit host list; the first host is the
   witness the template targets, and the row's reason argues why the others reach the key through the
   same rules or scanner states.
10. **The `plain` column**: the registry carries the directive-free valid filling of each hole, compiled
    ACCEPT and parsed clean; it is the typed control of §7.1. A row with no parseable template is a
    `TEMPLATE-GAP:` row, one template-level GAP.
11. **Sites** (§8 Defect families, ranking): a family's sites are the production walk's class-matched
    counts: the (host, class) pairs of `production_shapes.json` that match a (host, class) pair of the
    family's defective cells, the class read off the placement shape (`report.SHAPE_CLASSES`).
    `terminated-unit` sites are shown per host, never weighted; a `;` closing a split statement host
    (58 sites, `seeds._terminates`) is a terminated unit, not `sep-after`.

## Rev 2 changes (gpt-6.1-sol review of rev 1)

1. Census of all structural punctuation with roles and recursion/caller context; lexical punctuation
   listed, not dropped; seed inventory for what the grammar cannot show (P1-1).
2. Occurrence, boundary edge, host route and probe variant separated; per-edge continuation table
   (P1-2).
3. `OK-NEG`/`OVER` replaced by configuration vectors, `MIXED`, and syntax-vs-semantic `REJECTED` (P1-3).
4. `SILENT` reproducers kept out of the quick-tier corpus in a dedicated pytest (P1-4).
5. Continuation placements: prefix mechanism, whole operand, grouping chains, `in/is/as`, typed
   templates, signed literals, `semi-in-arms` restricted and item 39's following statement kept (P1-5).
6. Separator placements extended and written literally with validity vectors (P1-6).
7. `OK` renamed `CONSISTENT`; refusals recorded by reason; internal errors fail; independent structural
   assertions with fingerprints and a mutation check (P1-7).
8. Ranking by deduplicated families, defective production sites and dependencies; `UNCHECKED` separate;
   B12/B13 overlap assigned (P1-8).
9. Committed canonical evidence; deterministic report; `run --check` against pinned tool identity and
   corpus manifests (P2-9).
10. Cost recomputed from the design (P2-10).
