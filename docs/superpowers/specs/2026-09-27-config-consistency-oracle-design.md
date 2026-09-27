# Configuration-Consistency Oracle — Design

**Date:** 2026-09-27
**Status:** Design agreed section by section; the written spec is under review. Nothing below is implemented.
**Scope:** Build the oracle and wire it into both gate tiers. Grammar defects it finds are fixed in their own commits, each with a fixture. Changing the grammar to make lowering easier is out of scope.

The design was developed over two rounds with gpt-6-astra, an independent model that read the grammar, scanner, tools, CI workflow and `validate-grammar.sh`. The written spec was then reviewed independently by gpt-6-sol and gemini-3.8-flash. Corrections are marked with their source where they changed the design. One reviewer claim was checked and rejected: gemini counted 60 named `preproc*` types, but parsing `src/node-types.json` gives 74 top-level named types. Its `grep -c` counted references, not type definitions.

## Problem

This grammar parses **every** branch of `#if`/`#elif`/`#else`/`#endif` into one tree. The AL compiler (`alc`) does not: it evaluates the directives and never parses an inactive branch. Where a branch boundary cuts through a construct, the grammar enumerates the shape as a dedicated rule. Examples: a procedure signature that differs per branch over a shared body, or a block's `end` that lives inside a later `#if`. There are 74 named `preproc*` node types.

An enumeration has one characteristic failure mode. A shape nobody listed parses as a **wrong tree with zero ERROR nodes**. No existing gate compares the tree against what each configuration actually is:

| Gate | Blind because |
|---|---|
| `parse-al-parallel.sh` | counts ERROR/MISSING only |
| `tools/tree-harness.sh` | proves a tree did not *change*, not that it was ever right |
| `tree-sitter test` | expected trees are written by the same person who wrote the rule |
| `qc` (query coverage) | proves bytes reach nodes and reports some field/edge anomalies, not that nodes group the right bytes per configuration |
| `tools/validate_al_file.py` | has a targeted orphan-operator check for one former `#if` expression tear; nothing general |

These instruments are not blind to every silent misparse (sol), but none performs a per-configuration comparison.

The class is not hypothetical. Every item below shipped or was found with a clean error count:

1. The `end else begin` over `#endif` at `CRMSetupDefaults.Codeunit.al:76-84` flattened a whole if/else into a single then-branch.
2. `else #if X … #else begin A(); end; #endif` lost its `code_block`. `begin` became an identifier, and the statements became siblings of `begin`.
3. A `PREPROC_SPLIT_END` lookahead stopping on a trailing comment reparsed the run as a `call_statement`.
4. `#if`/`#elif` conditions swallowed the following line (`c6b8107`).
5. A split procedure signature followed by a pragma-only `#if` parsed the pragma block as an empty `preproc_conditional_var_block`. Found and fixed on 2026-09-27 (`04ff498`).

Issues #24 and #25 were reported by users. The project needs an instrument that finds this class on its own.

## Idea

For a file with `#if`, every assignment of its preprocessor symbols gives one **configuration**. In a single configuration the file is plain AL with no directives. This grammar parses plain AL without any split rules, so that parse is a much stronger reference than the multi-configuration tree.

The oracle checks, for every file and every configuration:

> The multi-configuration tree, **lowered** to that configuration, has the same ordered, field-labelled AL structure as the parse of the configuration's text. Separately, the multi-configuration tree satisfies its own **representation contracts** before any configuration is selected.

**The name matters.** This is a *configuration-consistency* oracle, not a correctness oracle. Both parses come from one grammar, so a defect that breaks both in the same way passes. Ordinary-AL fixtures and `alc` probes remain essential. CLAUDE.md will describe it under this name and claim nothing more.

### Why both halves are needed

Configuration equivalence alone cannot catch defect 5. The wrong wrapper (an empty `preproc_conditional_var_block`) and the right one (`preproc_pragma_only`) both lower to "a pragma, then the body". The single-configuration program is identical, so there is nothing for the comparison to reject, and the projector must not invent a `var_section` to make it fail. The defect is visible only as a claim the multi-configuration tree makes about itself, which is what representation contracts check. *(astra, round 1.)*

### Why not simpler comparisons

- **Type-and-span bags** miss wrong attachment. Two trees can hold the same calls and declarations while one call hangs off the wrong procedure.
- **Treating split nodes as transparent wrappers** misses a split node that groups the wrong pieces, as long as the leaves survive.
- **Full tree equality after naive projection** has no defined meaning where a split node crosses branches.
- **A correspondence table from split type to construct** is not enough. `preproc_split_case_statement_end` becomes a `case_statement` **plus following sibling statements**, and report-brace rules change which dataitem owns a trigger. *(astra, round 1.)*

