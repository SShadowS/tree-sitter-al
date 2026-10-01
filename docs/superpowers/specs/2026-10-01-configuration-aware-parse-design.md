# Configuration-aware parsing: scope and design (roadmap A7)

**Status:** approved section by section by the user, 2026-10-01. Written spec awaiting review.
**Roadmap:** A7 decides the scope; F0 and F1a–F1d implement it (see §8).
**Inputs:**
- the consumer inventory (`.superpowers/sdd/a7/consumers.md`, summarised in §1);
- three independent model reviews: gpt-6-sol, gpt-6-astra and gemini-3.8-flash (`.superpowers/sdd/a7/*-review.md`).

## 1. Problem and consumers

The grammar parses every `#if` branch into one tree: the native all-branches CST. Three
things go wrong with that:

- **Some files have no honest single tree.** EDocumentDE (deferred item 10) is a split
  `add*` layout header whose body stays open across `#endif`. The attempts cost +835 to
  +2,270 LR states, or `generate` never finished.
- **Some trees show only one configuration.** In the one-reading families (10 production
  records), the tree reflects one configuration's nesting. The oracle cannot validate the
  else-led `open_statement` arms either.
- **Tokens can depend on the configuration.** G7: `-1` is a signed literal only before
  `;`, `,`, `#` or EOF.

The consumer inventory (24 consumers) found:

- **Almost every consumer depends on the all-branches tree.** That covers editors, diff
  tools, comment-audit and al-sem's union analysis.
- **No consumer configures a tree today.** Where a configured view is wanted, it is wanted
  *with original positions*:
  - LethAL R214: mutants land in inactive arms, *and* active sites are lost because
    conditional parents fail statement-position checks;
  - al-sem: confidence;
  - graphify: condition tags.
- **Only al-perf would take a plain configured tree.**
- **Four consumers silently lose `#if` content:** al-differ, code-graph-rag, DevOpsWorker
  and graphify. This is a traversal problem.
- **Version drift is large.** About ten active consumers predate 4.0.0.

## 2. Three products, three claims, three ledgers

