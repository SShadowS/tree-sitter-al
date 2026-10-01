# Configuration-aware parsing: scope and design (roadmap A7)

**Status:** v2, 2026-10-01. The user approved v1's design section by section. v2 folds in a
second review round:

- gpt-6-sol: rework;
- gpt-6-astra: rework;
- gemini-3.8-flash: approve with changes.

All three kept the architecture. Their findings were about the public contracts and the
acceptance gates. v2 awaits the user's review.

**Roadmap:** A7 decides the scope; F0 and F1a–F1d implement it (§9).

**Inputs:**

- the consumer inventory (`.superpowers/sdd/a7/consumers.md`, summarised in §1);
- the design reviews (`.superpowers/sdd/a7/{sol,astra,gemini}-review.md`);
- the spec reviews (`.superpowers/sdd/a7/spec-review-{sol,astra,gemini}.md`).

**Terms used throughout:**

- **Canonical unit:** a byte offset into the original UTF-8 source, and a byte-based point
  (row, column in bytes).
- **Configuration:** a complete initial symbol set given by the caller.
- **Group:** one `#if`…`#endif` chain.
- **Arm:** one branch of a group.

## 1. Problem and consumers

The grammar parses every `#if` branch into one tree, the native all-branches CST. With the
current representation and the attempts made so far:

- **EDocumentDE (deferred item 10)** has no native tree. It is a split `add*` layout header
  whose body stays open across `#endif`. The attempts added +835 to +2,270 LR states, or
  `generate` never finished. That is evidence about those attempts, not proof that no
  representation exists.
- **The one-reading families** (10 production records) get a tree that shows one
  configuration's nesting.
- **The else-led `open_statement` arms** cannot be validated by the oracle (C1 debt).
- **Tokenisation can depend on the configuration.** In G7, `-1` is a signed literal only
  before `;`, `,`, `#` or EOF.

Consumer inventory (24 consumers):

- **The all-branches tree is load-bearing almost everywhere:** editors, diff tools,
  comment-audit, and al-sem's union analysis.
- **No consumer configures a tree today.** Where a configured view is wanted, it is wanted
  with original positions:
  - LethAL R214: mutants land in inactive arms, and active sites are lost because
    conditional parents fail statement-position checks;
  - al-sem: confidence;
  - graphify: condition tags. These are symbolic across builds, which is a different thing
    from activity in one configuration.
- **Only al-perf** would take a plain configured tree.
- **Four consumers mishandle `#if` content:** al-differ, code-graph-rag, DevOpsWorker and
  graphify. Each fails in its own way: a missing traversal, recognising only certain node
  kinds, or wrong condition logic.
- **Version drift is large:** about ten active consumers predate 4.0.0.

## 2. Products, claims and ledgers

| Product | Claim |
|---|---|
| **P1, native all-branches CST** (today's grammar) | Every branch is present. Each node's parentage, fields and tokens are true for the constructs it represents. |
| **P2, configured parse** | For one requested configuration: a tree of that configuration's masked text, at canonical original positions, meeting the gates in §8. |
| **P3, coverage and correspondence** | For one configuration: how each P1 node's source is covered, and how P1 relates to P2. |

The three products are reported in **four separate ledgers**:

| Ledger | What it records |
|---|---|
| **Native-CST defects** | P1 trees that are wrong or missing: deferred items, and `production-classes.tsv` entries whose cause is the grammar (for example `debt(B3, B3)`). |
| **Verification coverage** | What the oracle cannot yet check: `production-classes.tsv` `debt(C1, …)` entries. These are missing lowering, not proven grammar defects. One-reading records are `debt(F1, F1)`. Some else-led trees are recorded as lossless, with only the assembler missing. |
| **Configured correctness** (new, §8) | The P2 gates. |
| **Correspondence** (new, §8) | The P3 gates. |

**Rules:**

1. **No ledger closes another's entry.** P2 succeeding on EDocumentDE closes neither its
   native defect nor its oracle refusal. Closing the refusal needs a demonstrated oracle
   change.
2. **A failed native experiment does not close anything.** A time-boxed native-representation
   experiment that fails closes nothing and proves nothing impossible. It records:
   - the designs attempted;
   - state count and generate time;
   - corpus impact.
3. **The oracle checks consistency, not correctness.** Its flat text comes from the same
   Python resolver (`tools/alc_probe/matrix.py::flat_text`), and it parses that text with
   the same grammar. Correctness evidence comes from hand-written structural assertions plus
   compiler verdicts (§8).
4. **One grammar.** P2 parses masked text with the full grammar. A slim grammar is only a
   measurement spike that yields eligibility (§7).

## 3. The resolver core: `al_preproc` (C)

**Decision: C.** `al_preproc` is a small byte-level library in this repo, with no
tree-sitter dependency. C builds in every binding's existing toolchain (node-gyp,
setuptools, cargo `cc`, cgo, Swift, emscripten). The repo already ships, fuzzes and
ASan-tests C. `tools/config_oracle/directives.py` remains the **reference**. There are never
three independent ports.

