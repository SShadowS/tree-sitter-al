#!/bin/bash
#
# tree-harness.sh — parse-tree diff harness for tree-sitter-al
#
# Proves a grammar change is ZERO behavior change by re-parsing every file and
# checking the s-expression tree is byte-identical to a saved baseline. This is
# strictly stronger than "0 errors": a file can still parse without ERROR nodes
# yet produce a different tree. The harness catches that.
#
# Subcommands:
#   snapshot <ROOT> <SNAPDIR>   Parse every *.al under ROOT, store all trees in a
#                               single archive + a manifest of sha256 hashes.
#   verify   <ROOT> <SNAPDIR>   Re-parse every *.al under ROOT, compare to the
#                               snapshot. Exits non-zero and prints a tree diff
#                               for every file whose parse tree changed.
#
# Usage:
#   ./tools/tree-harness.sh snapshot ./BC.History .snapshots/bc
#   ./tools/tree-harness.sh verify   ./BC.History .snapshots/bc
#
# Notes:
#   * Run `tree-sitter generate` yourself before invoking — the harness parses
#     with whatever parser is currently built.
#   * Chunked parsing (one tree-sitter process per CHUNK_SIZE files) plus batched
#     hashing keeps both snapshot and verify to a handful of seconds for ~15k files.
#   * The file set must be stable between snapshot and verify (same ROOT). The
#     harness asserts this and aborts if the master file list drifted.

set -euo pipefail

CHUNK_SIZE="${CHUNK_SIZE:-500}"
NUM_THREADS="${NUM_THREADS:-$(nproc)}"

die() { echo "tree-harness: $*" >&2; exit 1; }

usage() {
    echo "Usage: $0 {snapshot|verify} <ROOT> <SNAPDIR>" >&2
    exit 2
}

