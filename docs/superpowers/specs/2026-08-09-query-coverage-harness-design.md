# Query-Coverage Harness — Design

**Date:** 2026-08-09
**Status:** Approved, not yet implemented
**Scope:** Build the harness. No grammar or query corrections in this work.

## Problem

The project has three quality gates, and a whole class of defect walks past all of them.

| Gate | What it proves |
|---|---|
| `parse-al-parallel.sh` | No ERROR nodes across 15,358 production files |
| `tools/tree-harness.sh verify` | Every file's s-expression tree is byte-identical to a saved baseline |
| `tree-sitter test` | 1,451 hand-written corpus trees still match |

None of them proves the tree actually *represents* the source, or that a consumer can *reach* a value through a query. Two real bugs demonstrate the gap:

1. **`begin`/`end` dropped inside `#if`.** Until 4.0.0 the depth > 0 path fell through to an anonymous `kw('begin')`. `kw()` builds a `token(PATTERN)`, and tree-sitter renders anonymous pattern tokens as hidden `aux_sym_*` symbols with `.visible = false`. The keyword was lexed and then dropped from the tree. Zero errors, tree "stable", CST not lossless over the source, keyword unhighlightable inside every `#if`.

2. **`PREPROC_SPLIT_END` stopping on a trailing comment.** The run silently reparsed as a `call_statement`. Clean error count, wrong tree, invisible to every gate.

`tree-harness.sh` is structurally blind to the first case: it hashes the output of `tree-sitter parse`, which contains named nodes only (`tools/tree-harness.sh:72-76`). No hash can change when a hidden token is dropped.

A third instance was found while designing this harness, and is documented below as the worked example.

## Worked example: the dropped `operator` field

`grammar.js:3434-3438` and `grammar.js:3446` declare:

```javascript
assignment_statement: $ => prec.dynamic(10, seq(   // 3434
  field('left', $._expression),
  field('operator', $._assignment_operator),
  field('right', $._expression)
)),

_assignment_operator: $ => token(choice(':=', '+=', '-=', '*=', '/=')),   // 3446
```

Three more rules carry the identical defect, all verified against `src/node-types.json`, which gives every one of them only `left` and `right`:

| Rule | Line | Hidden token wrapped by `field('operator', ...)` |
|---|---|---|
| `assignment_statement` | `grammar.js:3436` | `$._assignment_operator` |
| `assignment_expression` | `grammar.js:3442` | `$._assignment_operator` |
| `is_expression` | `grammar.js:3764` | `kw('is', 5)` |
| `as_expression` | `grammar.js:3769` | `kw('as', 5)` |

`_assignment_operator` is a `token(choice(...))` — a hidden token. The field wrapping it is therefore dropped. Parsing `i := 1; i += 2;` gives:

```
sexp:     (assignment_statement left: (identifier) right: (integer))
children: [('identifier', 'i'), ('integer', '1')]
child_by_field_name('operator') -> None
```

`src/node-types.json` lists only `left` and `right` for `assignment_statement`. Consequences:

- `:=` versus `+=` is unrecoverable from the tree. Verified: `i := 1` and `i += 2` both parse to `(assignment_statement left: (identifier) right: (integer))`. All five of `:=` `+=` `-=` `*=` `/=` collapse into one indistinguishable node, and since the bytes belong to no node there is no text fallback either. `i += 2` means `i := i + 2`, so a dataflow consumer is silently wrong. The `is_expression`/`as_expression` instances below are milder: their node types differ, so the type already encodes the operator.
- `queries/highlights.scm:155` (`":=" @operator`) can never match an assignment. It matches only the plain-string `':='` inside `for_statement` (`grammar.js:3663`). Verified: running that pattern over `for i := 1 to 5 do x := i;` returns exactly **one** capture, `parent = for_statement`. The assignment's `:=` is uncapturable.
- The bytes appear in no node at all: gap-scanning the sample yields `GAP 52 56 b' := '` and `GAP 60 64 b' += '`.

Measured frequency: 2,692 `:=` gaps across the six-file sample. Zero errors, stable tree, near-dead query.

**Note what this example is not.** The `:=` pattern is *mostly* dead, not *fully* dead — any for-loop keeps it matching. A "pattern matched zero times corpus-wide" check therefore sails right past it. This case is caught by detector 1 (byte gap) and detector 3 (dropped field), not by detector 6. Detector 6 finds only fully-dead patterns, which is a different and also worthwhile invariant.