## Architecture

The package is `tools/config_oracle/`, in Python with `py-tree-sitter`.

| Module | Responsibility |
|---|---|
| `directives.py` | Independent directive recognition and evaluation; the masked text for each configuration |
| `ir.py` | The comparable form: ordered field-labelled nodes, leaf provenance, typed fragments |
| `reference.py` | Extract the comparable form from the single-configuration parse |
| `contracts.py` | The hand-maintained, authoritative registry of special types |
| `lowering/` | Branch selection, assemblers, fragment consumers |
| `representation.py` | Contracts on the multi-configuration tree, independent of configuration |
| `compare.py` | Token, structure and trivia checks; discrepancy identities |
| `fixtures.py` | Extract cases from `test/corpus` |
| `runner.py`, `__main__.py` | Discovery, worker pool, accounting, reports, baseline, exit codes |

**Isolation rule:** `lowering/` must never import `reference.py`, and must never invoke a parser. Unit tests assert both, by inspecting imports and by running the lowering with the parser entry points replaced by functions that raise. These tests are **necessary, not sufficient** *(sol)*: a handler could still rebuild the answer from the selected source bytes by hand. The real defences are the reviewable contract of each handler, the accounting check, and the adversarial replays in section 5, which exist precisely to show that a wrong tree is not repaired. If lowering can see the single-configuration tree, a "matching helper" eventually starts repairing the tree under test with the answer, and the oracle turns into a second parser that agrees with itself. *(astra, round 2: "the most dangerous shortcut is a permissive normaliser that fixes the tested tree until both sides agree.")*

## 1. Directive resolver (`directives.py`)

**Input:** raw file bytes. The resolver never consults the grammar, and never walks `preproc_if` nodes or their `condition` fields. If it used the tree, a grammar bug would hide itself.

**Output:**

- **Directive groups.** Each `#if` … `#endif` group, with its nesting and its arms (`#if`, each `#elif`, `#else`). Each arm has a **presence predicate**. For a group under parent predicate `P` with arm conditions `e0 … en`:

  ```text
  if arm:      P ∧ e0
  elif arm i:  P ∧ ¬e0 ∧ … ∧ ¬e(i-1) ∧ ei
  else arm:    P ∧ ¬e0 ∧ … ∧ ¬en
  ```

  `#elif` is first-match. It is not an independent `#if`.
- **Directive extents.** For every directive: the offset of its `#`, the extent of its keyword, the **extent of its condition**, and the end of its line. These are the independent facts that the tree's directive nodes are checked against (see `directive-mismatch` below). A start offset alone cannot catch a condition that swallows the next line, because the swallowing directive still starts at the right `#`. *(sol)*
- **Symbol set** per file: symbols in conditions, plus `#define`/`#undef` names.
- **Masked text** per configuration. Every active byte stays at its original offset, so there is no byte map and no token merging at splice points. The rules, stated exactly *(gemini, sol)*:
  - inactive text is replaced by ASCII space (`0x20`) byte for byte, except that every `
` and `
` is kept, so line structure and CRLF are unchanged;
  - a consumed conditional directive line (`#if`, `#elif`, `#else`, `#endif`) is masked **in full**, from its first byte to the end of its line, **including any trailing comment**, so no comment changes position relative to the code;
  - a leading UTF-8 BOM is kept verbatim; a BOM anywhere else is ordinary text (see `docs/deferred-work.md` on the doubled-BOM file);
  - active UTF-8 is untouched;
  - active `#define`/`#undef`/`#pragma`/`#region` lines are kept, because they are extras in both parses;
  - masked bytes are recorded as padding, not as surviving source.

  Whether a directive may share a line with code, and whether a trailing comment is allowed on a directive line, are settled by probes 4 and 5. If the compiler accepts either, the whole-line rule above is revised before the resolver is written, not patched afterwards.
- **Trace** per configuration: which arm each group took, and why.
- **Extra events:** each comment, pragma, region/endregion and define/undef, with its interval and presence predicate. This feeds the trivia check.

**Lexing.** A small byte-level scanner with two modes. *Active* mode tracks strings, quoted identifiers, **verbatim strings, which can span lines** (`grammar.js` `verbatim_string`) *(sol)*, and comments, so a `#if` inside a block comment or a verbatim string is not a directive. Each of these has its own newline behaviour, taken from the grammar and checked by probe. *Disabled* mode is used inside inactive arms, and its treatment of quotes and comments is **set by the probes below**, not assumed from AL lexing. `tools/query_coverage/lexer.py` is not reused: it returns character offsets, has no disabled mode, and scans quotes across newlines. Its tested token rules may be borrowed.