### 3.1 C API: memory, concurrency and limits

```c
typedef struct al_limits {
    size_t max_source_bytes;      /* default 64 MiB */
    uint32_t max_nesting;         /* default 64 */
    uint32_t max_condition_depth; /* default 32 */
    size_t max_output_records;    /* directives + groups + events */
    size_t max_symbols;
} al_limits;

typedef struct al_resolution al_resolution;   /* opaque */

/* Reentrant and thread-safe: no global or static mutable state. All output lives in one
   arena owned by the returned al_resolution. `cancel` is polled throughout scanning,
   condition parsing and evaluation, at least every 64 KiB of input and at every directive,
   so a single long line is still bounded. It may be NULL. */
al_resolution *al_resolve(const uint8_t *source, size_t len,
                          const char *const *symbols, size_t nsymbols,
                          const al_limits *limits,
                          const volatile int *cancel);
void al_resolution_free(al_resolution *);
/* accessors return pointers into the arena; they are valid until al_resolution_free */
```

- **The condition parser** carries an explicit depth counter. If the counter passes
  `max_condition_depth`, it returns `limit-exceeded` without recursing further.
- **Allocation failure** returns the status `out-of-memory`.

### 3.2 Input

- **Source:** UTF-8 bytes. A leading BOM (bytes 0–2) is allowed. Any later BOM bytes are
  ordinary text: they are not skipped, so the doubled BOM of deferred item 6 behaves the
  same way it does in P1. Invalid UTF-8 is refused with `encoding-unsupported`. Transcoding
  other encodings is the caller's job.
- **Symbols:** given explicitly, and case-sensitive (alc-verified). The core does no
  filesystem lookup.
- **`app.json` loader.** The core does not read `app.json`; a separate helper does. Each
  binding provides
  `symbols_from_app_json(bytes) -> symbols | AppJsonError`, which:
  - accepts JSON and JSONC (comments, trailing commas);
  - reads `preprocessorSymbols`;
  - returns an empty set when the key is absent;
  - reports a type error if the value is not an array of strings;
  - keeps casing as written.

  Deciding which `app.json` owns a file is the caller's responsibility.

### 3.3 Output: the public schema and how it maps to the reference

| Field | Meaning | Present in the reference today? |
|---|---|---|
| `masked` | Same length as the source. See the masking rules below. | yes (`Resolution.masked`) |
| `selected_source` | Sorted intervals of original bytes that are *selected source*: in an active arm, and not part of a conditional-directive line. | yes (`Resolution.active`). Its definition is unchanged. |
| `retained_layout` | Bytes kept although not selected: the `\r` and `\n` of masked lines, and the leading BOM. | new; it can be derived from the reference |
| `conditional_directives[]` | For `#if`/`#elif`/`#else`/`#endif`: kind, `#` offset, physical line span, condition token span, condition AST | yes (`Resolution.directives`) |
| `definitions[]` | Active `#define`/`#undef`, in order: offset, symbol, and the change to the environment. These are **deltas**, not full environment snapshots, to avoid quadratic output. | **new** |
| `groups[]` | For each group: its arms, and a state | partly. The reference has `arm_choice`, where a missing entry means the group was not visited and `None` means no arm was selected. |
| `extras[]` | Active `#pragma`/`#region`/`#endregion`/`#define`/`#undef` events: kind and span | yes (`ExtraEvent` holds kind, start and end) |
| `status` | `ok`, or a code with a byte offset (§3.4) | yes (`ResolveError`) |