### Self-tests

Two detectors have a known-answer check on their first run. If either comes back clean, that detector is broken rather than the grammar being healthy.

- **Detector 1** must report the `:=`, `record`, `field`, and `tabledata` gap clusters.
- **Detector 3** must report exactly the four rules in the table above. A set-level implementation returns zero here — see the warning in its section.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Ground truth | The source bytes themselves | No goldens to maintain; a dropped token becomes a byte gap automatically |
| Query layer measured | Harness-owned `inventory.scm` **and** the shipped queries, reported separately | The shipped queries were written for editors, not exhaustive extraction; mixing them produces false holes |
| Corpus pinning | Committed manifest; corpus stays external and gitignored | Keeps Microsoft base-app source out of the repo |
| Output | Clustered JSONL + committed baseline + markdown summary | `run` prints only NEW/FIXED clusters, so the backlog does not drown the signal |
| Baseline counts | Ratchet downward automatically on every run | Without it, a cluster fixed to 0 and later regressed to any value below its accepted count passes silently |
| Runtime | Python, loading the local `al.dll` via ctypes | Verified working, ABI 15; direct byte access; matches existing `parse_bug_finder.py` tooling |

### The tautology caveat

With ground truth set to the source bytes, comparing a query capture's text to the file bytes at that capture's own byte range **always passes**. It is not an assertion. Only two kinds of check are non-vacuous here:

- **Existence and coverage** — every lexical occurrence of a construct has a covering node or capture.
- **Cross-derivation agreement** — two independent derivations of the same fact disagree.

`inventory.scm` must not be implemented as extract-then-compare-to-itself. Its job is to produce the artifact and to feed detector 5.

## Layout

```
tools/query-coverage/
  qc.py                    # single entry point
  manifest.tsv             # committed: object_type \t path \t sha256 \t bytes \t reason
  inventory.scm            # harness-owned extraction queries
  baseline.json            # committed: accepted current state, cluster fingerprints
  reports/                 # gitignored run output (findings.jsonl, summary.md, inventory/*.json)
```

## Commands

```bash
python tools/query-coverage/qc.py select     # rebuild manifest by set-cover over node-type vocabulary
python tools/query-coverage/qc.py run        # parse + all detectors, diff vs baseline
python tools/query-coverage/qc.py run --all  # ignore baseline, emit the full picture
python tools/query-coverage/qc.py accept     # promote the current report to baseline
```

### Build freshness

`run` verifies the loaded parser matches the current sources before doing anything else.

Record a sha256 stamp over `grammar.js` + `src/scanner.c` at build time and compare on each run. **Do not use mtime.** Git rewrites mtimes in arbitrary order during checkouts and branch switches on Windows, so an mtime comparison produces both false alarms and false all-clears.

The same stamp lets `run` skip the rebuild when nothing changed. `src/parser.c` is 26 MB; an unconditional rebuild puts a full compile inside every fix-iterate cycle for no reason.

Pin the `py-tree-sitter` version in the harness's requirements. `Language(int)` already emits a `DeprecationWarning` on the installed version; the verified loading recipe has a shelf life.

## Corpus selection

**Greedy set-cover over per-file node-type vocabulary.** Parse the whole corpus once (this already takes about 37 seconds via the existing tree-harness path), record the set of node types each file produces, then greedily pick files that add the most previously-unseen types until no file adds anything new. Expect 100–300 files. Use parent→child type pairs rather than bare types if the flat version saturates too early.

Three things `select` must pin down, or it is not reproducible:

- **Deterministic tie-breaking.** Ties broken by dict iteration order make `select` non-reproducible, which churns the manifest, which invalidates every baseline count. Order candidates by (gain descending, path ascending) and take the first.
- **Vocabulary means *named* node types.** The tree-harness path yields CLI s-expressions, which contain named nodes only. Set-cover over observed output covers the named types the corpus exercises — not "every node type the grammar can emit". The shortfall is measured by the never-observed report below rather than assumed away.
- **Multi-object files.** A `source_file` can hold more than one object declaration, and 30 files carry no type suffix at all. `manifest.tsv`'s `object_type` column holds a comma-separated list of every object type in the file, not a single value.

**Never-observed node types report.** A free by-product of the same parse: every type in `src/node-types.json` appearing in zero of the 15,358 files. That set is either dead grammar or a construct with no production coverage. Both are worth knowing, and it quantifies how far the corpus falls short of the grammar.