**Configurations.** Every assignment of the file's **free** symbols: the symbols used in conditions that the file never `#define`s or `#undef`s. BC.History's measured ceiling is 6 symbols (64 assignments), and 1,076 of 1,281 `#if` files have one symbol.

`#define`/`#undef` are evaluated **sequentially, per configuration**. The resolver walks the directives in source order with a symbol environment that starts from the assignment. A `#define` or `#undef` changes the environment **only if it is active**, meaning inside arms that were selected. Every later condition is evaluated against the environment at its own position, never against the initial assignment. A symbol that is both assigned and `#define`d has its assigned value only until the first active definition. *(gemini, sol)* Where `#define` may legally appear is `alc`'s positional rule (`docs/preproc-define-undef.md`) and a linter's concern. The resolver evaluates what the text says. The resolver also reports **arm coverage**: an arm that no assignment selects (for example `#if X` nested in `#if not X`) is listed. It is never counted as covered.

**Fail closed.** Unbalanced directives, an operator outside the probed vocabulary, or a construct the probes have not settled gives `cannot-validate: <reason>` for that (file, configuration). It is never treated as false and never skipped.

**Degenerate inputs are explicit, never vacuous** *(sol)*:
- a file with no conditional directives is not an oracle input, and is counted as `no-directives` in the report;
- a configuration whose masked text is empty or contains only extras is a real configuration, validated like any other: its expected structure is a `source_file` with no children;
- an input set (fixtures, or one corpus) that yields **zero** validated (file, configuration) pairs fails the run as `incomplete`, so no tier can pass by checking nothing.

### Probes, done before the resolver is written

The four-way rule in `docs/deferred-work.md` (flat and split, symbol defined and undefined) is the **minimum** and suffices for single-symbol questions. It is not enough for questions about precedence, overlapping `#elif` or `#define` state. Those need every combination of the symbols involved, and a flat equivalent for each. *(sol)* Every probe has a **discriminating control**: the wrong reading must produce a compile error, for example by referencing a procedure that only the right branch declares, because two successful compiles of two different valid programs prove nothing. Each probe uses an isolated project and a fresh output path, so a stale `.app` cannot count as success.

1. Are preprocessor symbols case-sensitive?
2. Which operators are accepted (`and`/`or`/`not`, `&&`/`||`/`!`), with what precedence, and are parentheses allowed?
3. Is `#elif` first-match when several arms are true?
4. May a directive follow code on the same line?
5. May a directive line carry a trailing `//` or `/* */` comment?
6. What does an unterminated `'` or `/*` inside an inactive arm do to the next directive?
7. Does a `#if` inside a multi-line block comment count as a directive?
8. Does a `#define` in one arm affect a later `#if`, and does a `#define` inside an **inactive** arm have any effect?
9. Can a `#if` appear inside a multi-line verbatim string, and is it a directive there?

Results go in `docs/preproc-directive-semantics.md`, a table in the style of `docs/preproc-define-undef.md`. The resolver's handwritten controls are derived from that table, **never** from the resolver's own output.

### Resolver self-test

Fixed cases, each with a handwritten expected mask, offsets and trace:

- overlapping `#elif` conditions;
- nesting;
- a group with no `#else`;
- repeated symbols;
- `not`;
- define/undef;
- a directive inside a string, a verbatim string spanning lines, or a comment;
- a `#define` inside an inactive arm, followed by a `#if` on that symbol;
- a directive line with a trailing comment;
- a directive's condition followed by a line that starts with an operator (the swallowed-line shape), with its handwritten condition extent;
- CRLF, a BOM, and end of file without a newline;
- a directive next to punctuation;
- non-ASCII identifiers;
- malformed directives.

There is also a mutation: switching `#elif` evaluation to independent (not first-match) must fail a named case.

## 2. The comparable form, extraction, and comparison

### The comparable form (`ir.py`)

`Node(kind, named, field, children, span)`, an ordered tree in which each child carries the field label its parent gave it.

- **Leaves** are terminals: named leaves and **anonymous tokens** (punctuation, operators, keyword children), each with its byte interval in the original file.
- **Inner nodes'** provenance is the ordered list of their leaves' intervals. It is computed from the leaves and never stored independently.
- **Extras** are left out of the structural tree and go to the trivia channel.

Because of masking, both sides are already in original-file coordinates.