Each group has one of these states:

- `selected(arm)`: an active group, and one arm chose;
- `no-selection`: an active group where no condition held and there is no `#else`;
- `parent-inactive`: the whole group sits inside an inactive arm.

The **reference gains the same public schema.** `definitions`, `retained_layout` and the
explicit group states are added to `directives.py`, and conformance compares the full
schema. Where the reference needs new code, the work is listed in F1a.

**Masking rules:**

- In an **inactive arm**, every byte except `\r` and `\n` becomes `0x20`. That includes
  comments, quotes and anything else, and none of it updates lexer state.
- A **conditional-directive line** becomes `0x20`, including any trailing `//`. Its
  `\r` and `\n` are kept.
- **Active extra-directive lines are kept verbatim.**
- The **leading BOM** is kept.

**Lexical rules** (alc-probed; see `docs/preproc-directive-semantics.md`):

- **Active text:** the scanner tracks `/* */` block comments, `//` line comments, ordinary
  quoted strings and identifiers, and verbatim `@'…'` strings. A directive-looking line
  inside a block comment or a verbatim string is text.
- **Inactive text:** only lines that start with a directive (optional whitespace, then `#`)
  are recognised.
- A `/* */` comment on a directive line is `block-comment-on-directive`.

### 3.4 Status codes: fail closed

**From the reference, complete list:**

- `unknown-directive`
- `empty-condition`
- `unsupported-condition`
- `unsupported-condition-token` (this covers `&&`/`||`, consistent with roadmap B2)
- `block-comment-on-directive`
- `trailing-token`
- `duplicate-else`
- `elif-after-else`
- `unbalanced-if`, `unbalanced-elif`, `unbalanced-else`, `unbalanced-endif`
- `directive-after-code`
- `malformed-define`
- `unterminated-active-comment`, `unterminated-active-string`, `unterminated-active-verbatim`

`discovery-not-converging` belongs to `discover()` only and is never emitted by `al_resolve`.

**New codes:** `limit-exceeded`, `cancelled`, `encoding-unsupported` and `out-of-memory`.

**Any non-`ok` status yields no masked buffer:** there is no partial output and no
fallback to P1.

### 3.5 Not in the core

- **Symbolic "which configurations?" analysis.** This would be a separate, bounded API with
  an explicit `unknown` result, defined later. graphify's condition tags need it.
- **`discover()`-style enumeration.** Single-configuration calls never enumerate.

### 3.6 Conformance

Four tiers. Only tier 1 is authoritative.

1. **The authoritative kernel** (`tests/preproc-vectors/kernel/*.json`). Each vector is
   **written by hand and reviewed by a second reader.** It holds the exact masked bytes,
   the interval lists, the group states, the definition deltas and the status. Each one
   has a mutation test in both implementations that proves it can fail. It covers:
   - CRLF, and no final newline;
   - BOM and doubled BOM;
   - multibyte and supplementary characters before, inside and after inactive regions;
   - ordinary strings and identifiers containing `#`;
   - comments and verbatim strings that span directive-looking lines;
   - inactive unterminated strings and comments;
   - every status code;
   - nesting and depth at their limits;
   - `#elif` first-match;
   - sequential `#define`/`#undef`;
   - the three group states.
2. **Compiler anchoring.** Every `tools/alc_probe` case contributes the compiler's
   *selection* verdict: alc identity, discriminating controls, and both split and flat
   compiles. Those cases also run as **raw compiler probes** for inputs the resolver refuses.
   These are labelled as compiler evidence, not as expected masks.
3. **Generated differential vectors.** Generated from the reference, labelled
   *non-authoritative*, and used only to compare C with Python.
4. **Fuzzing.** C under ASan/UBSan, plus a Python-vs-C differential run.

Where the compiler disagrees with Python, the compiler wins: Python is fixed and a kernel
vector is added.

## 4. The configured parse (P2)

### 4.1 Call shape and outcomes

```
configured.parse(new_source, symbols, *, limits, previous=None, edits=None, cancel=None)
  -> Configured
```

- **`new_source`** is the complete new text.
- **`previous` and `edits`** are optional. `edits` describe the transition from
  `previous.source` to `new_source`, in canonical coordinates. When supplied, they are
  checked for consistency.
