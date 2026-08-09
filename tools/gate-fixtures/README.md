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

## A standing finding about `parse-al-parallel.sh`

Both rows above are worth reading twice. `parse-al-parallel.sh` computes

```sh
comm -23 "$all_files" "$errors_unsorted" > "$parsed_path"   # parsed = all − detected errors
```

so "Parsed OK" is *total minus files that produced an error line*, never a count
of files actually parsed. A file that produces no output at all — because its
chunk's process died, or because its tree was silently dropped — is counted as a
success. Its own header comment already warns about this for MSYS path failures;
the fixtures show the property is general.

Consequence: **a green `parse-al-parallel.sh` run does not corroborate that every
file was examined.** It corroborates that an independent `find` enumerated the
same file set and that no file produced an ERROR/MISSING node or a read error.
Do not cite it as an independent count of work done.
