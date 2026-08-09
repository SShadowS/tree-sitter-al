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
#   * The file set must be stable between snapshot and verify (same ROOT). The
#     harness asserts this and aborts if the master file list drifted.
#
# A CLEAN RESULT MUST MEAN SOMETHING. This harness is the only thing standing
# between a silent parse-tree change and a release, so every path that could
# report "0 files changed" without having compared 15k real trees is asserted
# shut: each chunk must yield exactly as many trees as it had files, the
# manifest must have exactly one row per file, and a manifest difference that
# resolves to zero changed paths is treated as corruption, not as success.
#
# Performance, BC.History (15,358 files) at NUM_THREADS=16, measured:
#
#                          before    after
#   snapshot                44.1s    16.1s
#   verify, no change       24.6s    11.2s
#   verify, 20 changed      30.9s    15.3s
#   verify, 757 changed   2m56.1s    22.3s
#
#   * The trees are never exploded into one file each. `tree-sitter parse`
#     already concatenates a chunk's trees, so that blob is kept as-is and
#     tools/tree_blob.py splits/hashes it in-process — no 15k file creations,
#     no second hashing pass, no 15k-member tar. Parsing itself is ~8s of the
#     total and is the floor.
#   * The mismatch report runs ONE `diff -r` over the changed trees rather than
#     one `diff` per changed file. Process creation on Windows costs ~33ms, and
#     the old per-file loop spent ~230ms on each changed file, which is where a
#     757-file delta lost 2.5 of its 3 minutes.

set -euo pipefail

CHUNK_SIZE="${CHUNK_SIZE:-500}"
NUM_THREADS="${NUM_THREADS:-$(nproc)}"
GZIP_LEVEL="${GZIP_LEVEL:-1}"   # -1 costs ~40% archive size and saves ~17s per snapshot

# Stamped into SNAPDIR/FORMAT. `verify` reads the archive layout from what is
# actually on disk, so snapshots taken before this existed still work.
SNAP_FORMAT=2

die() { echo "tree-harness: $*" >&2; exit 1; }

usage() {
    echo "Usage: $0 {snapshot|verify} <ROOT> <SNAPDIR>" >&2
    exit 2
}