**Not biggest-file-per-type.** Measured: the biggest Query file (13.6 KB) produces zero findings, and the biggest Table spends 580 KB repeating `record` and `:=` thousands of times. Big means repetitive, not diverse. Roughly 20 files cannot exercise the ~36 complex property rules, the ~12 split-construct rules, or the long tail of 391 named node types. Keep biggest-per-type as a supplementary stress row, not as the coverage strategy.

**Derive object type from the tree root, not the filename.** BC.History suffixes are inconsistent: 527 `*.PermissionSet.al`, 276 `*.permissionset.al`, 15 `*.Permissionset.al`, 25 `*.PermissionsetExt.al`, 2 `*.permissionSetExt.al`, plus 30 files with no type suffix. The file is being parsed anyway; the root child's node type is authoritative and free.

`manifest.tsv` records the sha256 of each selected file. `run` aborts loudly if a file is missing or its hash drifted, rather than silently reporting against a different corpus.

## Detectors

### 1. Lossless coverage

Walk every leaf node (`child_count == 0`) in byte order. For each adjacent pair, assert the interstitial bytes contain nothing but whitespace. Non-whitespace bytes belonging to no leaf mean a token was lexed and dropped.

Implementation constraints, each of which was hit during design verification:

- **Whitespace means `isspace()` or `U+FEFF`.** The `extras` array (`grammar.js:128-138`) declares both `/\s/` (line 129) and `/\uFEFF/` (line 137). Python's `str.isspace()` returns False for the BOM, so a naive check flags offset 0 of every BOM'd file. Decode as UTF-8 and test `ch.isspace() or ch == '\uFEFF'` (written with the escape, never as a literal BOM in source). Keep this definition slaved to the `extras` array.
- **Walk all children, not named children.** Anonymous string tokens such as `';'` are visible leaves and legitimately provide coverage.
- **Exclude ERROR node ranges.** Error recovery both emits ERROR leaves covering garbage and drops adjacent tokens unpredictably. Gaps inside ERROR ranges belong to detector 2; mixing them makes detector 1's clusters unstable.
- **Fingerprint carries no byte offsets.** Key on (lowercased gap text with internal whitespace collapsed, enclosing named node type). Raw text leaks indentation into the key — `'else\r\n            if'` was observed as a distinct cluster. Offsets belong in the examples, not the key, or every corpus refresh churns the whole baseline.

**Expected day-one volume: large.** Measured 7,478 gaps across the 6 biggest clean files, forming roughly 30 clusters. `grammar.js` contains 267 `kw(` occurrences on 260 lines, of which roughly 76 sit inside an `alias(kw(...))` keyword rule and drop nothing; the remainder are inline uses, and every inline use drops its bytes on every clean parse. Top clusters in that sample: `record` (2,959), `:=` (2,692), `fieldelement` (668), `field` (281), `else … if` (40). Corpus-wide, expect 50–150 clusters.

This is why the baseline freeze is mandatory rather than merely convenient. It is also not all noise — the `:=` cluster is the worked example above, and `_tabledata_keyword` (`grammar.js:1028`, used un-aliased at `grammar.js:1032`) produces `NON-WS GAP 36-47: b' tabledata '` on `Permissions = tabledata Foo = rimd;` with `has_error: False`.

### 2. ERROR / MISSING census

Per object: every ERROR and MISSING node, its enclosing named construct, and three lines of source context. Straightforward, and it keeps error-recovery artifacts out of detector 1.

### 3. Dropped-field audit (static)

For every `field('name', ...)` declaration, check that the field name appears on **that rule's own node type** in `src/node-types.json`. A field wrapping a hidden token silently disappears; this is the general form of the `operator` bug.

**The check is per-owning-type, never set-level.** The field name `operator` exists in `node-types.json` on six other types — `additive_expression`, `comparison_expression`, `in_expression`, `logical_expression`, `multiplicative_expression`, `unary_expression`. An implementation that asks "does this field name appear anywhere in node-types.json" reports zero findings for `operator` and the detector is dead on arrival. This is what the detector-3 self-test guards.

**Read `src/grammar.json`, not `grammar.js`.** The compiled grammar is machine-readable JSON with `FIELD` and `ALIAS` nodes explicit, so the audit needs no JavaScript parsing and gets the rule→field ownership directly.

