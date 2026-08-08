# Release tree-sitter-al

Execute the full release process for tree-sitter-al. This publishes to GitHub Releases, npm, PyPI, and crates.io.

All three registries authenticate with OIDC trusted publishing. There are no publish tokens stored in the repository.

## Pre-flight Checks

Before starting, verify:
1. All tests pass: `tree-sitter test`
2. Production validation: `./parse-al-parallel.sh ./BC.History/ .` (0 errors)
3. No ERROR/MISSING nodes in any test: `grep -rn "(ERROR\b\|MISSING\b" test/corpus/ --include="*.txt" | grep -v "ERROR("`
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
tree-sitter build --wasm
```

WASM size is proportional to parser.c size. Commit: `chore: rebuild tree-sitter-al.wasm for vX.Y.Z`

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

Attaches to release `vX.Y.Z`:
- tree-sitter-al.wasm (copied from repo)
- tree-sitter-al.so (Linux, built in CI)
- tree-sitter-al.dll (Windows, built in CI)
- tree-sitter-al.dylib (macOS, built in CI)

## Step 6: Verify All Channels

```bash
gh release view vX.Y.Z
npm view @sshadows/tree-sitter-al versions --json
pip index versions tree-sitter-al 2>/dev/null || echo "Check https://pypi.org/project/tree-sitter-al/"
cargo search tree-sitter-al
```

PyPI and npm are behind a CDN and can take a few minutes to show the new version. Do not conclude a publish failed from a stale read.

## Quick Reference

| Step | Command | Where | Depends On |
|------|---------|-------|------------|
| Version bump | Edit 3 files + 2 lockfiles | Local | - |
| WASM rebuild | `tree-sitter build --wasm` | Local | Version bump |
| Push | `git push` | Local | WASM |
| All 3 registries | `git push origin vX.Y.Z` | CI | Push |
| GitHub Release | `gh workflow run "Build and release artifacts"` | CI | Push |

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