### Extraction from the single-configuration parse (`reference.py`)

- Parse the masked text and walk it with a `TreeCursor`, so fields on anonymous nodes are captured. This is the same reason `tools/edge-census.c` uses a cursor.
- An ERROR or MISSING node gives `cannot-validate: reference-error`. It fails the gate unless `fixture-classes.tsv` classifies that exact (case, configuration) as a deliberate negative.
- A non-extra `preproc*` node in the single-configuration tree means the resolver left a directive in the text. It is reported as `resolver-leak`.

### Allowed normalisation

The only allowed normalisation is hand-listed and minimal. **A content-only container that is empty after lowering is removed.** Examples are `statement_block`, `declaration_body` and `var_body`, which the grammar wraps in `optional(field(...))`, so the single-configuration tree has no node where lowering would leave an empty shell. Each listed type cites its rule. Nothing else is normalised: no flattening, re-sorting or merging.

Removing empty containers cannot hide a handler that wrongly empties one *(gemini)*. A container can only become empty if its content was dropped, and dropped active content fails the byte-coverage check below, regardless of whether a contract covers the type. Each removal is also recorded in the report with the accounting reason that emptied it (`inactive-arm` or `directive`), so a removal with any other cause is an error.

### Checks (`compare.py`), per (file, configuration)

1. **Byte coverage.** The resolver does not tokenise AL, so this check is stated over bytes, not tokens *(sol)*. Every **significant** active byte, meaning every active byte that is not whitespace and not the leading BOM, must be covered by **exactly one** leaf or extra in the single-configuration tree, and by exactly one leaf or extra in the lowered tree. No leaf or extra in either may cover a masked byte. This is the same discipline `tools/validate_al_file.py` applies to one tree, applied to both sides and cross-checked. It catches dropped or invented material independently of structure. The resulting leaf interval lists of the two sides must then be equal, which is the token-level statement the structural check builds on.
2. **Structure.** An ordered tree comparison, with nodes **matched by provenance, not by text**. Identical `Foo();` statements in two arms are different nodes, and a comparison by set would turn "one missing, one duplicated" into a pass. Kinds of divergence: `missing`, `extra`, `kind`, `field`, `order`, `parent`, each reported with the deepest common ancestor and the first diverging path.
3. **Trivia.** The ordered (kind, interval) extras must agree three ways: the resolver's active events, the single-configuration tree's extras, and the lowered tree's extras for that configuration. Which node an extra is attached to is not compared.

**Discrepancy identity:** (file, configuration, check, kind, path), where the path is a list of (kind, field, first-leaf interval). The identity is stable across runs, so one discrepancy cannot replace another at the same count.

### Comparator self-test

Mutations are applied to a correct pair of trees, and each must fail with its **named** kind, not just "some failure":

- delete a node;
- duplicate a node;
- move a statement to another parent, keeping its type and span;
- swap `then_branch` and `else_branch`;
- rename a field;
- drop an operator;
- take the other arm's provenance for identical text;
- swap two siblings;
- remove a trivia event.

A clean control must pass.

## 3. Lowering engine

### Registry (`contracts.py`)

The registry is hand-written and authoritative. Each entry is `register(type, kind, handler, policy, hosts, witnesses)`, and a duplicate key raises: a Python dict literal would silently overwrite, just as a JavaScript object in `grammar.js` can.

Kinds:

| kind | meaning |
|---|---|
| `directive` | consumed; contributes no nodes |
| `trivia` | routed to the trivia channel |
| `token-alias` | a single token standing for an ordinary one, e.g. `preproc_split_begin` becomes a `begin_keyword` leaf with the same interval |
| `branch-select` | select the active arm and splice it into the parent under a declared policy |
| `assembler` | assemble configured constructs from pieces across arms and fragments |
| `fragment` | produces a typed partial result that a named assembler consumes |

The registry also covers special types without the `preproc` prefix, `else_table_relation_fragment` being the known case. Hidden helper rules that appear inside visible owners, such as `_preproc_end_guard`, get a named segment helper that those owners call.

**`node-types.json` is a census check, not the source of the list.** Checking a hand-maintained expectation against a generated declaration is valid, as in `tools/check-field-types.py`. Deriving the expectation from the generated file and then checking it against itself is not. *(astra, round 2.)* On every run:

1. Every named `preproc*` type in `node-types.json` has exactly one entry.
2. Every entry's type still exists.
3. Every handler resolves.
4. Every entry's required witnesses exist and were exercised in this run, on active content, not only inactive.
5. At runtime, an unregistered special node gives `cannot-validate: unregistered-type`. **There is no default handler.**

