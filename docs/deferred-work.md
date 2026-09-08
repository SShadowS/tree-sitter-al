# Deferred work

Open items carried past 4.0.0, with **how each one was established** so the next
person can tell a measurement from a recollection. Nothing here is a "known
limitation" in the sense the project philosophy forbids — every item is a defect
with a known shape, parked because the release shipped, not because it was judged
unfixable.

**Re-verify before acting on any of these.** They were measured against the 4.0.0
tree; several touch areas the release itself changed. An item whose probe no longer
reproduces is finished — say so and delete the entry.

---

## The instrument these items depend on

Most items below are "does the AL compiler accept this?" questions, and the answer
is only trustworthy from `al compile` (see CLAUDE.md, *Validating AL Syntax
Questions*). One extra rule applies to every `#if`-related probe:

**alc does not parse inactive branches.** A file with `#if FOO` … `#else` … `#endif`
must therefore be compiled **four** ways before a verdict means anything:

| config | what it proves |
|---|---|
| flat, symbol undefined | the else-branch text is valid on its own |
| flat, symbol defined | the then-branch text is valid on its own |
| split, symbol undefined | alc accepts the split file taking the else branch |
| split, symbol defined | alc accepts the split file taking the then branch |

`preprocessorSymbols` in `app.json` selects the config. A single-config probe is
worthless and has already produced one false ACCEPT and one false REJECT in this
project's history — one of which reached a committed fixture before it was caught
(`ef4cc7e`). `AL1021` appears in the log of successful runs too; judge by whether
`out.app` was produced, not by the log being empty.

---

## 1. Six separator positions have no preprocessor host

**Established:** an audit that enumerated all 26 separator sites in `grammar.js`,
mapped each to its owning rule, and probed the unhosted ones against `alc`. Done
during 4.0.0, after the run/group rework in `812ace7`. Not re-run since.

`812ace7` made every comma-separated list a sequence of **runs** with preproc
**groups** between them, which is what lets a `#if` branch supply the separator its
neighbour is missing. Five families got that treatment. These six positions did not,
so a `#if` at the separator is an `ERROR` here while `alc` accepts the file:

- `argument_list`
- `parameter_list` (the `;`-led form)
- `implements_clause`
- `option_member_list`, **comma-leading** shape (see item 2)
- key field list
- `ml_value_list`

Per-host enumeration is still the tractable approach at this count — the
scanner-classification design sketched during the release is an architecture
upgrade, not a prerequisite.

## 2. A rule existing is not the same as the shape being covered

**Established:** by construction, during the same audit. This is the reason item 1
says "shape" rather than "site".

`preproc_conditional_option_members` exists and handles

```al
X, #if FOO Y #endif
```

and **errors** on

```al
X #if FOO , Y #endif
```

Same program, same `alc` verdict, different side of the comma. Every host needs
**both** placements pinned by a fixture, or the next audit will read the rule's
existence as coverage — as this one nearly did.

## 3. The dangling-operator residual

**Established:** measured directly, and pinned as a fixture.

`test/corpus/preproc_dangling_operator_known_wrong_test.txt` asserts a tree this
project believes is **WRONG**. `#if FOO and` with the operand on the following line
is absorbed into `condition: (preproc_and_expression FOO BAR)` with zero `ERROR`
nodes; `alc` rejects the same input in both configs with `AL0629`. The newline
terminator added to `preproc_if` cannot fire while the condition is grammatically
incomplete.

The fixture is a **tripwire**: its header says the expectation is the defect, so a
failure there most likely means someone fixed the parser and should update the
fixture — not that they broke it. Do not regenerate it with `tree-sitter test -u`
without reading the header.

## 4. `_expression_statement` accepts any expression as a statement

**Established:** two measured attempts, both reverted. Their diffs are stashed with
the messages `failed: _expression_statement restriction (BC 35.7%)` and
`failed: fail-loud backstop (BC 33.3%)` — find them by message, since `stash@{N}`
indices shift whenever any stash is dropped.

`_expression_statement: $ => $._expression` lets a bare literal stand where a
statement belongs. Narrowing it to call/member forms dropped BC.History to 35.7%;
a wider set with `prec(20)` and a declared conflict gave 33.3%. The unexplored lead,
recorded in the rule's own comment in `grammar.js`, is that the rule sits in the
`inline` array — removing it there changes what the conflict resolution can see.
Both prior attempts left it inlined.

## 5. Gate self-test: 5 of 23 cases had never been green on a runner — RESOLVED 2026-09-09

**Established:** output captured from run `31548406743`, job `93965657846`
(`gh run view <id> --job <id> --log`). Final line: `gate-selftest: 17 passed,
5 failed, 1 skipped, of 23 selected`. The five fell into two clusters — the whole
step-6 AL-parsing path dead on the runner (3 cases, including the harness's own
control `step6-clean-corpus-passes`), and both ts-lock guard cases reporting
`holder A never acquired the lock`.