- **`previous` is never mutated.** Its tree is copied before any synthetic edit, so earlier
  snapshots stay usable.

`Configured` is immutable. It holds: `source`, `revision` (a content hash), `symbols`,
`grammar_build_id`, `resolver_version`, `schema_version`, `resolution`, `masked`, `tree`,
`outcome`.

**Outcomes.** Each is reported separately:

| Outcome | Meaning |
|---|---|
| `resolution-failed` | the core's code; there is no tree |
| `cancelled` | the parser is reset afterwards, never resumed |
| `operational-error` | artifact load or allocation failure |
| `parsed-clean` | `has_error` is false. This is **not** a validity claim. |
| `parsed-recovered` | `has_error` is true. The tree is returned, and its error and missing nodes are listed. |

Compiler validity is always `unknown` from the API.

### 4.2 Coordinates

- **Public API positions** are canonical: original UTF-8 byte offsets and byte points.
- **The masked buffer is the same length as the source,** so the bytes the tree sees equal
  the original bytes, numerically.
- **Raw nodes and views are separate things.** Raw binding nodes are the runtime's own
  objects, in the runtime's units. Configured node views are what the API returns, in
  canonical units, with helpers whose units are named explicitly:
  - `utf16_index_of(byte_offset)`;
  - `byte_offset_of_utf16(index)`;
  - Python `char_index_of(byte_offset)`.
- **The conversion chain, for runtimes that parse strings:**
  1. masked runtime index;
  2. masked UTF-8 byte offset, computed **from the masked text**;
  3. the identical original byte offset;
  4. the original runtime index, computed **from the original text**.

  Blanking a multibyte inactive character to N spaces changes the masked UTF-16 length, so
  steps 2 and 4 must use their own text. The chain applies to node positions, query
  captures, range queries and synthetic tree edits.
- **WASM:** parses from the masked **string** given to `web-tree-sitter`, and converts
  through the chain above. A malformed UTF-16 surrogate in the input string gives
  `encoding-unsupported`.
- **Python:** parses bytes, so its raw nodes are already canonical.
- **Rust:** works in bytes.

### 4.3 Text helpers

| Helper | Returns |
|---|---|
| `node_text(n)` | the original bytes of `n`'s span |
| `active_segments(n)` | an ordered list of `(byte range, bytes)` for the selected source inside `n`. This is the provenance-preserving form. |
| `active_text(n)` | the concatenation of `active_segments`. It is documented as **lossy in coordinates**, and is not a parse input. |
| `masked_text(n)` | the masked bytes of the span |
| `is_span_fully_selected(n)` | true only if the span holds no unselected or directive bytes. It says nothing about the semantic safety of a refactoring. |

### 4.4 Incremental updates

v1 is correctness first. A faster scheme may replace it only if it passes the same tests.

1. **Re-resolve the whole new source.** The cost of this is measured, not assumed.
2. **If `new_masked` equals `previous.masked` byte for byte** and the edits are
   equal-length, reuse the previous tree and update only the source and revision.
   Otherwise go on.
3. **Compute the masked edit.** The masked buffer always has the same length as its source.
   So the `edits` from step 1, applied in original coordinates, are also edits to the masked
   buffer: insertions and deletions at the same offsets. On top of those come the bytes
   whose masking flipped.
   - Express the source edits as `tree.edit` calls in **descending start-offset order**,
     with points computed from the old and new masked texts.
   - Express the flipped regions as replacement edits.
   - **Fall back to a fresh parse** if:
     - the flipped bytes exceed 64 KiB;
     - they span more than 16 disjoint regions;
     - `edits` were not supplied.
4. **Parse** `new_masked` with the copied and edited tree.
5. **If re-resolution fails,** return `resolution-failed` and keep no tree.

**What forces a fresh parse:** a change of symbol set, `grammar_build_id`, resolver version
or schema version.

**Equivalence requirement.** The incremental tree must equal a fresh parse of the same
masked text. Equality is checked on the complete cursor walk: anonymous tokens, fields,
byte spans, points, and missing, extra and error flags. On top of that, the **edited old
tree's points** are checked against the new text, which is the edit-point check in
`tools/perf/incremental.py`. Fresh-against-incremental equality alone misses bad edit
points.

