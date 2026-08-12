# Release tree-sitter-al

Execute the full release process for tree-sitter-al. This publishes to GitHub Releases, npm, PyPI, and crates.io.

All three registries authenticate with OIDC trusted publishing. There are no publish tokens stored in the repository.

## Pre-flight Checks

Before starting, verify:
1. All tests pass: `tree-sitter test`
2. Production validation: `./parse-al-parallel.sh ./BC.History/ .` (0 errors)
3. No **unexpected** ERROR/MISSING nodes in any test — this must print nothing:

   ```bash
   grep -rn "(ERROR\b\|(MISSING\b" test/corpus/ --include="*.txt" \
     | grep -v "ERROR(" \
     | grep -vE "(^|/)(option_members_tabledata_keyword_test|pragma_whitespace_tolerance_test|preproc_if_elif_whitespace_tolerance_test|preproc_region_whitespace_audit_test|scanner_var_attribute_token_span_test|directive_word_boundary_test|scanner_unicode_identifier_negative_test|range_not_an_expression_negative_test|preproc_split_operator_negative_test|interface_access_negative_test|missing_separator_negative_test)\.txt:"
   ```

   The `(^|/)…\.txt:` anchoring is load-bearing. `grep -rn` emits
   `path:lineno:content`, so an unanchored name matches anywhere in the line
   — including the matched source text — and would silently exempt any future
   fixture whose content happens to mention one of these names. Anchored, the
   name must be the file's own basename, which is exactly the comparison
   `validate-grammar.sh` makes.

   **Both alternatives need the opening paren.** This search previously read
   `MISSING\b` without it, while `ERROR` required `(ERROR\b`. Expected trees
   write these as `(MISSING xyz)` and `(ERROR)`, so the bare form matched the
   word anywhere on a line — a fixture *title* or a prose comment containing
   "MISSING" failed the release. `validate-grammar.sh` Step 3 anchors its
   equivalent search to line starts and was never affected, so the two gates
   disagreed on what counts as a hit. Found by writing a fixture titled with
   the bare word.

   Those ten files are deliberate negatives — their ERROR nodes *are* the
   assertion. Any hit OUTSIDE them is a real problem. Each is named below rather
   than counted by ordinal: the prose count has drifted from the list twice
   (once at six-vs-seven, once at seven-vs-eight), because an ordinal has to be
   re-derived every time somebody appends an entry, and a name does not.

   - `option_members_tabledata_keyword_test` — a misplaced `TableData X = R`
     fragment under OptionMembers surfaces rather than being silently absorbed.
   - `pragma_whitespace_tolerance_test`, `preproc_if_elif_whitespace_tolerance_test`,
     `preproc_region_whitespace_audit_test` — `#` + newline + `pragma`/`if`/`elif`/
     `region` does not lex as a directive; tolerance after `#` is horizontal-only.
     Also that `# ifx` is not `#if`.
   - `scanner_var_attribute_token_span_test` — a stray identifier before a var
     attribute gets its own node instead of being absorbed into the `[` token.
   - `directive_word_boundary_test` — a directive keyword with no word boundary
     (`#regionX`, `#pragmaX`) is not a directive at all.
   - `scanner_unicode_identifier_negative_test` — a codepoint the grammar's
     `[\p{L}\p{N}_]` excludes is not an identifier character.
   - `range_not_an_expression_negative_test` — `..` is not an expression
     operator, so `1 + (1 .. 4)` has no reading in AL.
   - `interface_access_negative_test` — the interface `Access = X` HEADER form
     is not AL (alc AL0104, both bare and after `extends`). Removed from the
     grammar in 4.0.0; the accepted form is a body property.
   - `missing_separator_negative_test` — a comma-separated list with the comma
     omitted (`where(A = const(1) B = const(2))`, two `tabledata` entries,
     `case i of 1 2:`). alc rejects all three with AL0104; the grammar used to
     absorb the second item silently as an extra element.

   `scanner_unicode_identifier_negative_test` is carried AHEAD of its fixture:
   the file lands with the identifier-classification branch, and an allow-list
   entry for an absent file is inert. Adding it early is what stops the two gates
   disagreeing at the moment that branch merges, since neither branch can edit
   the other's copy.

   Unscoped, this check had 8 hits across the original 4 files and so had never
   passed at any release, v3.3.0 included. The same exemption list lives in
   `validate-grammar.sh` Step 3 (`DELIBERATE_ERROR_FIXTURES`), which matches on
   exact basename. **The two gates must exempt exactly the same set** — change
   both or neither, and keep the matching anchored so they cannot drift.