The named `preproc*` set is a census and not a complete detector of changes. New directive-bearing sites that arrive through hidden helpers or aliases are exactly what witnesses and the corpus runs exist to catch. The spec says so rather than claiming otherwise.

### Engine

`lower(node, ctx) → Lowered(nodes, fragments, accounting)`.

- **Ordinary nodes** lower as themselves: same kind, same fields, with the lowered children spliced into the same field slot.
- **Fragments** must reach a registered consumer of their kind. A fragment that reaches an ordinary node, or an unconsumed fragment at a declared assembly boundary, is an error: `unconsumed-fragment`.
- **`ctx`** holds the configuration, the resolver's directive groups, and a read-only chain of ancestors. There is no global bag of pending tokens: such a bag lets a lowering function satisfy an obligation with an unrelated later delimiter.

### Branch selection

This logic is shared by all `branch-select` entries.

- The node's `preproc_if`/`preproc_elif`/`preproc_else` children are matched **by byte offset** to the resolver's directive groups. The tree's `condition` fields are never evaluated.
- Each directive node in the tree is matched to a source directive, and its **extent** must equal the resolver's: the `#` offset, the keyword extent, the condition node's extent against the resolver's condition extent, and the directive ending at the resolver's end of line. A tree directive with no source directive, a source directive with no tree directive, or any extent disagreement is an error: `directive-mismatch`. The extent comparison, not the start offset, is what catches defect 4. *(sol)*
- The active arm's payload is returned with its field labels and anonymous tokens intact. It is never reduced to "the named children".

Each entry declares an **insertion policy** and the parent slots it may appear in:

| policy | meaning |
|---|---|
| `splice-repeat` | into a repeat slot (statements, body elements) |
| `single-slot` | exactly one node, or zero if the slot is optional; otherwise an error. No synthesised `begin … end` |
| `list-run` | into a comma- or semicolon-separated run, with the separators accounted for |

A policy that does not fit the actual parent is an error, not a guess. Being a "transparent container" is a hypothesis checked per type, not inferred from the name. Known exceptions *(astra, round 2)*:

- `preproc_conditional_permissions` can contain the property's terminating `;`;
- `preproc_conditional_expression_tail` continues **after** its `#endif`, so it is an expression fragment, not a conditional;
- `preproc_conditional_table_relation` can select an `else_table_relation_fragment` that completes an earlier relation.

Each `preproc_conditional_*` entry is checked against its rule in `grammar.js` before it is registered.

### Assemblers and fragments

Assemblers are ordinary Python functions. Fragment dataclasses (`RoutineTail`, `CaseCompletion`, `BlockCompletion`, `ExpressionContinuation`, …) are introduced only when a real consumer needs one.

Every contract that may rewrite a parent/field edge **names** the rewrite, for example `split-case-end`: *`following` statements become siblings of the reconstructed `case_statement`.* Any edge change not named by the running contract is an error.

Expression continuation (`preproc_conditional_expression_tail`, `preproc_operand_prefix`) needs composition that respects precedence. The assembler composes the fragments the tree recorded. The tree already labels them: `_expression_continuation` carries `operator` and `operand` fields. It **never reparses the selected source**.

This was disputed in review. gemini proposed reparsing the active expression slice with tree-sitter, to avoid writing operator-precedence composition in Python. It is rejected because reparsing with the same grammar returns exactly the single-configuration answer, so the check would test the parser against itself and hide a wrong grouping in the multi-configuration tree. The cost gemini identified is real, and is met this way instead: composition uses a **hand-written precedence table** taken from the compiler-verified precedence (`test/corpus/operator_precedence_test.txt`, whose groupings were established with `alc`), **not** from the grammar's `prec()` values. That keeps the assembler independent of the thing it checks. The table has its own self-test: each fixture grouping from `operator_precedence_test.txt` is recomposed from a flat operand/operator list and must match. AL has a small number of precedence levels and no user-defined operators, so this is a bounded table, not an expression parser.

### Accounting

Every handler returns a record of what it did with each leaf of its input:

- kept;
- omitted, with a reason (`inactive-arm`, `directive`);
- routed to trivia.

The engine asserts the records cover every leaf of the original node exactly once. A dropped or double-counted leaf is an error: `accounting`.

### Representation contracts (`representation.py`)

These run on the multi-configuration tree **before** lowering and before any empty wrapper is removed. Removing wrappers first would erase the evidence of defect 5.

Initial contracts:

Contracts are stated **per host slot and per configuration**, not as existence claims about a whole group *(sol)*:

- `preproc_conditional_var_block`, **in the slot between a routine signature and its body**: for each arm that has no `var_section`, the arm must contain at least one other **structural** child, otherwise the group's reading as a var block is unsupported in that arm's configuration. A group whose every arm is empty of structure is a `preproc_pragma_only` by definition, and is a violation. A group with `var` in its `#if` arm and only a pragma in its `#else` arm is legitimate, and a named positive control.
- `preproc_pragma_only` has **no structural children** in any arm. Its arms may be empty, or hold any extras (pragmas, comments, regions, defines), as the rule's own comment says. Comment-only and empty-arm cases are **named positive controls**, which the contract must pass. *(sol: "only pragma extras" would have flagged valid trees.)*
- Each split node's arms contain the pieces its contract names. For example, every `preproc_split_procedure` arm holds a complete `_procedure_header`.
- Tree directives and source directives correspond one-to-one.

Each contract has a mutation witness that must trip it and nothing else.

### Links from grammar.js (later milestone)

Each special rule gets a comment `// projection-contract: <id>` naming a stable contract id, not a function name. A check verifies that the comment sits on the intended rule and names a real contract. It only makes the contracts discoverable. It is not the authority: editing a rule and its annotation together would otherwise bless a changed meaning automatically.

## 4. Inputs, runner, baseline, gates

### Inputs

- **Fixtures (`fixtures.py`).**
  - Extracts every case from `test/corpus/*.txt` as (file, case name, source bytes, offset).
  - Reconciled against `tools/count_corpus_cases.py` **per file and by case name**, not by total. Two independent readers of the corpus format must agree, which also re-checks the silent-drop traps in CLAUDE.md.
  - Inputs are the cases that contain directives according to the **resolver**, never according to which trees contain `preproc` nodes: that would omit exactly the cases whose multi-configuration parse failed.
  - Deliberate negatives are classified per case and per configuration in `tools/config_oracle/fixture-classes.tsv`, with the expected outcome and a reason. Files are never skipped wholesale.
  - The fixtures are **input**. Their expected S-expressions play no part in the verdict.
- **Corpora.**
  - BC.History (`./BC.History`), DC (`./DC`), and BC 28.1 W1: `AL_BC28_ROOT`, defaulting to `H:/Git/BC28.1`, branch `bc28.1-w1` = `w1-28.1.49838.49886`, 16,928 `.al` files.
  - Discovered the same way, by resolver, not by tree.
  - The discovered set is written as a manifest with sha256 hashes.

### Runner

- Builds the parser once, before starting workers, via `tools/query_coverage/loader.ensure_library`. Its freshness stamp is extended to cover `src/*.h` (for example `src/unicode_id.h`), and concurrent builds are serialised.
- Distributes one file per task to a worker pool. The original tree is parsed once per file. Only one original tree plus one configured tree are held at a time, with iterative traversal: `qc.py` documents what retaining corpus trees costs.
- Each worker returns one record per (file, configuration) with a status: `pass`, `discrepancy(id)`, `representation-violation(id)`, or `cannot-validate(reason)`.
- The parent asserts it received **exactly** the expected set of (file, configuration) records. A dropped worker, file or configuration is `incomplete`, never a quieter pass. This is the same discipline as `tree-harness.sh`'s per-chunk assertions.
- **Exit codes:**
  - `0`: clean;
  - `1`: a new or unexplained discrepancy, a representation violation, or a stale baseline entry;
  - `2`: could not run, or incomplete (missing corpus, build failure, dropped records).
- **Reports:** `tools/config_oracle/reports/findings.jsonl` and `summary.md`, with the key line *"N new discrepancies, M baselined, K configurations not validated (reasons)"*. The header records identities (sha of `grammar.js` and `src/`, the BC.History HEAD, the BC28.1 commit, and a manifest hash for DC, which is not a git repository), so a release can cite a specific full run.
- Throughput is **measured** in milestone 1. The full tier's time budget is set from that measurement, not from an estimate.

### Baseline (full tier only)

`tools/config_oracle/baseline.tsv` holds exact discrepancy ids, each with a required note naming its investigation. **Never** a file, a node type, a count or a cluster. *(astra, round 2.)*

- A run fails on any discrepancy id that is not in the baseline.
- A run fails on any baseline id that no longer occurs. The entry must be removed, which records the fix.
- A run fails on an entry without a note.
- `cannot-validate` and `representation-violation` can never be baselined.
- **The quick tier has no baseline.** A fixture discrepancy always fails.
- There is no automatic accept. `propose` writes candidate ids to a separate file for review and never modifies `baseline.tsv`.