**Incremental tests** cover:

- insertions, deletions and newline edits in inactive arms;
- an edit that creates or destroys a directive;
- `#define` edits;
- active comment, string and verbatim edits that change directive recognition;
- CRLF changes;
- symbol switches;
- chained edits;
- further use of the previous snapshot.

### 4.5 Cancellation

Cancellation spans every phase: resolution, diffing and the parse. The parse uses
tree-sitter's progress callback or timeout, and the parser is reset after any
cancellation. In WASM a synchronous call cannot see a flag set from the same thread, so
cancellation is supported **only when the API runs in a Worker**. The cancel flag is then
a `SharedArrayBuffer` word, read by both the resolver and the progress callback. On the
main thread the API offers no mid-call cancellation, and the docs say so.

Tests cover cancellation during a long-line resolution, during diffing and during a parse.
Each test is followed by a successful parse of a different document on the same parser.

### 4.6 Not in scope

Parsing all configurations at once, and merging configured trees.

## 5. Arm selection, coverage and correspondence (P3)

### 5.1 The shared arm model

F0, P2 and P3 all use one model. It is defined here before any of them is planned, and it
adds **no** P1 node types.

```
select_arm(group_id, resolution)
  -> selected(ArmView) | no-selection | parent-inactive | unresolved

ArmView {
  group_id,
  arm_id,
  source_ranges,        # the selected source bytes of the arm
  fielded_fragments     # ordered (field name | none, P1 child node | anonymous token)
                        # pieces: the P1 children inside the arm, in source order.
                        # Hidden rules such as _procedure_header appear as their children.
}
```

- **One P1 node may contain several groups.** For example, `preproc_split_if_then_begin`
  has an opening group and a closing group. `groups_of(p1_node)` lists them in order.
- **`active_arms(p1_node, configured)`** returns, for each group, its `select_arm` result.
  This replaces v1's `active_arm → node`, which promised a node that does not exist.

### 5.2 Source coverage

`coverage(p1_node, configured) -> active | inactive | mixed | not-applicable | unknown | wrong-document`

- **What is counted:** significant terminals. Directive and extra nodes are metadata; their
  coverage is reported separately by `trivia_coverage(n)`.
- **`not-applicable`:** a node with no counted terminal. That includes zero-width, MISSING,
  directive-only and trivia-only nodes.
- **`unknown`:** resolution failed.
- **`wrong-document`:** the node belongs to a different revision or `grammar_build_id`.
- **P1 `ERROR` nodes** are counted like any other node, using their terminals.
- **Byte-range form** for sub-node mutation sites: `coverage_of_range(byte_range)`.
- **Coverage is activity in one configuration,** not presence and not a symbolic
  condition. It **adds** configured activity annotations. It does **not** replace graphify's
  condition tags, which need the deferred symbolic API.

### 5.3 Structural correspondence

```
correspond(p1_node, configured)
  -> matched([Link]) | no-counterpart(reason) | unsupported(contract_context) | unavailable(reason)

Link { p2_node, kind, p1_intervals, p2_intervals }
kind = identity | assembled | retokenised | reparented
```

**Each kind:**

- **`identity`:** the same construct, terminals and field role.
- **`assembled`:** the P1 construct is built from fragments, for example a split header plus
  a shared body.
- **`retokenised`:** the configuration tokenises the text differently. In G7, one P1 leaf
  becomes several P2 tokens, or the reverse.
- **`reparented`:** the same construct with a different parent. One example is the siblings
  after `preproc_split_case_statement_end`. A statement that is always selected can also
  change parent.

**Matching** uses source intervals plus a **correspondence contract**. The contracts are
separate from oracle *lowering* support:

- they reuse the registry identities and the reviewed facts;
- they are written specifically for correspondence;
- a registered assembler does **not** imply correspondence support. For example,
  `preproc_conditional_case` excludes `case_else_branch` from its arms today.

## 6. F0: the classified traversal helper

### 6.1 The traversal policy

The policy is **written by hand and maintained by hand.** Name prefixes are **never** used
as a classification rule.

**Seven classes:**

