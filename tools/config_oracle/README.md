# Config oracle

`python -m tools.config_oracle` validates that every configuration of an `#if`-bearing AL
file lowers to one reading, against the resolver and (in the full tiers) against alc. It is
validate-grammar.sh Step 5e and the CI job `config-oracle`. This file holds the reference
material carried out of `CLAUDE.md` on 2026-10-21; the one-line commands stay there.

## Tiers and exit codes

```bash
python -m tools.config_oracle run --tier quick
#   (a) registry census, (b) self-tests, (c) fixture differential, (d) condition structure
#   (tree condition vs the resolver: ast + truth table); ~2-3 s (docs/performance-baselines.md)
./tools/ts-lock.sh python -m tools.config_oracle run --tier full|resolve \
    --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0
#   full ~22 min, resolve ~8 min
python -m tools.config_oracle replay
#   historical-defect replays; ~80s cold, ~10s warm
```

Exit codes, every tier: **0** clean, **1** finding, **2** cannot run.

Gates of the full and resolve tiers:
- **0** = every refusal is in `production-classes.tsv` (still NOT validated);
- **1** = unclassified refusal, stale entry, discrepancy, corpus HEAD not the one the tsv
  records, a modified/deleted/renamed tracked `.al`, an untracked `.al` not recorded
  (`# corpus-untracked`) or with another sha256, a recorded one gone;
- **2** = unlabelled/empty/overlapping root, malformed tsv (e.g. `: host` without `:<slot>`).

A fixture cannot-validate record must be classified in
`tools/config_oracle/fixture-classes.tsv` (negative / invalid-config need alc evidence;
`debt(<owner>)`); an entry matching no record is stale and fails.

A boundary that depends on the configuration is a one-reading violation and is refused (B12,
`docs/deferred-work.md` item 36); fragment runs are B13 (item 37).

## Lowering modules added by the B-phases

- `lowering/conditional_lists.py`: the family-schema registry `FAMILIES` for B7b-1 strict
  conditional lists (region adapter, item kinds, separator, alc cardinality; split-tree
  validation and per-configuration `item (sep item)*`). A new host needs a `FAMILIES` entry
  and a `contracts.py` entry (`docs/superpowers/plans/2026-10-07-b7b-1-strict-conditional-lists.md`).
- `lowering/case_terminators.py` (B7b-3): `CASE_SEMI` marking, `case-terminator-attach`,
  decoration validation, `lowering:one-reading` for the case-`else` reading of spec 4.4.
- `lowering/move_args.py` (B7b-3): one adapter for the move header's routes 1-3, dispatched
  by host kind.
- `lowering/engine.py` `absorb_arm_terminators`: four rewrites, `empty-body-terminator`,
  `filled-terminator`, `orphan-terminator` (B7b-3), beside B7b-0's `arm-terminator`.

## The has_error model test

`tests/test_directive_eol.py` is the model for a pytest that asserts `root_node.has_error`
for a hidden token: the only gate that sees a MISSING node for a `_`-prefixed token
(`CLAUDE.md`, "Gates that catch what the obvious check misses").

## After a parser or oracle change

After ANY change to `src/parser.c`, `src/scanner.c` or `tools/config_oracle`, the B7a matrix
must be re-fingerprinted: `./tools/ts-lock.sh python -m tools.b7_audit assert --refresh`, a
full `run`, then `report` (`docs/b7-separator-continuation-matrix.md`). The committed matrix is
valid only at the parser/oracle hashes its evidence header and `tools/b7_audit/assertions.tsv` record.