**Each discrepancy is an investigation, not a presumed grammar fix.** The cause may be the grammar, the resolver, a lowering function, a wrong contract, or an invalid configuration. Forcing every difference into a grammar change would bend the parser to satisfy a buggy oracle. The first target is zero *unexplained* discrepancies. The second is an empty baseline, with every grammar defect fixed. *(astra, round 2; this replaced "each discrepancy becomes a grammar fix".)*

### Gates

- **`validate-grammar.sh` Step 5e**, on every run: `python -m tools.config_oracle run --tier quick`. It runs the self-tests, registry census, representation contracts and fixture differential, and needs no corpus.
- **`validate-grammar.sh --full` Step 6b**: `--tier full` over all three corpora, with **identical logic**; only the input scope differs. A missing corpus **fails** the step with exit 2. It does not inherit the warn-and-skip at `validate-grammar.sh:538` that the query-coverage step uses, because this run was explicitly requested over three corpora.
- **CI:** `pytest tools/config_oracle/tests` **and** `python -m tools.config_oracle run --tier quick`. CI runs the gate itself, not only its unit tests, closing the gap that exists for `qc` today (`.github/workflows/ci.yml:79-101` runs only `pytest tools/query_coverage/tests`).
- **`tools/gate_selftest.py`:** new cases proving that Step 5e fails on an injected discrepancy, a dropped configuration and an unregistered type, and that the quick tier cannot pass with a baseline present.

The oracle is a Python module and adds no `.sh` files. If one is added later, it falls under `tools/check-exec-bits.sh`.

## 5. Proving it can fail

### Replaying historical defects

A fixture that now passes is a regression guard, not proof that the oracle detects anything. For each silent defect in the Problem section:

- build the parser from **the commit just before the fix** into a temporary library;
- run the oracle over the fixture that the fix added;
- require the **expected** check and kind.

| # | Defect | Expected detection |
|---|---|---|
| 1 | `CRMSetupDefaults` `end else begin` over `#endif` | structure: `parent` |
| 2 | `else #if … #else begin … end; #endif` lost `code_block` | structure: `missing` / `parent` |
| 3 | `PREPROC_SPLIT_END` stopped by a trailing comment | structure |
| 4 | `#if`/`#elif` condition swallowed the next line (`c6b8107`) | `directive-mismatch` |
| 5 | pragma block as `preproc_conditional_var_block` (`04ff498`) | representation contract, and **not** structure |
| 6 | `#elif` absent from `preproc_split_code_block_end` | structure |

Replay 6 is **not** an example of the silent class. The grammar's own comment on `preproc_split_code_block_end` says the defect left a MISSING `end_keyword`, which kept the error gate honest. It stays in the table as a structural replay, but is not counted as evidence that the oracle finds what the error gates cannot. *(sol)*

Every replay also requires that **no earlier `cannot-validate` masks it**: a replay whose pre-fix run stops at `reference-error` or `resolver-leak` has not shown the expected detection.

The exact pre-fix commits are identified during planning. A defect whose pre-fix commit cannot be built, or that has no fixture, gets a hand-built bad tree instead, **labelled as such**: that exercises the comparator, not the whole instrument.

### Coverage of rare types

About 21 special types never occur in BC.History. The frequency of a type in production sets the order of work, not the standard it is held to. Every registered type needs a **witness matrix**:

- fixture case id;
- configurations exercised;
- the special type actually produced, with non-empty active payload;
- variants covered: the first arm, a later `#elif`, `#else`, and no arm selected; empty and non-empty; shared and conditional pieces; terminator inside or outside the directives; nesting; identical content in both arms; ownership that depends on the configuration;
- the structural assertions;
- the mutation tests that tell right from wrong.

A handler that has only run on inactive content has not been tested.

### Deterministic transformations

About a dozen parameterised tests over ordinary AL:

- wrap complete constructs in a conditional;
- duplicate an arm's content;
- negate a condition and exchange the arms;
- add comments and pragmas at scanner-sensitive boundaries (between a split `begin`/`end` and its directive, the lookahead sites in `src/scanner.c`);
- compose split headers with split tails.

These do not replace deliberately built witnesses for the assemblers: wrapping whole statements never exercises case-end redistribution or report-brace ownership.

## Milestones

Each milestone has an exit condition that must be **demonstrated**, not claimed.

Both reviewers found the first milestone too easy *(sol, gemini)*. It now has to prove the resolver on real files and prove one hard assembler before anything else is built on top.

