# Config oracle — milestone 2 results

Measured on 2026-09-28, grammar `2c3928c57fe98fc7` (report header; HEAD `6b94cd9`,
branch `feat/config-oracle-m2`). Corpora: BC.History `87e7d2a19d2`, DC `5e67e5b9c`,
BC 28.1 W1 `4fc2ccf16` (`H:/Git/BC28.1`), BCApps 29.0 `e16d6c30`
(`H:/Git/BCApps-29.0`). Every run below was wrapped in `./tools/ts-lock.sh`.

## Resolve sweep

```
./tools/ts-lock.sh python -m tools.config_oracle run --tier resolve \
  --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0 \
  --report tools/config_oracle/reports/resolve-m2
```

Summary: 14,662 configurations checked, `pass` 14,655, `cannot-validate` 7
(`reference-error:error` 7), 0 `resolver:*`, 0 internal errors; 64,624 inputs without
conditional directives; `elapsed: 482.4s` inside `runner.run` (13 m 44 s wall,
including corpus read and lock); peak RSS 1,256 MiB (max over processes); exit code 1.
The exit code is 1 because the resolve tier has no classification file: the 7 records
are classified here, not in `fixture-classes.tsv`, which covers fixtures only.

| Corpus | `.al` files | with `#if` | configurations | pass | `reference-error:error` | `resolver:*` |
|---|---|---|---|---|---|---|
| BC.History | 15,358 | 1,281 | 3,120 | 3,120 | 0 | 0 |
| DC | 1,352 | 44 | 92 | 92 | 0 | 0 |
| BC 28.1 | 16,928 | 1,061 | 2,580 | 2,580 | 0 | 0 |
| BCApps 29.0 | 36,717 | 3,345 | 8,870 | 8,863 | 7 | 0 |
| **total** | **70,355** | **5,731** | **14,662** | **14,655** | **7** | **0** |

File total checked: 64,624 + 5,731 = 70,355, the sum of `.al` files under the four
roots. The three older corpora give the same `#if` file and configuration counts as
milestone 1 (1,281 / 44 / 1,061 and 3,120 / 92 / 2,580), all still `pass` after the
BC 29 fixes and G1 to G5.

The two known BCApps parse-error files:
- `Apps/DE/EDocumentDE/app/src/EDocumentServiceDE.PageExt.al` (deferred-work item 10):
  all 4 configurations `pass`. Each configuration on its own is valid AL; only the
  multi-configuration parse fails, and the resolve tier does not use it.
- `Layers/APAC/Tests/SINGLESERVER/ERMPurchaseReportsIII.Codeunit.al` (invalid source):
  it has no conditional directive, so it is one of the 64,624 flat inputs and the
  resolve tier does not check it.

No `#if`/`#elif` line in BCApps 29.0 uses `&&` or `||` (grep), so deferred-work item 9
still has zero production impact across all four corpora.

### Classification

One cluster, 3 files, 7 configurations. Every record was examined; none was sampled.

| Cluster | Records | Files (configuration) | Classification | Evidence |
|---|---|---|---|---|
| Table field opened inside `#if not CLEANSCHEMA<n>` and closed after `#endif` (the `preproc_split_table_field_open` family) | 7 | `Apps/IN/INFADepreciation/app/src/table/FixedAssetShift.Table.al` (`CLEANSCHEMA26=1`); `Apps/W1/SalesOrderAgent/app/src/Setup/SOASetup.Table.al` (`CLEAN28=0,CLEANSCHEMA28=1`, `CLEAN28=1,CLEANSCHEMA28=1`); `Layers/FR/BaseApp/Bank/BankAccount/BankAccount.Table.al` (all four `CLEAN27`×`CLEAN28` with `CLEANSCHEMA31=1`) | **invalid source in that configuration** | See below. |

Every one of the 7 records has `CLEANSCHEMA<n>=1`, and every configuration of these
files with that symbol undefined is `pass`. The first error offset sits right after the
field's closing `}`: FixedAssetShift line 206 (after `#if` 195 / `#endif` 205), SOASetup
line 42 (`#if` 28 / `#endif` 40), BankAccount line 1087 (`#if` 1032 / `#endif` 1085).
With the symbol defined, the resolver removes the field header and `{`, but not the
`}` after `#endif`. That `}` closes `fields` early, so the following `field(...)` lines
land outside any section. The grammar comment on `preproc_split_table_field_open`
names these three files and says that only the `#if`-taken configuration compiles.

Four-way alc probe, re-run for this task on self-contained repros of all three shapes:
FixedAssetShift (the body continues with a trigger after `#endif`), SOASetup (a nested
`#if not CLEAN28 … #else … #endif` before the outer `#endif`), and BankAccount (a nested
`#if CLEAN28 … #else` whose else arm carries a trigger). The harness was
`probe_alc.compile_probe`, with the flat text taken from `directives.resolve`.
Controls: sanity ACCEPT, garbage REJECT (AL0183, AL0198).

| Shape | schema symbol undefined, split / flat | schema symbol defined, split / flat |
|---|---|---|
| FixedAssetShift (`CLEANSCHEMA26`) | ACCEPT / ACCEPT | REJECT / REJECT (AL0104, AL0162, AL0198) |
| SOASetup (`CLEANSCHEMA28`), `CLEAN28` undefined and defined | ACCEPT / ACCEPT (both) | REJECT / REJECT (AL0104, AL0198) (both) |
| BankAccount (`CLEANSCHEMA31`), `CLEAN28` undefined and defined | ACCEPT / ACCEPT (both) | REJECT / REJECT (AL0104, AL0198) (both) |

The compiler rejects exactly the configurations the oracle reports, and accepts every
configuration the oracle passes. The oracle and the grammar are both right here: this
is Microsoft source that nobody builds with `CLEANSCHEMA<n>` defined.

### Fixes made

None. No resolver defect was found (0 `resolver:*` records), and no grammar defect
(every `reference-error` is a configuration alc also rejects).

### Findings for Task 18

None from the resolve sweep.