| Class | Meaning | Default `walk` behaviour |
|---|---|---|
| ordinary | not a configuration node | normal descent |
| branch container | a group whose arms are complete units (registry kind `branch-select`) | descend into every arm, and report `(group, arm)` to the visitor |
| assembler | a construct built from arm fragments plus shared parts, possibly crossing `#endif` (registry `assembler`) | hand the visitor a `SplitInfo` and never flatten it |
| fragment | a piece that only makes sense inside an assembler (registry `fragment`) | delivered through `SplitInfo` |
| token alias | a keyword or terminal emitted by a split token (registry `token-alias`) | treated as an ordinary token |
| directive metadata | `#if` / `#elif` / `#else` / `#endif` lines | skipped unless requested |
| trivia | `pragma`, regions, `#define`/`#undef` | skipped unless requested |

Known exceptions that **must** be pinned by witnesses:

- `preproc_conditional_expression_tail` is an assembler whose continuation comes after
  `#endif`.
- `preproc_conditional_table_relation` and `preproc_conditional_property_value` are
  assemblers.
- `preproc_split_begin` and `preproc_split_end` are token aliases.
- `preproc_split_case_end_branch` and `preproc_split_report_brace_close` are fragments.
- `else_table_relation_fragment` has no prefix.
- `pragma` is not in the registry today.
- The 7 registry `unsupported` types each get an explicit class and a witness. An
  `unsupported` lowering status is not a traversal class.

**`SplitInfo`** carries:

- the `groups_of` list;
- each group's arms as `ArmView` fragments (§5.1), unconfigured, so every arm is present;
- the shared parts, in source order, with their field names;
- anonymous tokens, kept as tokens.

**Census gate.** Every named type in `src/node-types.json` that is not ordinary needs a
policy entry: prefixed and unprefixed, registered and unregistered. A new or removed type
fails the gate. Same discipline as `contracts.census`.

### 6.2 Acceptance

1. **Per-runtime parity** across Rust, Python and Node/WASM. The same fixtures must give
   the same **fielded visit sequence**: class, type, field and arm identity.
2. **Witnesses for every exception in §6.1.** A mutant that treats `expression_tail` as
   transparent must fail them.
3. **Executable consumer canaries.** F0 *enables* fixes; it does not perform them. The
   canaries check behaviour, not just visit order:

| Consumer | What the canary checks |
|---|---|
| DevOpsWorker | recognises split procedures |
| al-differ, code-graph-rag | find definitions in every conditional arm, and object bodies through split declarations |
| graphify | its `#elif` and `#else` condition case. It is reported `unsupported` until the symbolic API exists. |
| **LethAL R214, part 1** | statement-position recognition under conditional parents. The previously lost active call and assignment sites must be found. |

4. **Docs:** recursion alone does not fix node-kind recognition. Use `SplitInfo`.

## 7. Packaging, runtimes and the slim spike

### 7.1 Packaging and runtime contracts

The `configured` companion API ships inside each binding package:

- **Rust:** `tree_sitter_al::configured`, behind a **cargo feature** (`configured`, off by
  default). It adds the runtime `tree-sitter` dependency at a declared range
  (`>=0.25, <0.27`, matching the inventory).
- **Python:** `tree_sitter_al.configured`.
- **Node:** `@sshadows/tree-sitter-al/configured`. It has a **browser-safe subpath** that
  never imports the native addon.

The plain `tree_sitter_al()` language export is unchanged.

**WASM:** `al_preproc` ships as a companion WASM module with a small JS adapter. C placed
next to `scanner.c` is not exposed through `web-tree-sitter`.

**Runtime support matrix** (declared, and tested before any support claim):

- Rust: tree-sitter 0.25 and 0.26;
- Python: ≥ 3.12 (the `requires-python` in `pyproject.toml`), with py-tree-sitter at the ranges in `tools/check-runtime-ranges.py`;
- Node: 18 or later (native);
- browser WASM: web-tree-sitter at its declared range.

Go and Swift come later.

**Clean-install artifact tests:** install each published artifact into a clean environment
with no Python and no repository tools, then load and parse. Include a real browser WASM
load.

**Identity:** every result carries `grammar_build_id`, `resolver_version` and
`schema_version`. Package semver alone does not identify unreleased builds.