**Scope v1 to visible, un-aliased rules; report the rest as skipped.** Resolving the owning type is not always trivial:

- Fields declared inside *hidden* rules (`_procedure_header`) surface in `node-types.json` under whatever visible rules reference them. Matching against a type literally named `_procedure_header` is a false positive for every such field.
- Fields inside rules *aliased at their use sites* (`alias($.permissions_property, $.property)`, `grammar.js:500`) surface under the alias target.

Emit a `skipped: hidden or aliased rule` list rather than guessing. All four known instances are visible un-aliased rules, so the cheap scope catches everything currently known while staying honest about its blind spot.

**Known blind spot, with a cheap dynamic complement.** A field whose content is a `choice()` mixing visible and hidden alternatives stays in `node-types.json`, yet is silently absent on the instances that took the hidden alternative. Static analysis cannot see this. During the corpus walk, flag any node where a field marked `required: true` in `node-types.json` returns `None` — that catches it at almost no cost.

The static half runs without parsing anything and costs a single pass over two files.

### 4. Reserved-keyword-as-identifier audit

Flag any leaf of type `identifier` whose text case-insensitively equals a hard-reserved word: `begin`, `end`, `then`, `else`, `until`, `repeat`, `case`, `exit`, `var`, `procedure`, `trigger`.

Exclude the deliberate `keyword_as_identifier` whitelist (`grammar.js:4148-4159`): `field`, `key`, `value`, `separator`, `dataset`, `type`, `version`, `action`, `table`, `assembly`. Those are legitimate identifiers in AL and are whitelisted on purpose — see `.claude/rules/contextual-keywords.md`.

`end` appearing as a call-statement identifier is bug 2's exact signature. Without this detector the harness would miss one of its own two motivating examples: that misparse leaves no byte gap (every byte is covered by an `identifier` leaf and punctuation) and produces no ERROR.

Two tuning points. Carry the enclosing node type in the fingerprint and exclude member-access position, or `x.End` — a DotNet or interface member legitimately named `End` — fires on every use. And validate the hard-reserved list with `al compile` probes before trusting it, `exit` and `var` especially: AL is lenient about contextual keywords, and per this project's own doctrine the compiler is the only ground truth. Day-one false positives land in the baseline either way, so this is tuning, not a blocker.

### 5. Independent lexer and anchor counting

**A mini-lexer for strings, comments, and directives only.** AL's rules here are small and unambiguous: `'...'` with `''` escaping, `//` to end of line, `/* */`, and `#`-prefixed directive lines. This is the one component that can catch parser *tokenization* errors, because it derives token boundaries without consulting the grammar. Write it from the AL language rules, not by transliterating `grammar.js` — a transliteration shares the bug and detects nothing.

**Anchor counting, not construct extraction.** Per file, count anchor occurrences falling outside comments and strings, and compare against node counts from the tree. On mismatch, localize by nearest-offset diff.

**The anchor table is part of the spec, not an implementation detail.** "Compare against the corresponding node counts" diverges the moment anyone writes it: `field(` in AL source is not only `field_declaration` — it is also the field reference inside link properties (`SubPageLink = X = field(Y)`), inside `CalcFormula`/`TableRelation` (`where(X = field(Y))`), and potentially a `.Field(` method call. A naive `field(` versus `field_declaration` comparison mismatches on every page carrying a link property. That is permanent noise, and the likely "fix" is an implementer subtracting fudge factors until it balances.

Commit an explicit table: anchor → lexical rule → the exact set of node types whose counts sum to the expectation. Prefer 1:1 mappings against visible keyword nodes wherever one exists, because those are exact and self-explaining:

| Anchor | Lexical rule | Expected node count |
|---|---|---|
| `procedure` | word boundary, not preceded by `.` | `procedure_keyword` |
| `trigger` | word boundary, not preceded by `.` | `trigger_keyword` |
| `key(` | word boundary, not preceded by `.` | `key_declaration` |
| `value(` | word boundary, not preceded by `.` | `enum_value_declaration` |
| `action(` | word boundary, not preceded by `.` | `action_declaration` |

Every shipped anchor turned out to be 1:1 against a node type verified to exist. The anticipated multi-type sums were not needed — but the table stays committed and reviewable, because the reason they were anticipated is real.