[ $# -eq 3 ] || usage
CMD="$1"; ROOT="$2"; SNAPDIR="$3"
[ -d "$ROOT" ] || die "ROOT '$ROOT' is not a directory"

# --- shared: build the per-file tree set + manifest into $WORK -----------------
# Produces:
#   $WORK/master.txt      sorted list of *.al paths (relative to repo cwd)
#   $WORK/trees/NNNNNN     plain s-expression tree, indexed by line in master.txt
#   $WORK/manifest.tsv     "<path>\t<sha256-of-tree>" sorted by path
build_trees() {
    local WORK="$1"
    mkdir -p "$WORK/trees" "$WORK/chunks"

    find "$ROOT" -name '*.al' -type f | LC_ALL=C sort > "$WORK/master.txt"
    local count
    count=$(wc -l < "$WORK/master.txt")
    [ "$count" -gt 0 ] || die "no *.al files under '$ROOT'"
    echo "tree-harness: $count files, $NUM_THREADS threads, chunk $CHUNK_SIZE" >&2

    # Stable, zero-padded chunk names so the global file index is reconstructible.
    split -l "$CHUNK_SIZE" -d -a 4 "$WORK/master.txt" "$WORK/chunks/chunk_"

    export WORK CHUNK_SIZE
    # Parse one chunk, split the concatenated output on the '(source_file' root
    # (only ever at column 0), and write each tree to its global index.
    process_chunk() {
        local chunk="$1"
        local base idx_base
        base=$(basename "$chunk")
        idx_base=$(( 10#${base#chunk_} * CHUNK_SIZE ))   # 0-based offset into master.txt
        local out="$WORK/raw_$base"
        tree-sitter parse --paths "$chunk" > "$out" 2>&1 || true
        awk -v outdir="$WORK/trees" -v base="$idx_base" '
            /^\(source_file/ { n++; close(cur); cur = sprintf("%s/%06d", outdir, base + n) }
            { if (n > 0) print > cur }
        ' "$out"
        rm -f "$out"
    }
    export -f process_chunk

    find "$WORK/chunks" -name 'chunk_*' -type f -print0 \
        | xargs -0 -P "$NUM_THREADS" -I {} bash -c 'process_chunk "$@"' _ {}

    # Verify every file produced exactly one tree (guards against read-error desync).
    local produced
    produced=$(find "$WORK/trees" -type f | wc -l)
    [ "$produced" -eq "$count" ] \
        || die "tree count mismatch: $produced trees for $count files (read error or split desync)"

    # Build the manifest with a single batched sha256sum over all trees, then
    # join hashes (ordered by index) against the master path list.
    ( cd "$WORK/trees" && LC_ALL=C ls | LC_ALL=C sort | xargs sha256sum ) > "$WORK/hashes.txt"
    paste -d'\t' "$WORK/master.txt" <(cut -d' ' -f1 "$WORK/hashes.txt") \
        | LC_ALL=C sort > "$WORK/manifest.tsv"
}

case "$CMD" in
snapshot)
    WORK=$(mktemp -d)
    trap 'rm -rf "$WORK"' EXIT
    build_trees "$WORK"

    rm -rf "$SNAPDIR"
    mkdir -p "$SNAPDIR"
    cp "$WORK/master.txt"   "$SNAPDIR/master.txt"
    cp "$WORK/manifest.tsv" "$SNAPDIR/manifest.tsv"
    # All trees in one compressed archive (members are the 000001.. index files).
    tar -czf "$SNAPDIR/trees.tar.gz" -C "$WORK" trees
    n=$(wc -l < "$SNAPDIR/master.txt")
    echo "tree-harness: snapshot of $n trees written to $SNAPDIR"
    echo "tree-harness: manifest sha256 = $(sha256sum "$SNAPDIR/manifest.tsv" | cut -d' ' -f1)"
    ;;

verify)
    [ -f "$SNAPDIR/manifest.tsv" ] || die "no snapshot at '$SNAPDIR' (run 'snapshot' first)"
    WORK=$(mktemp -d)
    trap 'rm -rf "$WORK"' EXIT
    build_trees "$WORK"

    # The file set must not have drifted.
    if ! diff -q "$SNAPDIR/master.txt" "$WORK/master.txt" > /dev/null; then
        die "file set changed since snapshot — re-run 'snapshot'"
    fi

    if diff -q "$SNAPDIR/manifest.tsv" "$WORK/manifest.tsv" > /dev/null; then
        n=$(wc -l < "$WORK/manifest.tsv")
        echo "tree-harness: VERIFIED — all $n parse trees byte-identical to snapshot"
        exit 0
    fi

    # Report every changed file with a tree diff (old tree extracted from archive).
    #
    # Both the archive extraction and the path->index lookup happen ONCE, before
    # the loop. Doing either per changed file made reporting O(n^2): each
    # iteration re-inflated the whole trees.tar.gz to fetch a single member and
    # re-scanned all of master.txt, which put a ~2s floor under every changed
    # file on a 15k-file snapshot and made large deltas unusable.
    echo "tree-harness: MISMATCH — parse trees changed:" >&2
    changed=0

    # join old+new manifests on path; emit path when hashes differ
    LC_ALL=C join -t$'\t' "$SNAPDIR/manifest.tsv" "$WORK/manifest.tsv" \
        | awk -F'\t' '$2 != $3 { print $1 }' > "$WORK/changed.txt"

    # Resolve every changed path to its 1-based line number in master.txt in a
    # single pass, emitting "<path>\t<zero-padded index>".
    awk 'NR==FNR { idx[$0] = FNR; next } { printf "%s\t%06d\n", $0, idx[$0] }' \
        "$SNAPDIR/master.txt" "$WORK/changed.txt" > "$WORK/changed_idx.tsv"

    # One pass over the archive pulls out exactly the members we need; snapshot
    # trees land in $WORK/old/trees/NNNNNN, mirroring $WORK/trees/NNNNNN.
    cut -f2 "$WORK/changed_idx.tsv" | sed 's|^|trees/|' > "$WORK/old_members.txt"
    mkdir -p "$WORK/old"
    tar -xzf "$SNAPDIR/trees.tar.gz" -C "$WORK/old" -T "$WORK/old_members.txt"

    while IFS=$'\t' read -r path idxp; do
        changed=$((changed + 1))
        echo "" >&2
        echo "=== CHANGED: $path" >&2
        diff "$WORK/old/trees/$idxp" "$WORK/trees/$idxp" >&2 || true
    done < "$WORK/changed_idx.tsv"
    echo "" >&2
    echo "tree-harness: $changed file(s) changed" >&2
    exit 1
    ;;

*)
    usage
    ;;
esac