**`node-types.json`:** the canonical file at the repo root and in every package is always
generated from the full grammar.

### 7.2 Slim grammar (F1d): a spike that yields eligibility, not a release

**Candidate:** the same `grammar.js`, with the structural conditional and split rules
removed by a generate-time flag.

**What it must keep:**

- the directive extras that masking keeps;
- scanner compatibility: external-token order and the error-recovery guard.

**Harnesses come first, and must be built and verified before any number counts:**

- `ab` in parse-only configured-input mode. Corpus files are resolved and masked into
  memory **once**, before the timed ABBA loop.
- an end-to-end API benchmark: resolver plus parse plus adapter;
- a WASM A/B harness covering throughput, compressed size, and instantiate and compile
  time;
- an incremental benchmark.

**Before any timing,** the complete public trees must be equivalent on masked inputs:

- ordinary AL;
- every split and one-reading witness after selection;
- EDocumentDE;
- the extras that masking keeps;
- invalid selections;
- large blanked regions.

**Eligibility.** Two bars are declared in advance and assessed independently:

- **Native/all runtimes:** median parse throughput ratio slim/full ≥ 1.25 on the configured
  workload. The 95% CI lower bound must be ≥ 1.20, from 24 or more `ab` rounds or two
  agreeing runs. No runtime may show a p99 latency or peak-memory regression > 5%.
- **WASM-only:** a reduction of ≥ 40% in **brotli-compressed** artifact size (including the
  companion resolver and loader), **or** a reduction of ≥ 40% in `WebAssembly.instantiate`
  plus compile time in Node/V8. Throughput may not regress by more than 5%.

**Eligibility is not a release.** Shipping a slim artifact needs its own approved change:
packaging, schema and query compatibility, and per-runtime correctness. If a slim artifact
ships, its types go in `node-types.slim.json`, and the canonical file is never replaced.

**If neither bar is met,** record "not justified for these builds and workloads" in
`docs/state-reduction-method.md`, with reconsideration triggers:

- a major grammar-size change;
- a new configured-heavy consumer;
- a new WASM size budget.

## 8. Validation gates

### 8.1 P2: configured correctness

**Configuration manifest.** `tests/configured/manifest.tsv` lists every `(file, configuration)`
to test. Its rows come from three sources:

- the alc-probe cases;
- the production families;
- explicitly listed corpus configurations, taken from each file's resolver-discovered
  configurations with an explicit bound and **test-only**.

Each row gets an expected class: `valid`, `expected-invalid` (with compiler evidence) or
`deferred` (with an owner).

**The gate requires all of the following:**

1. **Every row is accounted for** in every runtime under test, and every requested root is
   non-empty. The successful population must be non-vacuous: every named witness plus at
   least 1,000 corpus configurations, with the count reported.
2. **Zero unclassified outcomes.**
   - Every `valid` row must be `parsed-clean`. Visible ERROR nodes count, not just hidden
     MISSING ones.
   - `expected-invalid` and `deferred` rows must match their classification exactly. A
     stale classification fails.
   - A classified row is never counted as validated.
3. **Hand-written structural assertions** pin node types, fields, token kinds and
   provenance for these witnesses:
   - each named family: EDocumentDE, every one-reading family, the else-led arms;
   - **the G7 witness:** a valid host where `-1` is followed by a kept `#pragma` line and
     then an operator. alc is probed first. If it accepts, the intended unary-or-literal and
     operator structure is pinned, together with a terminator control and the blanked-`#endif`
     variant.
   - CRLF with no final newline;
   - leading and doubled BOM;
   - long blanked runs;
   - empty selection;
   - extras only.

   Comparing P2 with a flat parse of the same text remains, but **as an equivalence check
   only**.
4. **Fresh against incremental equality, plus the edit-point check,** on sampled edits (§4.4).
5. **Gate self-test mutations:** a visible ERROR, a hidden MISSING, a dropped configuration,
   an empty root, a stale classification. Each must turn the gate red.
6. **The report records:**
   - the identities: source revision, configuration, `grammar_build_id`, resolver and schema
     versions, runtime;
   - per-root counts of clean, recovered, failed, classified and untested.

**Placement:** `validate-grammar.sh` runs the manifest witnesses. CI runs the witnesses and
the gate self-test. The corpus sweep (`python -m tools.configured sweep`) runs under
`--full`.