**`field(` is excluded in v1**, and this is the case that justified writing the table down. A field reference inside a `where()` clause produces no node at all: parsing `TableRelation = Other.Code where(X = field(N))` bottoms out at `where_condition`, whose children are `identifier X`, `=`, `(`, `identifier N`, `)`. The `field` keyword is a bare `kw()` and is dropped entirely — detector 1 reports it as a byte gap, alongside `where`. So one `field_declaration` plus one where-clause reference counts 2 lexically and 1 structurally, and no node-type sum reconciles that, because the second occurrence has nothing to count.

Adding `where_condition` to the sum would be the tempting fix and is wrong: `where(X = 5)` is a `where_condition` containing no field reference, so it trades a known gap for a wrong number. The anchor is excluded and the exclusion is logged, per the no-silent-caps rule.

An earlier draft of this table named `field_reference` and `enum_value`. Neither exists in `src/node-types.json` — which is why the verification step below is part of the task rather than an afterthought.

Validate each mapping once at `accept` time, then treat drift as a finding.

Counting carries no nesting state, so it cannot desync. This matters: a full brace/`begin`-`end`-tracking shadow extractor loses sync precisely on `preproc_split_*` files, where `begin`, `end`, and the terminating `;` are deliberately split across `#if` branches. Its worst noise would land exactly where this project's bugs live. The construct-extraction half of the original design is therefore cut.

### 6. Shipped-query audit

Two crisp invariants, replacing the noisy "node types no shipped query captures" list. Structural nodes are legitimately uncaptured by highlighting, so that list is mostly false positives.

- **Keyword and operator coverage.** Every `*_keyword` node and every visible operator token must receive a capture from `queries/highlights.scm`. Directly checkable against the documented 83-keyword architecture. "Operator token" needs an explicit definition rather than intuition — take it as the anonymous entries in `node-types.json` whose text is entirely punctuation, minus the structural delimiters `;` `,` `(` `)` `{` `}` `[` `]` `.` `:`. Write the resulting list into the harness so it is reviewable.
- **Dead patterns.** Any shipped-query pattern matching zero times is reported. Run this over **all 15,358 files**, not the manifest subset — a manifest-only run false-flags patterns for rare constructs that set-cover happened to satisfy from a single file. A query pass over the full corpus is affordable.

Fingerprint dead patterns on a hash of the pattern's **source text**, never its index. Indices shift on every `.scm` edit and would churn the baseline wholesale.

This detector finds only *fully* dead patterns. `queries/highlights.scm:155` is not one of them — see the note in the worked example.

This detector is informational and never fails the run.

## inventory.scm

A harness-owned extraction query file producing a semantic dump per object: object id/name/type, every property name + value + byte range, fields with id/name/type/properties, keys, triggers, procedures with parameters and return type, variable declarations, enum values, and the page layout/actions tree.

It serves two purposes: it feeds detector 5's node counts, and it is the artifact a human or an LLM reads when writing corrections.

**Meta-check against `node-types.json`.** Enumerate the child types of `property`'s `value` field and the element types of each section body, and fail the meta-check if any lacks an inventory pattern. Complex properties follow no naming convention — only two rules match `*_property`, while the rest are value-shape rules such as `ml_value_list` and `table_relation_value` — so a new complex property would otherwise slip into the grammar and leave `inventory.scm` silently stale. That is the same staleness failure this harness exists to eliminate.

## Output

**`reports/findings.jsonl`** — one finding per line, stable sort order. Each record carries the cluster fingerprint, category, object type, file path, byte offset, line/column, enclosing node type, and a source snippet.

The first line is a **provenance header**: build stamp hash, manifest hash, `py-tree-sitter` version, harness version. Three lines of code, and it is what makes any two reports comparable — which is the entire point of a run-it-over-and-over harness.

**`reports/summary.md`** — clusters with counts and up to three examples each, grouped by detector, most frequent first.

**`baseline.json`** — accepted cluster fingerprints with their counts, plus the manifest hash they were accepted under. `run` refuses to diff a baseline accepted under a different manifest, which closes the count-churn interaction between `select` and the exit rule.

### Fingerprints

Every detector needs one, or its findings cannot be clustered or baselined. Detector 1's is specified in its own section; the rest:

