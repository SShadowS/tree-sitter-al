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

## 5. Gate self-test: 5 of 23 cases have never been green on a runner

**Established:** output captured from run `31548406743`, job `93965657846`
(`gh run view <id> --job <id> --log`). Final line: `gate-selftest: 17 passed,
5 failed, 1 skipped, of 23 selected`. Root cause still not fixed, but the five are
no longer anonymous and they fall into **two clusters, not five problems**:

**Cluster A — the whole step-6 AL-parsing path is dead on the runner (3 cases).**

```
FAIL  step6-broken-al-file        output never said 'AL parsing failed'; output never said 'error file(s)'
FAIL  step6-clean-corpus-passes   exited 1; expected 0; output never said 'AL parsing:'; ...
FAIL  pap-offsetting-loss         exited 0; expected non-zero; output still said 'Success rate'
```

`step6-clean-corpus-passes` is the harness's own **control** — it injects nothing and
asserts a clean corpus PASSES. A failing control means the machinery does not run at
all on the runner, so the other two are downstream of it and prove nothing on their
own. Start here: the expected `AL parsing:` line is absent entirely, which points at
`parse-al-parallel.sh` not executing rather than at the detection logic being wrong.

**Cluster B — the ts-lock guard cases never acquire the lock (2 cases).**

```
| ts-lock-release-guard: FAIL - holder A never acquired the lock
FAIL  tslock-release-guard-detects
FAIL  tslock-release-guard-passes
```

Both failures share that one line, so this is one bug: holder A cannot take the lock
in the runner's environment. Neither case says anything about the guard's real
behaviour until that is fixed.

The job had been red long enough on `main` to be read as background noise, which is
the failure mode a gate must never have. **Do not "fix" these by relaxing the
assertions** — two of the five are controls, and a control that passes vacuously is
worse than a red job.

## 6. Adopt the split-matrix probe tooling under `tools/`

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