[ $# -eq 3 ] || usage
CMD="$1"; ROOT="$2"; SNAPDIR="$3"
[ -d "$ROOT" ] || die "ROOT '$ROOT' is not a directory"

TOOLDIR=$(cd "$(dirname "$0")" && pwd)
TREE_BLOB="$TOOLDIR/tree_blob.py"
[ -f "$TREE_BLOB" ] || die "missing helper '$TREE_BLOB'"

if [ -z "${PYTHON:-}" ]; then
    for cand in python3 python py; do
        if command -v "$cand" >/dev/null 2>&1 \
           && "$cand" -c 'import sys' >/dev/null 2>&1 </dev/null; then
            PYTHON="$cand"; break
        fi
    done
fi
[ -n "${PYTHON:-}" ] || die "no working python interpreter found (set PYTHON=...)"

# --- shared: build the per-file tree set + manifest into $WORK -----------------
# Produces:
#   $WORK/master.txt      sorted list of *.al paths (relative to repo cwd)
#   $WORK/raw/chunk_NNNN  concatenated trees for that chunk, exactly as parsed
#   $WORK/idx/chunk_NNNN  "<sha256>\t<offset>\t<length>" per tree in that blob
#   $WORK/manifest.tsv    "<path>\t<sha256-of-tree>" sorted by path
build_trees() {
    local WORK="$1"
    mkdir -p "$WORK/chunks" "$WORK/raw" "$WORK/idx" "$WORK/rc"

    find "$ROOT" -name '*.al' -type f | LC_ALL=C sort > "$WORK/master.txt"
    local count
    count=$(wc -l < "$WORK/master.txt")
    [ "$count" -gt 0 ] || die "no *.al files under '$ROOT'"
    echo "tree-harness: $count files, $NUM_THREADS threads, chunk $CHUNK_SIZE" >&2

    # Build the parser once, serially, before fanning out. tree-sitter locks its
    # build directory so a cold cache is not known to corrupt a parallel run, but
    # a single warm parse removes the window entirely and costs nothing when the
    # shared library is already current.
    head -n 1 "$WORK/master.txt" > "$WORK/warmup.txt"
    tree-sitter parse -q --paths "$WORK/warmup.txt" >/dev/null 2>&1 || true

    # Stable, zero-padded chunk names so the global file index is reconstructible.
    split -l "$CHUNK_SIZE" -d -a 4 "$WORK/master.txt" "$WORK/chunks/chunk_"

    export WORK PYTHON TREE_BLOB
    # Parse one chunk and index the resulting blob in place. A non-zero exit from
    # tree-sitter is NORMAL here (it reports failure when any file has an ERROR
    # node), so the status is recorded for diagnostics rather than acted on; the
    # per-chunk tree count below is what actually decides whether a chunk is good.
    process_chunk() {
        local chunk="$1"
        local base rc=0
        base=${chunk##*/}
        tree-sitter parse --paths "$chunk" > "$WORK/raw/$base" 2>&1 || rc=$?
        if ! "$PYTHON" "$TREE_BLOB" index "$WORK/raw/$base" > "$WORK/idx/$base"; then
            echo "index-failed(parse rc=$rc)" > "$WORK/rc/$base"
        else
            echo "$rc" > "$WORK/rc/$base"
        fi
    }
    export -f process_chunk

    find "$WORK/chunks" -name 'chunk_*' -type f -print0 \
        | xargs -0 -P "$NUM_THREADS" -I {} bash -c 'process_chunk "$@"' _ {}

    # Every chunk must yield exactly one tree per file it listed. A global total
    # is not enough: two chunks losing and gaining the same number of trees would
    # cancel out and silently mis-pair every path after the gap with the wrong hash.
    # `split -l` fixes the expected size of every chunk but the last, so the
    # counts come from ONE `wc` over the index files rather than a per-chunk
    # command: on Windows a process spawn costs ~33ms and `mapfile` on a 500-line
    # file costs ~38ms, so a 31-chunk loop either way threw away several seconds.
    local nchunks last_expected base expected got idx seen=0
    nchunks=$(( (count + CHUNK_SIZE - 1) / CHUNK_SIZE ))
    last_expected=$(( count - (nchunks - 1) * CHUNK_SIZE ))
    while read -r got base; do
        [ "$base" = "total" ] && continue
        base=${base##*/}
        idx=$(( 10#${base#chunk_} ))
        expected=$CHUNK_SIZE
        [ "$idx" -eq $(( nchunks - 1 )) ] && expected=$last_expected
        seen=$(( seen + 1 ))
        if [ "$got" -ne "$expected" ]; then
            local keep
            keep=$(mktemp -d "${TMPDIR:-/tmp}/tree-harness-fail-XXXXXX")
            cp "$WORK/chunks/$base" "$keep/" || true
            cp "$WORK/raw/$base" "$keep/" || true
            {
                echo "tree-harness: chunk $base produced $got trees for $expected files"
                echo "tree-harness:   tree-sitter status: $(cat "$WORK/rc/$base" || echo '<none recorded>')"
                echo "tree-harness:   file list and raw output preserved in $keep"
                echo "tree-harness:   first lines of raw output:"
                head -n 5 "$WORK/raw/$base" 2>&1 | sed 's/^/tree-harness:     /' || true
            } >&2
            die "chunk $base desynced — refusing to report on an incomplete tree set"
        fi
    done < <(wc -l "$WORK"/idx/chunk_*)
    [ "$seen" -eq "$nchunks" ] \
        || die "only $seen of $nchunks chunks were indexed — a parse worker never ran"

    # Concatenate the per-chunk indexes in chunk order, which is master.txt order
    # (the zero-padded names sort identically in every locale).
    cat "$WORK"/idx/chunk_* > "$WORK/index.tsv"
    local produced
    produced=$(wc -l < "$WORK/index.tsv")
    [ "$produced" -eq "$count" ] \
        || die "tree count mismatch: $produced trees for $count files"

    paste -d'\t' "$WORK/master.txt" <(cut -f1 "$WORK/index.tsv") \
        | LC_ALL=C sort > "$WORK/manifest.tsv"
    local rows
    rows=$(wc -l < "$WORK/manifest.tsv")
    [ "$rows" -eq "$count" ] || die "manifest has $rows rows for $count files"
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
    # One compressed blob holding every tree back to back, in master.txt order.
    cat "$WORK"/raw/chunk_* | gzip "-$GZIP_LEVEL" -c > "$SNAPDIR/trees.gz"
    n=$(wc -l < "$SNAPDIR/master.txt")
    printf 'format=%s\ntrees=%s\n' "$SNAP_FORMAT" "$n" > "$SNAPDIR/FORMAT"
    echo "tree-harness: snapshot of $n trees written to $SNAPDIR"
    echo "tree-harness: manifest sha256 = $(sha256sum "$SNAPDIR/manifest.tsv" | cut -d' ' -f1)"
    ;;

verify)
    [ -f "$SNAPDIR/manifest.tsv" ] || die "no snapshot at '$SNAPDIR' (run 'snapshot' first)"
    # manifest.tsv has never changed shape, so a pre-format-2 snapshot still
    # verifies; only the archive layout differs, and the mismatch report reads
    # the old one through a legacy path rather than stranding stored baselines.
    if [ -f "$SNAPDIR/trees.gz" ]; then
        SNAP_ARCHIVE="$SNAPDIR/trees.gz"; SNAP_READER=extract
    elif [ -f "$SNAPDIR/trees.tar.gz" ]; then
        SNAP_ARCHIVE="$SNAPDIR/trees.tar.gz"; SNAP_READER=extract-tar
    else
        die "snapshot '$SNAPDIR' has no tree archive — re-run 'snapshot'"
    fi
    WORK=$(mktemp -d)
    trap 'rm -rf "$WORK"' EXIT
    build_trees "$WORK"

    # The file set must not have drifted.
    if ! cmp -s "$SNAPDIR/master.txt" "$WORK/master.txt"; then
        die "file set changed since snapshot — re-run 'snapshot'"
    fi

    # The snapshot itself must describe every file, or a comparison against it
    # proves nothing.
    n=$(wc -l < "$WORK/master.txt")
    snap_rows=$(wc -l < "$SNAPDIR/manifest.tsv")
    [ "$n" -gt 0 ] || die "empty file list — nothing was compared"
    [ "$snap_rows" -eq "$n" ] \
        || die "snapshot manifest has $snap_rows rows for $n files — snapshot is damaged"

    if cmp -s "$SNAPDIR/manifest.tsv" "$WORK/manifest.tsv"; then
        echo "tree-harness: VERIFIED — all $n parse trees byte-identical to snapshot"
        exit 0
    fi

    echo "tree-harness: MISMATCH — parse trees changed:" >&2

    # join old+new manifests on path; emit path when hashes differ
    LC_ALL=C join -t$'\t' "$SNAPDIR/manifest.tsv" "$WORK/manifest.tsv" \
        | awk -F'\t' '$2 != $3 { print $1 }' > "$WORK/changed.txt"
    [ -s "$WORK/changed.txt" ] \
        || die "manifests differ but no path disagrees on its hash — snapshot manifest is malformed"

    # Resolve every changed path to its 1-based line number in master.txt in a
    # single pass, emitting "<path>\t<zero-padded index>".
    awk '
        NR==FNR { idx[$0] = FNR; next }
        { if (!($0 in idx)) { print "tree-harness: changed path absent from master.txt: " $0 > "/dev/stderr"; exit 3 }
          printf "%s\t%06d\n", $0, idx[$0] }
    ' "$SNAPDIR/master.txt" "$WORK/changed.txt" > "$WORK/changed_idx.tsv" \
        || die "a changed path is not in the snapshot's master list — snapshot is inconsistent"
    changed=$(wc -l < "$WORK/changed_idx.tsv")
    [ "$changed" -gt 0 ] || die "changed-file index came out empty — refusing to report a clean run"

    # Pull only the changed trees out of both sides. Each side is one streaming
    # pass over blobs the helper opens itself (piping 1.3 GB into native Python
    # from MSYS costs 20-35s; letting it read the files costs ~1s). A member
    # missing from the archive degrades to a note for that one file instead of
    # aborting the whole report, and an empty request extracts nothing at all
    # (the `tar -T` trap this replaced extracted everything).
    cut -f2 "$WORK/changed_idx.tsv" > "$WORK/wanted.txt"
    mkdir -p "$WORK/cmp/old" "$WORK/cmp/new"
    old_stats=$("$PYTHON" "$TREE_BLOB" "$SNAP_READER" "$WORK/wanted.txt" "$WORK/cmp/old" \
        "$SNAP_ARCHIVE") \
        || die "could not read snapshot archive '$SNAP_ARCHIVE'"
    new_stats=$("$PYTHON" "$TREE_BLOB" extract "$WORK/wanted.txt" "$WORK/cmp/new" \
        "$WORK"/raw/chunk_*) \
        || die "could not re-read the freshly parsed trees"
    [ -n "$old_stats" ] && [ -n "$new_stats" ] \
        || die "tree extraction reported nothing — refusing to report on an unread archive"
    read -r old_seen old_written old_missing <<< "$old_stats"
    read -r new_seen new_written new_missing <<< "$new_stats"

    [ "$new_missing" -eq 0 ] && [ "$new_seen" -eq "$n" ] \
        || die "freshly parsed tree set is incomplete ($new_seen trees, $new_missing unresolved)"
    if [ "$old_seen" -ne "$n" ]; then
        echo "tree-harness: WARNING — archive holds $old_seen trees, expected $n" >&2
    fi
    [ "$old_written" -gt 0 ] \
        || die "no snapshot tree could be read for any of the $changed changed files"

    # ONE diff process for the whole delta — the old per-file loop spent ~230ms
    # on every changed file, which is where a 757-file delta lost 2.5 of its 3
    # minutes. Run from $WORK/cmp so the headers `diff -r` emits are the
    # fixed strings rewritten below, and pass -s so a pair that turns out
    # identical still gets a `=== CHANGED:` header instead of vanishing from the
    # report. Both directories are name-sorted and names are the zero-padded
    # master.txt line numbers, so the report order matches changed_idx.tsv.
    ( cd "$WORK/cmp" && diff -r -s old new || true ) \
        | awk -F'\t' '
            FNR==NR { path[$2] = $1; next }
            /^diff -r -s old\/[0-9][0-9][0-9][0-9][0-9][0-9] new\/[0-9][0-9][0-9][0-9][0-9][0-9]$/ {
                split($0, a, " "); idx = substr(a[4], 5)
                printf "\n=== CHANGED: %s\n", path[idx]; next
            }
            /^Files old\/[0-9][0-9][0-9][0-9][0-9][0-9] and new\/[0-9][0-9][0-9][0-9][0-9][0-9] are identical$/ {
                split($0, a, " "); idx = substr(a[2], 5)
                printf "\n=== CHANGED: %s\n", path[idx]; identical++; next
            }
            /^Only in new: [0-9][0-9][0-9][0-9][0-9][0-9]$/ {
                idx = substr($0, 14)
                printf "\n=== CHANGED: %s\n", path[idx]
                print "tree-harness: snapshot tree for this file is missing from the archive — cannot diff"
                next
            }
            { print }
            END {
                if (identical > 0)
                    printf "\ntree-harness: %d changed file(s) parsed to a tree identical to the snapshot — the snapshot manifest disagrees with the snapshot archive\n", identical
            }
        ' "$WORK/changed_idx.tsv" - >&2

    echo "" >&2
    echo "tree-harness: $changed file(s) changed" >&2
    exit 1
    ;;

*)
    usage
    ;;
esac