1. **The resolver on real files, and a slice that already checks something.**
   - Scope: the probes and `docs/preproc-directive-semantics.md`; the resolver and its self-test; `ir.py`, `reference.py` and `compare.py` with the comparator mutations; branch selection for `preproc_conditional` and `preproc_conditional_statement`; `directive-mismatch` with extents; the var-block and pragma-only representation contracts with their positive controls; runner accounting.
   - Plus **one hard assembler, `split-case-end`**, and **one scanner-sensitive shape**, a `PREPROC_SPLIT_END` followed by a trailing comment. Each has a clean positive control and a false-positive control. The scanner-sensitive shape has replay 3. `split-case-end` has no historical silent defect to replay, so its negative is a hand-built bad tree with `following` placed inside the `case_statement`, labelled as such, plus a grammar mutant that drops the `following` field.
   - Plus the **resolver and single-configuration parse over every `#if` file in BC.History, DC and BC 28.1**. This needs no lowering. The exit is zero `cannot-validate: resolver-*` and zero `reference-error` over production flat AL, or each one investigated and classified. Resolver defects must surface here, not at milestone 5. *(gemini)*
   - *Exit:* replays 2, 3, 4 and 5 caught with the expected kind, each without an earlier `cannot-validate`. Replay 5 is caught by the representation check and **not** by structure, which proves which check found it. The positive controls pass. **Elapsed time and peak memory** are measured and recorded. *(sol)*
2. **The remaining hard shapes.**
   - Scope: split procedure with every tail form; a report-brace ownership case; expression continuation with the precedence table and its self-test.
   - *Exit:* each has its witness matrix and edge-rewrite contracts, and replays 1 and 6 are caught. If the fragment design fails here, it is redesigned before the remaining handlers are written.
3. **Everything else, in order of frequency.**
   - *Exit:* every special type registered, with no "unsupported" entries; the witness matrix is complete; the deterministic transformations pass.
4. **The quick gate becomes mandatory.**
   - Step 5e, CI and `gate_selftest` cases.
   - *Exit:* the fixture tier runs with zero discrepancies, zero `cannot-validate` and no baseline file; every gate-integration failure mode is tested.
5. **The full gate, staged.** *(sol)*
   - First, a run over the three corpora with **no baseline and no gate**, recorded: completeness, false positives, time and memory. The exact-id baseline and Step 6b are built only after that run shows the model is tractable on production code. The `grammar.js` contract annotations come after that, not before.
   - Then all three corpora, Step 6b.
   - *Exit:* every (file, configuration) is accounted for, and every discrepancy is investigated and classified. Grammar defects are fixed in their own commits with fixtures, and the baseline is empty. CLAUDE.md is updated only then.

## Definition of done

- `validate-grammar.sh --full` passes the oracle over BC.History, DC and BC 28.1 W1, with an empty baseline.
- The quick tier runs in CI.
- CLAUDE.md documents the oracle as a configuration-consistency oracle and states its limit: both parses share one grammar.

## Review points considered and rejected

Recorded so they are not re-raised without new evidence:

- *"There are 60 named `preproc*` types, not 74"* (gemini). Parsing `src/node-types.json` gives 74 top-level named types; the grep counted references.
- *"`Foo`, a `#if X` line, then `= 1;` is a false positive"* (gemini). If the two parses disagree on that text, the grammar and the compiler's view differ. That is a finding the oracle should report, not noise to suppress.
- *"Masking with long runs of spaces risks scanner lookahead limits"* (gemini). The scanner's whitespace and comment loops in `src/scanner.c` have no length bound. The deterministic transformations include a long inactive arm as a control anyway.
- *"A statement redistribution after a split `end` is a false-positive trap"* (gemini). That redistribution is exactly what the `split-case-end` contract defines. A disagreement there is the check working.
- *"Allow reparsing expression slices"* (gemini). Rejected in section 3; the precedence table replaces it.
- *"Drop the import-isolation test as ceremony"* (sol, gemini). Kept, because it is cheap, but stated as necessary rather than sufficient.

## Out of scope

- A general-purpose AL generator or fuzzer.
- Symbolic (SAT-based) enumeration of configurations. 64 per file is the measured ceiling.
- Changing the grammar to ease lowering. Candidate improvements are filed separately, for example named segment fields on `_preproc_end_guard`, whose statement runs before and after `end` are currently told apart only by position.
- Fixing the stale comment above `_preproc_branch_statement`, which says `code_block` is deliberately absent from `_statement_inner` while `grammar.js:3968` includes it. It was found during this design, belongs in its own small commit, and does not block this work.