4. Working directory is clean (no uncommitted grammar/scanner changes)
5. `src/parser.c` is current: run `tree-sitter generate` and confirm no diff. CI fails otherwise, because `parser-test-action` regenerates and runs `git diff --exit-code`.

## Step 1: Version Bump

Update version in ALL THREE files (they must match):
- `package.json` → `"version": "X.Y.Z"`
- `Cargo.toml` → `version = "X.Y.Z"`
- `tree-sitter.json` → `"version": "X.Y.Z"`

**CRITICAL: Also update lockfiles after version bump:**
```bash
npm install --package-lock-only  # Regenerates package-lock.json
cargo check                       # Updates Cargo.lock
```

Commit all 5 files together: `chore: bump version to X.Y.Z`

## Step 2: Rebuild WASM

```bash
tree-sitter build --wasm -o tree-sitter-al.wasm
tools/check-wasm-fresh.sh --update
```

Commit both files: `chore: rebuild tree-sitter-al.wasm for vX.Y.Z`. WASM size is
proportional to parser.c size.

**This is not a formality, and it is not only a release step.** The release
workflow `cp`s the committed wasm — it never builds it — so the file in git *is*
the artifact every web-tree-sitter consumer loads. Between v4.0.0 and the next
grammar fix it went stale, and the shipped wasm parsed
`codeunit 80228 "T" { var Filter: Codeunit "Some Thing"; }` with an ERROR that the
repository's own parser did not have. Nothing in the test suite loads the wasm, so
every gate stayed green.

`tools/check-wasm-fresh.sh` now runs in CI (`wasm-freshness`) and as Step 9 of
`validate-grammar.sh`, comparing a stamp of `src/parser.c` + `src/scanner.c`
against the recorded one. **Never run `--update` to clear a red gate** — it records
"the current wasm was built from the current sources", so updating without
rebuilding turns the check into a rubber stamp.

## Step 3: Push

```bash
git push
```

CI (`ci.yml`) runs parser tests on Linux, macOS and Windows, fuzzes the scanner when `src/scanner.c` changed, and validates `queries/` with `ts_query_ls`. Let it go green before releasing.

## Step 4: Publish all three registries

Push the tag from your machine. Each publish workflow triggers on `v*` tags independently, verifies the tag against `package.json`, and publishes.

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

**The tag must be pushed from your machine, not created by CI.** Step 5's workflow tags with the default `GITHUB_TOKEN`, and GitHub suppresses workflow triggers for events created by that token, so a CI-created tag starts nothing.

To publish without a tag, dispatch the workflows directly; the tag check skips itself on manual dispatch:

```bash
gh workflow run "Publish npm Package" --ref main
gh workflow run "Publish Python Package" --ref main
gh workflow run "Publish Rust Crate" --ref main
```

The three are independent, so one registry failing does not block the others.

## Step 5: GitHub Release (binaries)

```bash
gh workflow run "Build and release artifacts" --ref main
gh run watch <RUN_ID> --exit-status
```

**This workflow is `workflow_dispatch` only.** Pushing the tag in Step 4 does NOT
trigger it — the three registry publishes fire on `v*`, this one does not. Skip
Step 5 and the GitHub release for `vX.Y.Z` has no assets at all, while npm still
gets a wasm (its `files` list includes `*.wasm`).

Attaches to release `vX.Y.Z`:
- tree-sitter-al.wasm — **copied from the repo, never built here** (`cp tree-sitter-al.wasm artifacts/`). Whatever is committed is what ships; see Step 2.
- tree-sitter-al.so (Linux, built in CI)
- tree-sitter-al.dll (Windows, built in CI)
- tree-sitter-al.dylib (macOS, built in CI)

PyPI and crates.io carry no wasm at all — both build natively — so the wasm
reaches consumers through exactly two channels: this release and npm.

## Step 6: Verify All Channels

```bash
gh release view vX.Y.Z
npm view @sshadows/tree-sitter-al versions --json
pip index versions tree-sitter-al 2>/dev/null || echo "Check https://pypi.org/project/tree-sitter-al/"
cargo search tree-sitter-al
```

