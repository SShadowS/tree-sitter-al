# Gate fixtures

Fault injectors for testing the **validation gates**, not the grammar.

These are **fixtures, not utilities**. Nothing in the build, the test suite or
`validate-grammar.sh` calls them. Each is a `tree-sitter` shim that only takes
effect when a caller deliberately puts its directory earlier on `PATH`, and each
passes every un-targeted invocation through to the real binary byte-for-byte,
preserving its exit status.

They exist because a gate that reports success without having examined anything
is invisible from the outside: the only way to know a gate works is to break the
thing it watches and confirm it says so. Each fixture below is one
(gate, injected defect, expected failure) row.

## Fixtures

### `offsetting-loss/` — a loss the global count cannot see

One chunk emits N trees fewer, another emits N more (duplicating its last), so
the corpus total reconciles. `tree-sitter` exits **0** throughout, so no amount
of checking return values catches it. Only counting the work per chunk does.

Knobs: `FIXTURE_LOSE_CHUNK` (default `chunk_0001`), `FIXTURE_GAIN_CHUNK`
(default `chunk_0002`), `FIXTURE_DELTA` (default 3).

```bash
R=./BC.History/PowerBIReports                 # 280 files
F="$PWD/tools/gate-fixtures/offsetting-loss"
PATH="$F:$PATH" CHUNK_SIZE=100 ./tools/tree-harness.sh snapshot "$R" /tmp/snap
```

With `CHUNK_SIZE=100` the corpus splits 100/100/80 and the fault makes it
100/97/83 — still 280.

| gate | verdict |
|---|---|
| `tree-harness.sh` **before** `055eb41` | `snapshot of 280 trees`, then `VERIFIED — all 280 parse trees byte-identical to snapshot`, exit 0 |
| `tree-harness.sh` **at/after** `055eb41` | `chunk chunk_0001 produced 97 trees for 100 files` / `tree-sitter status: 0` / `desynced — refusing to report on an incomplete tree set`, exit 1 |
| `parse-al-parallel.sh` | `Parsed OK: 280, Errors: 0, Success rate: 100.0%` — **does not detect it** |

What the pre-`055eb41` VERIFIED was covering, measured against a clean run of
the same corpus:

| | clean | faulted |
|---|---|---|
| manifest sha256 (first 16) | `1c59235923d25904` | `0496b5c078eed1c6` |
| rows carrying another file's hash | 0 | **82 of 280** |
| distinct tree hashes | 279 | 276 |
| trees present in a clean run but absent entirely | — | **3** |

Three files were never opened, in either the snapshot or the verify run.

### `json-offsetting-loss/` — the same loss, for a caller that counts records

`offsetting-loss/` splits its input on `(source_file` markers, so it only works
against a caller that asks for trees. `parse-al-parallel.sh` now counts with
`tree-sitter parse -q --json-summary`, which emits no trees at all — pointed at
that, the tree fixture finds nothing to trim and **passes the stream through
unchanged, injecting no fault whatsoever**. A gate test that injects nothing is
a tautology, so this fixture does the same job on the JSON: one chunk emits
DELTA records fewer, another DELTA more, and the corpus-wide total still
reconciles. `tree-sitter` exits **0** throughout.

Knobs: `FIXTURE_LOSE_CHUNK` (default `chunk_0001`), `FIXTURE_GAIN_CHUNK`
(default `chunk_0002`), `FIXTURE_DELTA` (default 3).

```bash
F="$PWD/tools/gate-fixtures/json-offsetting-loss"
PATH="$F:$PATH" ./parse-al-parallel.sh <40-file-corpus> . 4 10
```

| gate | verdict |
|---|---|
| `parse-al-parallel.sh` **before** the JSON count | `Parsed OK: 40, Errors: 0, Success rate: 100.0%`, exit 0 |
| `parse-al-parallel.sh` **after** | `chunk chunk_0001 produced 7 parse records for 10 files` / `3 file(s) in this chunk were never parsed` / `chunk chunk_0002 produced 13 parse records for 10 files` / `3 more record(s) than files`, exit 1 |

Both chunks are named, and `tree-sitter exit=0` is printed beside each — the
point being that no amount of return-value checking finds this, and neither
does the global total, which still comes to 40.

### `al-corpus/` — a small AL corpus that is not BC.History

Six hand-written AL files (table, page, codeunit, enum, interface, and one with
a `#if`) so the gate self-test can exercise `parse-al-parallel.sh` and
`validate-grammar.sh --full` **in CI**, where `BC.History` is gitignored and
absent. `tools/gate_selftest.py` copies them into a scratch corpus and, for the
negative cases, adds a deliberately unparseable file alongside.

Not a grammar-coverage corpus and not a substitute for BC.History: its job is
to be a *countable* set of files, so a gate that miscounts can be caught.

### `chunk-parse-failure/` — a chunk that produces nothing

One chunk's `tree-sitter` invocation fails outright and emits no trees: the
wholesale loss that a caller writing `tree-sitter parse ... || true` swallows.

Knob: `FIXTURE_FAIL_CHUNK` (default `chunk_0001`).

```bash
F="$PWD/tools/gate-fixtures/chunk-parse-failure"
PATH="$F:$PATH" CHUNK_SIZE=100 ./tools/tree-harness.sh verify "$R" /tmp/snap
```

| gate | verdict |
|---|---|
| `tree-harness.sh` **before** `055eb41` | `tree count mismatch: 180 trees for 280 files` — detected, but with nothing to act on |
| `tree-harness.sh` **at/after** `055eb41` | names the chunk, its `tree-sitter` status, the preserved raw output and the error text inside it, exit 1 |
| `parse-al-parallel.sh` | `Parsed OK: 280, Errors: 0, Success rate: 100.0%` — **does not detect it**, with 100 of 280 files never parsed |

## A standing finding about `parse-al-parallel.sh` — now fixed

**Historical, kept because the numbers it invalidates are still quoted in the
4.0.0 plan.** `parse-al-parallel.sh` used to compute

```sh
comm -23 "$all_files" "$errors_unsorted" > "$parsed_path"   # parsed = all − detected errors
```

so "Parsed OK" was *total minus files that produced an error line*, never a count
of files actually parsed. A file that produced no output at all — because its
chunk's process died, or because its tree was silently dropped — counted as a
success. Its own header comment already warned about this for MSYS path
failures; the fixtures showed the property was general. `Processed` was worse
than useless: `parsed + errors` where `parsed = all − errors` is algebraically
`|all|`, so it always equalled `Total files` while *looking* like a
reconciliation.

The counts now come from `tree-sitter parse --json-summary`, one record per file
actually parsed, reconciled **per chunk** against that chunk's file list. The
rows above record what each fixture produced before and after.

**What this means for older numbers.** Every `15,358/15,358, 0 errors, 100%`
recorded before that change establishes that no file *reported* an error. It does
not establish that every file was read. Re-run the corpus if you need the
stronger claim; the script now makes it.