| Product | Claim | Ledger |
|---|---|---|
| **P1, native all-branches CST** (today's grammar) | Every branch is present. Each node's parentage, fields and tokens are true for the constructs it represents. | native-CST debt: `docs/deferred-work.md`, `production-classes.tsv` `debt(B*)`/`debt(C1)`, plus the existing gates |
| **P2, configured parse** | For one requested symbol set, the tree is identical to a parse of that configuration's text, at the original byte positions. | configured-correctness ledger (new; §7) |
| **P3, coverage and correspondence** | For one symbol set: how each P1 node's source is covered, and how P1 nodes relate to P2 nodes. | correspondence ledger (new; §7) |

**Rules:**

1. **P2 never closes P1 debt** (roadmap F1 rule). EDocumentDE reports two separate results:
   P2 must succeed, and P1 stays open until a native representation exists or a time-boxed
   experiment rules one out.
2. **The oracle checks consistency, not correctness.** Its flat reference uses the same
   grammar, so correctness evidence for P2 comes from compiler-backed witnesses
   (`tools/alc_probe`).
3. **One grammar.** P2 parses masked text with the full grammar. A slim grammar is a
   measurement spike only (F1d, §6).

## 3. The resolver core: `al_preproc` (C)

**Decision: C.** It is a small byte-level library that lives in the repo next to
`src/parser.c` and has no tree-sitter dependency. C builds in every binding's existing
toolchain (node-gyp, setuptools, cargo `cc`, cgo, Swift, emscripten), and the repo
already ships, fuzzes and ASan-tests C. The Python `tools/config_oracle/directives.py`
stays the **reference** and the test oracle. There are never three independent ports.

### Input

- `source`: UTF-8 bytes; a leading BOM is allowed. Any other encoding is the caller's
  responsibility. v1 refuses it with `encoding-unsupported`.
- `env0`: the initial symbol set, given explicitly. Symbols are case-sensitive
  (alc-verified). The core does no filesystem lookup. A separate helper parses
  `app.json` `preprocessorSymbols`.
- `limits`: maximum nesting depth, maximum condition-expression depth, maximum bytes, and
  a cancellation flag that is polled at least once every 1,024 lines.

### Output (`al_resolution`)

| Field | Meaning |
|---|---|
| `masked` | Same length as `source`. These bytes become `0x20`: inactive arms, and the whole `#if`/`#elif`/`#else`/`#endif` lines including any trailing `//`. These are kept: `\r`, `\n`, the leading BOM, and active `#define`/`#undef`/`#pragma`/`#region`/`#endregion` lines. |
| `active` | Sorted intervals: the original bytes that reach the parser. |
| `directives[]` | kind, `#` offset, line span, parsed condition AST, symbol (for define/undef) |
| `groups[]` | for each `#if` group: its arms and the arm chosen under `env0`. `#elif` is first-match, and choosing no arm is legal. |
| `extras[]` | the active extra events in order, including the environment after each `#define`/`#undef` |
| `status` | `ok`, or a failure code plus a byte offset |

### Failure taxonomy: fail closed

The codes carried over from the reference are:

- `unknown-directive`
- `empty-condition`
- `unsupported-condition`
- `unsupported-condition-token` (this includes `&&`/`||`, consistent with roadmap B2)
- `block-comment-on-directive`
- `trailing-token`
- `duplicate-else`
- `elif-after-else`
- `unbalanced-if`
- `directive-after-code`
- `malformed-define`
- `unterminated-active-comment`
- `unterminated-active-string`

The new codes are `limit-exceeded`, `cancelled` and `encoding-unsupported`. A failure
yields **no** masked buffer: no partial output, and no fallback to P1.

### Lexical rules

These are compiler-probed; see `docs/preproc-directive-semantics.md`.

- **Active text:** `/* */`, `//` and verbatim `@'…'` are tracked, so a directive-looking
  line inside one of them is text.
- **Inactive text:** only lines that start with a directive are recognised. Unmatched
  quotes and comments are ignored.

### Not in the core

- **Symbolic "which configurations?" analysis.** That is a separate, bounded API with an
  explicit `unknown`, and it comes later.
- **`discover()`-style enumeration.** Single-configuration calls never enumerate.

### Conformance

The vectors live in `tests/preproc-vectors/*.json`. Each holds the input bytes, the
symbols, and the expected masked SHA-256, active intervals, groups, extras and status.

**Seeds:**

- every `tools/alc_probe` case, which anchors the vectors to the compiler;
- the oracle fixtures;
- edge cases:
  - CRLF;
  - no final newline;
  - a BOM, and the doubled BOM (item 6, recorded as an open case);
  - a G7 `-1` before a kept `#pragma`;
  - an inactive unterminated string;
  - nesting at the limit.

**Checks:** CI runs the vectors against both Python and C. C also gets an ASan fuzz job
and a Python-vs-C differential run.

**Independence:** expected values come from the Python reference **and** alc probes,
never from C alone. Where alc disagrees with Python, alc wins and Python is fixed.

## 4. The configured parse (P2)

### Call shape

The call has the same shape in every binding:

```
configured.parse(source, symbols, *, limits, old=None, edits=None) -> Configured
Configured { source (immutable original bytes), revision, symbols, grammar_version,
             resolver_version, resolution, masked, tree, outcome }
```

### Outcomes

Each outcome is reported separately and never folded into another:

- `resolution-failed` (with the core's code; there is no tree);
- `cancelled`;
- `parsed-clean` (`has_error` is false, which is **not** a validity claim);
- `parsed-recovered` (`has_error` is true; the tree is returned with its error nodes
  listed).

Compiler validity is always `unknown` from the API.

### Positions and text

- **Positions:** every node keeps its original byte offset and its row/column in bytes,
  because the masked buffer has the same length as the source.
- **Text:**
  - `node_text(n)` reads the **original** source.
  - `active_text(n)` returns only the active bytes inside `n`'s span.
- **Unsafe spans:** a parent's span may enclose masked bytes, so it is not a safe
  replacement region. Use `is_span_fully_active(n)` to check.

### Coordinates

Bytes are the reference unit. Each binding converts, and documents the conversion:

- **Rust:** bytes.
- **Python:** `str` index or bytes.
- **JS/WASM:** UTF-16 code units, converted from the **original** source and never from
  the masked one. Blanking a multibyte inactive character shifts the UTF-16 indices of
  everything after it.

### Incremental updates

v1 is correct first. It may only be replaced by a faster scheme that passes the same tests.

1. Apply the edit to the original source, which gives a new revision.
2. Re-resolve the whole file. This is O(file), and cheap relative to the parse.
3. Diff the old masked buffer against the new one, and turn each changed range into a
   `tree.edit` on the old tree. Then call `parse(new_masked, old_tree)`.
4. If resolution fails, report `resolution-failed` and discard the old tree. A stale tree
   is never returned.

**What triggers what:**

- A change of symbol set, grammar version or resolver version forces a fresh parse.
- The masked diff covers every other case: edits to directives, `#define`, comments,
  strings, newlines and inactive text. An edit inside an inactive region is a masked no-op.

**Requirement:** the incremental tree equals the fresh tree over the complete cursor walk
(anonymous tokens, fields, spans and `has_error`). This must hold across chained edits and
symbol switches. `tools.perf incremental` gains a configured mode to check it.

**Cache key:** the source revision, the symbols, the grammar version and the resolver
version.

### Not in scope

Parsing all configurations at once, and merging configured trees. P3 relates P1 to P2
without merging them.

## 5. Coverage, correspondence and traversal (P3 and F0)

### Axis 1: source coverage

Coverage is exact for one requested symbol set:

`coverage(p1_node, resolution) -> active | inactive | mixed | not-applicable | unknown`

- **What is counted:** a node's significant terminals, not its bounding span. Directive
  lines are metadata and trivia is counted separately; neither decides the result.
- **`not-applicable`:** zero-width and MISSING nodes.
- **`unknown`:** resolution failed.
- **Coverage is not "presence".** Every terminal can be active while the node's claimed
  parentage or construct identity is still wrong.
- **What it serves:**
  - LethAL's simple-site filter: a leaf operator or literal is mutable only if it is
    `active`;
  - graphify's condition tags, which it replaces.

### Axis 2: structural correspondence

Correspondence needs P1 and P2:

`correspond(p1_node, configured) -> [(p2_node, kind)]`

| `kind` | Meaning |
|---|---|
| `exact` | same construct, same terminals, same field role |
| `assembled` | the P1 node is made of fragments (for example split header plus shared body); the P2 node is this configuration's construct |
| `no-counterpart` | nothing in P2 corresponds (an inactive arm, a removed wrapper) |
| `unsupported` | there is no contract for this type yet |

- **Many-to-many is allowed.**
  - A G7 signed-literal leaf may correspond to two P2 tokens.
  - One `preproc_split_case_statement_end` may yield a case plus the siblings that follow
    it.
- **Matching** uses active terminal intervals plus a **correspondence contract for each
  split type**. Text or span equality alone is never enough.
  - The contracts reuse the oracle registry (`tools/config_oracle/contracts.py`: hosts,
    arms and policies) as the source of truth.
  - `unsupported` is a valid answer, and coverage is tracked per type.

### `active_arm(split_node, configured) -> P1 node | none`

This returns the arm a configuration selected, for example a split procedure's chosen
header. It is built on correspondence. It serves al-sem's confidence work and the fix for
its `object_kind_of()` bug, which maps every `PreprocSplitDeclaration` to `Codeunit`.

### F0: the traversal helper

The helper ships first and is independent of P2 and P3.

`walk(node, visitor)` classifies every node:

| Category | Examples | Default |
|---|---|---|
| **container** | `preproc_conditional*` and their arm bodies | descend into every arm; this fixes the four silent-loss consumers |
| **split assembler** | `preproc_split_*` | hand the visitor a `SplitInfo` (the arms plus the shared parts); never flatten, because flattening changes meaning |
| **directive trivia** | `preproc_if`/`else`/`endif`, `#pragma`, `#region` | skipped by default; available on request |

- **The classification table** is generated from the oracle registry. A census gate fails
  if a new `preproc_*` type is left unclassified, the same discipline as
  `contracts.census`.
- **It ships in Rust, Python and Node/WASM.** All three are tested against one fixture set
  with expected visit orders.
- **The documentation must say** that recursion alone does not fix node-kind recognition.
  Statement position and split headers need `SplitInfo`, and that is LethAL R214's lost
  active sites.

## 6. Packaging, runtimes and the slim spike

### Packaging

The `configured` companion API ships inside each binding package:

- `tree_sitter_al::configured` (Rust);
- `tree_sitter_al.configured` (Python);
- `@sshadows/tree-sitter-al/configured` (Node/WASM).

The plain `tree_sitter_al()` language export stays a standard grammar function, so
editors and queries are unaffected.

### Runtimes

- **v1:** Rust, Python, and Node native plus WASM. Go and Swift come later.
- **WASM:** C functions placed next to `scanner.c` are **not** automatically exposed
  through `web-tree-sitter`. F1b ships `al_preproc` as a companion WASM module with a
  small JS adapter.
- **Support claims:** a runtime is declared supported only once its tests pass.

### Slim grammar (F1d, a spike)

The candidate is the same `grammar.js` with the structural conditional and split rules
removed by a generate-time flag.

**What it must keep:**
- the directive extras that the mask leaves in place;
- scanner compatibility: external-token order, and the error-recovery guard.

**How it is measured:**
- `tools.perf ab`, with a new configured-input mode, on identical masked inputs:
  - ordinary AL;
  - every split and one-reading witness after selection;
  - EDocumentDE;
  - the kept extras;
  - invalid selections;
  - large blanked regions;
  - incremental edits and symbol switches.
- Trees must be equivalent across the complete public tree before any timing.
- What is measured:
  - native and WASM throughput and tail latency;
  - resolver-plus-parse latency;
  - incremental latency;
  - compressed artifact size;
  - WASM load time;
  - peak memory;
  - build and release cost.

**The bars, declared in advance:**
- **≥25% end-to-end** speed-up on the configured workload, at 24 or more `ab` rounds or
  with two agreeing runs: ship slim in every runtime, behind the companion API so that
  consumers never choose a grammar by hand.
- **≥40% WASM size or startup** improvement: ship a WASM-only slim artifact.
- **Neither:** keep one grammar permanently, and record the result in
  `docs/state-reduction-method.md` so the spike is not repeated.

## 7. Validation

| Ledger | Evidence | Gate |
|---|---|---|
| **P1, native CST** | deferred items; `production-classes.tsv` `debt(B*)`/`debt(C1)`; tree-harness; has_error sweep; oracle | the existing gates, unchanged |
| **P2, configured** | compiler-backed witnesses: each `alc_probe` case and each production family (EDocumentDE, every one-reading family, the else-led arms) parsed through P2 must equal a parse of the flat text of the alc-accepted configuration; plus the named tests below | a new `validate-grammar.sh` step plus CI; a corpus sweep `python -m tools.configured sweep --root …` with 0 unclassified resolution failures, 0 hidden-only errors, and incremental equivalence on sampled edits |
| **P3, correspondence** | a contract per split type, with `unsupported` counted; coverage fixtures; `active_arm` fixtures | a census: every `preproc_split_*` type has a contract or an `unsupported` entry with an owner |
| **Resolver conformance** | the vectors (Python == C == alc-anchored expectations); ASan fuzzing; Python-vs-C differential | CI |

The named P2 tests:

- G7: `-1` before a kept `#pragma`, and before a blanked `#endif`;
- CRLF with no final newline;
- a leading BOM, and the doubled BOM (open);
- very long blanked runs (performance);
- an empty selection;
- a file with only extras;
- EDocumentDE;
- each one-reading family;
- the else-led arms.

P2 performance is measured with `ab` in configured-input mode on the pinned V-Cache core,
following `docs/performance-baselines.md`.

## 8. Roadmap placement

Roadmap F1 is split, and F0 and E4 are added:

| Item | Content | When |
|---|---|---|
| **F0** | the classified traversal helper in Rust, Python and Node/WASM, with migration examples | in parallel with Phase B; ships in a non-breaking release |
| **F1a** | the `al_preproc` contract and vectors, the C port, conformance and fuzzing | in parallel with Phase C, once this spec is approved |
| **F1b** | the `configured` companion API and the incremental model in Rust, Python and Node/WASM; the P2 ledger; demonstrations on EDocumentDE and the one-reading families; first consumers LethAL (Rust) and al-perf (WASM) | after F1a |
| **F1c** | coverage, then the per-split correspondence contracts, then `active_arm`; consumer fixes found on the way (al-sem `object_kind_of`, LethAL R214) | after C1, because it reuses the completed oracle contracts |
| **F1d** | the slim-grammar spike (measurement only) | after F1b |
| **E4** | the consumer compatibility process (§9); brainstormed separately | before the next release |

Native-CST work stays in Phases B, C and D. EDocumentDE gets a time-boxed native
representation experiment in Phase B. If that fails, it stays P1 debt.

## 9. E4 in outline (for its own brainstorm)

- **Registry:** one machine-readable `consumers.json`, recording:
  - identity and owner;
  - integration mode;
  - declared, locked, installed and bundled versions;
  - the artifact hash;
  - the runtime ABI;
  - the tree-shape version tested;
  - the last migration evidence.

  Local checkout paths go in an optional, git-ignored mapping, and worktrees are
  deduplicated.
- **Checker:** `tools/check-consumers.py` reports lag and compatibility. When it cannot
  check a consumer it says "not checked", never "compatible".
- **Release flow:** E2 produces executable old/new behaviour canaries before a release.
  Then come targeted bump PRs with behaviour diffs and named owners. A release never
  waits on external merges.
- **First targets:** LethAL, al-sem, one WASM consumer and one Python consumer.

## 10. Out of scope for A7

All implementation. This spec is the deliverable. F0 and each F1 part get their own plan.