PyPI and npm are behind a CDN and can take a few minutes to show the new version. Do not conclude a publish failed from a stale read.

**Verify the published wasm is the one you built** — a version number matching
proves nothing about the binary, and this is the artifact that shipped stale
once:

```bash
gh release download vX.Y.Z -p tree-sitter-al.wasm -D /tmp/relcheck
sha256sum /tmp/relcheck/tree-sitter-al.wasm tree-sitter-al.wasm   # must match
```

For a functional check — the one that actually caught the stale wasm — load it in
web-tree-sitter and parse a construct the release fixed. `errors=0` on the new
wasm and `errors=1` on the previous one is the discriminating pair; a check that
passes on both versions is not testing the fix.

## Quick Reference

| Step | Command | Where | Depends On |
|------|---------|-------|------------|
| Version bump | Edit 3 files + 2 lockfiles | Local | - |
| WASM rebuild | `tree-sitter build --wasm -o tree-sitter-al.wasm` then `tools/check-wasm-fresh.sh --update` | Local | any `src/parser.c` or `src/scanner.c` change |
| Push | `git push` | Local | WASM |
| All 3 registries | `git push origin vX.Y.Z` | CI | Push |
| GitHub Release | `gh workflow run "Build and release artifacts"` | CI | Push — **not triggered by the tag** |

The WASM row does **not** depend on the version bump: no version string lives in
`src/parser.c`, `src/grammar.json` or `src/node-types.json` (only `package.json`
and `Cargo.toml` carry one), so a bump alone leaves the stamp valid. It depends
on the generated sources changing — which is what `check-wasm-fresh` measures,
and why the trigger is that rather than "every release".

## Trusted publishing setup

Each publish workflow must run as a **top-level** workflow. npm and PyPI validate trusted publishing against the *calling* workflow, so wrapping these in a reusable-workflow caller breaks both. An earlier `release.yml` orchestrator did exactly that and PyPI rejected the upload with:

```
release.yml@refs/tags/v3.2.1 does not match expected
Trusted Publisher (publish-pypi.yml @ SShadowS/tree-sitter-al)
```

Registry-side configuration, all matched on exact strings:

| Registry | Configured against |
|----------|-------------------|
| npm | org `SShadowS`, repo `tree-sitter-al`, workflow `publish-npm.yml`, environment `npm` |
| PyPI | workflow `publish-pypi.yml` |
| crates.io | repo `SShadowS/tree-sitter-al`, workflow `publish-crates.yml` |

## Gotchas

- **Lockfiles**: `package-lock.json` and `Cargo.lock` must be regenerated after a version bump or `npm ci` fails in CI
- **npm needs npm >= 11.5.1** for trusted publishing. Node 24 ships npm 11.x, and the workflow additionally installs `npm@latest`. With an older npm the CLI silently falls back to token auth
- **npm placeholder token**: `actions/setup-node` with `registry-url` exports `NODE_AUTH_TOKEN` as the literal string `XXXXX-XXXXX-XXXXX-XXXXX`. The workflow blanks it, otherwise a failed OIDC exchange falls back to that bogus token and reports a misleading 404
- **Debugging a failed npm publish**: add `--loglevel silly`. The real reason appears as `npm verbose oidc Failed token exchange request with body message: ...`. Without it, npm reports only E404 or ENEEDAUTH. A "package not found" body means the trusted publisher fields on npmjs do not match exactly; they are case sensitive and the web form silently accepts a leading `@` on the organization
- **npm scope**: the package is `@sshadows/tree-sitter-al`. The unscoped name cannot be claimed; npm rejects it as too similar to `tree-sitter-cli`
- **`files` glob in package.json** is `queries/*.scm`. npm packs the working directory rather than the git index, so a broader glob ships untracked scratch files. 3.2.0 shipped `queries/bad_delete.scm.v1` that way
- **WASM is tracked in git**: `.gitignore` has `!tree-sitter-al.wasm` exception
- **Stale local `al.dll` / `al.so`**: `ts_query_ls` loads the prebuilt library from the repo root. If it reports invalid node types that clearly exist in `src/node-types.json`, run `tree-sitter build` and retry
- **CI-created tags do not trigger workflows**: see Step 4