| Detector | Fingerprint key |
|---|---|
| 2 — ERROR/MISSING | (enclosing construct type, ERROR or MISSING symbol) |
| 3 — dropped field | (rule name, field name) |
| 4 — reserved keyword | (keyword, enclosing node type) |
| 5 — anchor count | (anchor, file path) |
| 6 — dead pattern | (query file, sha256 of the pattern's source text) |

No fingerprint contains a byte offset or a pattern index.

### Exit codes and the ratchet

| Code | Meaning |
|---|---|
| 0 | No new cluster, no cluster above its ratcheted count |
| 1 | A regression: new cluster, or count above the ratchet |
| 2 | Corpus broken: a manifest file is missing or its sha256 drifted |
| 3 | Stale parser: build stamp does not match `grammar.js` + `src/scanner.c` |

CI must be able to distinguish "corpus broken" from "regression found", hence the separate codes. `run --all` reports everything and exits 0 regardless of findings; it is a reporting mode, not a gate.

**The baseline ratchets downward automatically.** Whenever a run observes a *lower* count for an existing cluster, it rewrites that count in `baseline.json` immediately and prints the ratchet it applied.

This is deliberate, and it is the one place `run` mutates a committed file as a side effect. Without it there is a hole: a cluster at 100 gets fixed to 0 and is reported FIXED with exit 0; it later regresses to 80; the baseline still reads 100, so 80 < 100 and the run passes. The regression stays invisible until somebody remembers to re-`accept`. Ratcheting means the bar only ever moves down, so that regression fails the very next run. The cost is a modified `baseline.json` in `git status` after a run that improved something — expected, and the printed ratchet lines say exactly why.

`accept` remains the only way to raise a count or admit a new cluster.

## Failure model

Report-only initially. The first `accept` freezes today's holes into `baseline.json`, which makes the harness a regression net immediately while the backlog is worked down separately. Correcting the findings is explicitly out of scope for this work.

## Known limitations

Stated plainly rather than discovered later. Updated post-implementation (final whole-branch review, finding F3): a seventh detector, **corpus**, was added to close the node-type-disappearance gap this section originally missed entirely, and two of the three original bullets below needed correction once the other six detectors were actually built and measured against the real grammar.

Not caught by anything in the harness:

- **Precedence and associativity misparses inside expressions.** `a + b * c` grouped wrongly covers every byte correctly.
- **Scanner over-consumption**, where a string or comment token swallows adjacent code — unless detector 5's lexer is genuinely independent, which is why that constraint is called out above.
- **Wrong-parent attachment that also preserves every node's type.** A property landing under the wrong field when preprocessor branches interleave produces no gap, no error, and correct byte coverage. This is narrower than it first looks: detector 4 (reserved-keyword-as-identifier) *does* catch the `case`/dangling-`else` mis-association found while building this harness, because that misparse degrades a keyword into a plain `identifier` — a type change, not just a wrong parent. The limitation is real only for attachment errors where every node keeps its original type.

Closing these needs structural assertions against expected trees, which is what `test/corpus/` already provides. The harness complements those tests; it does not replace them.

Two things the original six-detector plan did not anticipate, both surfaced by the final review:

- **A named node type still declared in `src/node-types.json` can stop being produced by anything in scope while every byte stays covered.** Detector 1 is byte-coverage-based and cannot see this. `corpus.never_observed` (§ Corpus selection) already computed the right set from day one; it just was not turned into a gating Finding until this correction. It is scoped to what the manifest actually exercises — 357 of 391 named types — so it says nothing new about the other 34, which are dead grammar or genuinely uncovered constructs either way. Two things that look like this trigger are not, in fact, caught by it: a keyword rule reverting from `alias(kw('word'), 'word')` to a bare `kw('word')` still yields a childless `(x_keyword)` leaf per `CLAUDE.md`'s keyword-shape table, so the type stays observed; and a rule inlined to a bare string literal removes the type from `node-types.json` entirely, so `never_observed` no longer iterates it (caught only incidentally, when a shipped `.scm` names the type by hand and `tree_sitter.Query` raises `QueryError` on the now-unknown type). Nor is the historical `begin`/`end` dropped-inside-`#if` bug an instance of this class — `begin_keyword` was still emitted at depth 0, so it was never in the never-observed set; that bug is detector 1's byte-gap catch.
- **Detector 3's dynamic half is narrower than "every field."** It flags a field marked `required: true` in `node-types.json` that returns `None` on a real instance — 241 of the 392 field declarations. An *optional* field whose content is a `choice()` mixing visible and hidden alternatives passes the static check (the name is present) and is never inspected dynamically. That is the majority of the grammar's fields, not an edge case.