### 8.2 P3: correspondence

1. **A mandatory supported matrix** of **type × host × arm shape × reading** for:
   - every assembler and branch container;
   - the non-prefixed fragments;
   - conditional expression and relation nodes;
   - ordinary shared descendants;
   - G7 literals.

   Each supported cell has an active witness that asserts the actual links: kind,
   intervals, parent.
2. **Mutation tests:** wrong parentage, provenance with the same text but a different arm,
   a dropped link, a stale document. Each must fail.
3. **`unsupported` cells** are listed explicitly, each with an owner. They **never count**
   toward the mandatory minimum.
4. **Coverage witnesses:**
   - directive-only, trivia-only and ERROR nodes;
   - wrong-document rejection;
   - masked gaps;
   - **LethAL R214, part 2:** inactive sites are excluded or marked, so no inactive
     configuration is reported as an ordinary survivor.

### 8.3 Resolver conformance

The four tiers of §3.6, in CI.

### 8.4 Performance

P2 performance is measured with the harnesses from §7.2, on the pinned V-Cache core, under
`docs/performance-baselines.md` (same session, `ab`).

## 9. Roadmap placement and release boundaries

| Item | Content | Depends on | When |
|---|---|---|---|
| **F0** | Classified traversal policy (§6), `SplitInfo` and `ArmView` (§5.1, unconfigured), Rust/Python/Node/WASM helpers, consumer canaries including LethAL R214 part 1 | this spec | in parallel with Phase B |
| **F1a** | `al_preproc` C core, the reference schema upgrade, the four conformance tiers, limits, cancellation, `app.json` helper | this spec | in parallel with Phase C |
| **F1b** | `configured` API and adapters, coordinates, incremental model, cancellation, packaging and clean-install tests, the P2 gate (§8.1), **coverage (§5.2), including R214 part 2**, first consumers al-perf (P2) and LethAL (coverage) | F1a | after F1a |
| **F1c** | structural correspondence (§5.3), the supported matrix (§8.2), configured semantic lowering, al-sem `object_kind_of` fix | F1b **and** the relevant C1 contracts | after both |
| **F1d** | slim-grammar spike: harnesses plus eligibility (§7.2) | F1b | after F1b |
| **E4** | consumer compatibility process (§10), own brainstorm | this spec | before the next release |

**Release boundaries.**

- **F0** ships **additively in the next major release**, together with the unreleased
  tree-shape changes. Its policy is generated against that grammar. No backport is made to
  the 4.x line: a policy generated against `main` does not describe the 4.x trees.
- **The next stable major** is gated by: the Phase B tree-breaking work, the gates (A1–A4,
  C2), E1–E3, **E4's release steps**, and F0.
- **F1a–F1d** ship in later minor releases.
- **Consumer adoption** (a merged bump PR) is never a release gate. Canaries and migration
  notes are.

**Native work** stays in Phases B, C and D. EDocumentDE gets a time-boxed native experiment
in Phase B, and its outcome is recorded under §2 rule 2.

## 10. E4 outline (its own brainstorm)

**Registry:** one machine-readable `consumers.json`, recording for each consumer:

- identity and owner;
- integration mode;
- declared, locked, installed and bundled versions;
- artifact hash;
- runtime and ABI;
- the tree-shape version tested;
- the last migration evidence.

Machine-local paths go in an optional, git-ignored mapping file. Worktrees and indirect
consumers are deduplicated.

**Checker:** `tools/check-consumers.py` reports lag and compatibility. A consumer it cannot
inspect is reported as "not checked", never as compatible.

**Release flow:**

1. E2 produces executable old/new behaviour canaries before the release. The canaries
   cover:
   - definitions in every arm;
   - split headers;
   - statement positions;
   - `case_else_branch` ownership (item 22);
   - field cardinality;
   - query captures;
   - mutation spans;
   - native/WASM parity.
2. Targeted bump PRs follow, each with a behaviour diff and a named owner.

**Priority:** LethAL, al-sem, one WASM consumer and one Python consumer.

## 11. Out of scope for A7

All implementation. This spec is the deliverable, and F0 plus each F1 part gets its own plan.