**Resolved:** the two clusters were **one cause**, not two bugs. Four scripts were
committed as mode 100644: `parse-al-parallel.sh`, `tools/ts-lock.sh`,
`tools/gate-fixtures/ts-lock-release-guard.sh` and
`tools/gate-fixtures/json-offsetting-loss/tree-sitter`. The harness runs each gate
through `bash`, so the gates themselves did not need the bit — but
`validate-grammar.sh` Step 6 execs `./parse-al-parallel.sh` directly (Linux:
`Permission denied`, exit 126 → "no readable summary" → cluster A), the ts-lock guard
execs `../ts-lock.sh` with stderr silenced (holder A never creates the lock → cluster
B), and PATH lookup skips a 100644 shim (the real `tree-sitter` runs, nothing is
injected, `pap-offsetting-loss` exits 0). None of it reproduces on Windows, where the
repo is written: `core.fileMode=false`, so index modes are invisible to `ls`, to
`git status` and to Git Bash, which runs a 644 script. The same class had already
hit `tools/check-wasm-fresh.sh` once (bed960a) and was fixed for that one file.

Established by reproducing in a fresh Linux clone (WSL, tree-sitter 0.27.0), which
checks out index modes: byte-identical failure messages to CI, then 21/23 passing
after `git update-index --chmod=+x` on every tracked `*.sh` and shim. The control
still exited 1 for a second reason hidden behind the first: Step 9 (WASM freshness,
added in 4.0.1 after this harness) failed in the scratch copy with
`missing tree-sitter-al.wasm`, because the scratch never carried the wasm or its
stamp. Both are copied now, and Step 9 gained its own mutation case,
`step9-wasm-stale`. Final: 23 passed, 1 skipped (no C toolchain), of 24.

The assertions were not relaxed. The gate for the class is `tools/check-exec-bits.sh`
(validate-grammar.sh Step 10, and its own CI step): it reads the git index, so it
answers the same on every platform. Full write-up in the CHANGELOG entry for the
release after 4.1.0.

## 6. Three uncovered bytes: a doubled UTF-8 BOM

**Established:** measured at the 4.0.1 release with a leaf-walking gap scanner
over both corpora — 36,852 files, exactly 3 non-whitespace bytes covered by no
leaf, all in
`DO.Support/BC/BaseApp/Test/Tests-VAT/ERMVATServCharge.Codeunit.al`. BC.History is
clean at 0.

The file opens with **two** UTF-8 BOMs, at offsets 0 and 3. The first is file
preamble and correctly belongs to no node; the second is equally not AL source,
but it is not at offset 0, so nothing excludes it and no node claims it. Strictly,
the CST is not lossless over those 3 bytes.

Deliberately not "fixed" by widening the scanner's BOM exclusion: that would hide
it rather than decide it. The open question is what the tree *should* do with a
second BOM — alc's verdict on the file has not been probed, and that verdict
decides whether this is an extra to absorb or text to surface.

Two traps that any re-measurement will hit, both of which produced a wrong answer
first:

- **Excluding the leading BOM is mandatory.** Without it, 1,788 BC.History files
  report 3 bytes each (5,364 total) and the corpus looks broken.
  `tools/validate_al_file.py`'s `_significant()` excludes it for the same reason.
- **An `ERROR` node covers its own bytes**, so feeding the scanner deliberately
  broken AL produces *no gap* and proves nothing. The control that works is a
  build that ignores anonymous leaves: it must report gaps on a file the real
  scanner calls clean (22 bytes on a 6-line codeunit, 213 on a real
  PermissionSet).

## 7. Adopt the split-matrix probe tooling under `tools/`

**Established:** the method (see *The instrument*, above) exists and works; the
tooling that automates it was written ad hoc during the release and never landed.

Automating the four-way compile is what makes items 1–3 cheap to re-verify. It
caught one of its own case-construction bugs during the release — a probe that
would otherwise have been filed as "alc rejects Implementation splits", which is
false.

---

## Longer-lived proposals, tracked separately

- [`python-bindings-modernization.md`](python-bindings-modernization.md) — the
  Python bindings still return a raw pointer via `PyLong_FromVoidPtr`; modern
  `tree-sitter` (0.24+) expects a `PyCapsule`. Written against `tree-sitter==0.25.2`
  as used by `code-graph-rag`.
- [`improvements-for-owned-ir-consumer.md`](improvements-for-owned-ir-consumer.md) —
  proposals from a downstream consumer that lowers the CST into an owned IR.
  **Baseline is v3.0.1 (`eeb2839`)**, so parts of it are stale: 4.0.0 removed four
  never-populated fields and changed keyword node shape. Diff it against the current
  `node-types.json` before treating any item as open.
- [`history-scanner-token-drop-v3.3.0.md`](history-scanner-token-drop-v3.3.0.md) —
  **historical.** The byte-gap measurement taken against the released v3.3.0 tag
  that started the losslessness work. Kept because the *method* is reusable, not
  because the numbers are current; 4.0.0 fixed the classes it describes.
