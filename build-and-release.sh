#!/bin/bash
# Build WASM locally and trigger GitHub Actions to build shared libraries + create release
# Usage: ./build-and-release.sh [--skip-wasm] [--dry-run]
#
# Creates two releases:
#   - Versioned release (v0.1.0) from package.json version — permanent, with changelog
#   - 'latest' release — always points to newest build
set -euo pipefail

SKIP_WASM=false
DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --skip-wasm) SKIP_WASM=true ;;
        --dry-run) DRY_RUN=true ;;
        *) echo "Unknown arg: $arg"; exit 1 ;;
    esac
done

echo "=== Pre-flight checks ==="

# 1. Check we're on main
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "ERROR: Must be on main branch (currently on '$BRANCH')"
    exit 1
fi

# 2. Check no uncommitted changes to tracked files
if ! git diff --quiet HEAD; then
    echo "ERROR: Uncommitted changes to tracked files. Commit or stash first."
    git diff --stat HEAD
    exit 1
fi

# 3. Check versions match between package.json and Cargo.toml
PKG_VERSION=$(grep '"version"' package.json | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/')
CARGO_VERSION=$(grep '^version' Cargo.toml | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/')
VERSION_TAG="v${PKG_VERSION}"

echo "  package.json version: $PKG_VERSION"
echo "  Cargo.toml version:   $CARGO_VERSION"
echo "  Release tag:          $VERSION_TAG"

if [ "$PKG_VERSION" != "$CARGO_VERSION" ]; then
    echo "ERROR: Version mismatch between package.json ($PKG_VERSION) and Cargo.toml ($CARGO_VERSION)"
    exit 1
fi

# 4. Check if versioned release already exists
if gh release view "$VERSION_TAG" >/dev/null 2>&1; then
    echo ""
    echo "WARNING: Release $VERSION_TAG already exists!"
    echo "  The workflow will skip creating a new versioned release."
    echo "  To create a new versioned release, bump the version in package.json and Cargo.toml first."
    echo ""
    read -p "  Continue anyway (updates 'latest' only)? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 5. Verify grammar generates and tests pass
echo ""
echo "=== Validating grammar ==="
tree-sitter generate
echo "  Parser generated OK"

TEST_OUTPUT=$(tree-sitter test 2>&1 | grep "Total parses:")
if echo "$TEST_OUTPUT" | grep -q "failed parses: 0"; then
    echo "  Tests: $TEST_OUTPUT"
else
    echo "ERROR: Tests failing!"
    echo "  $TEST_OUTPUT"
    exit 1
fi

# 6. Build WASM
if [ "$SKIP_WASM" = false ]; then
    echo ""
    echo "=== Building WASM ==="
    echo "  This requires ~90GB virtual memory and takes ~12 minutes..."
    tree-sitter build --wasm -0 .
    WASM_SIZE=$(ls -lh tree-sitter-al.wasm | awk '{print $5}')
    echo "  Built: tree-sitter-al.wasm ($WASM_SIZE)"

    # Verify it's valid
    if file tree-sitter-al.wasm | grep -q "WebAssembly"; then
        echo "  Valid WebAssembly binary"
    else
        echo "ERROR: WASM file is not valid"
        exit 1
    fi
else
    echo ""
    echo "=== Skipping WASM build (--skip-wasm) ==="
    if [ ! -f tree-sitter-al.wasm ]; then
        echo "ERROR: tree-sitter-al.wasm not found. Build it first or remove --skip-wasm."
        exit 1
    fi
    echo "  Using existing: tree-sitter-al.wasm ($(ls -lh tree-sitter-al.wasm | awk '{print $5}'))"
fi

# 7. Commit WASM if changed
if ! git diff --quiet tree-sitter-al.wasm 2>/dev/null || ! git ls-files --error-unmatch tree-sitter-al.wasm >/dev/null 2>&1; then
    echo ""
    echo "=== Committing updated WASM ==="
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY RUN] Would commit tree-sitter-al.wasm"
    else
        git add tree-sitter-al.wasm
        git commit -m "build: update prebuilt WASM

[BC.History: $(cat ./BC.History/errors.txt 2>/dev/null | wc -l | tr -d ' ') errors]"
        echo "  Committed"
    fi
else
    echo ""
    echo "  WASM unchanged, no commit needed"
fi

# 8. Push and trigger workflow
echo ""
echo "=== Pushing and triggering release ==="
if [ "$DRY_RUN" = true ]; then
    echo "  [DRY RUN] Would push to origin/main"
    echo "  [DRY RUN] Would trigger build-wasm.yml workflow"
    echo "  [DRY RUN] Workflow would create: $VERSION_TAG + latest"
else
    git push origin main
    echo "  Pushed to main"

    gh workflow run build-wasm.yml
    echo "  Triggered release workflow"

    sleep 3
    RUN_ID=$(gh run list --workflow=build-wasm.yml --limit 1 --json databaseId --jq '.[0].databaseId')
    echo "  Run ID: $RUN_ID"
    echo "  Watch: gh run watch $RUN_ID"
    echo "  View:  gh run view $RUN_ID"
fi

echo ""
echo "=== Done ==="
echo "Workflow will create:"
echo "  - $VERSION_TAG release (permanent, versioned)"
echo "  - 'latest' release (rolling, always newest)"
