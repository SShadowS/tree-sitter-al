#!/usr/bin/env python3
"""tree_blob.py — split, hash and extract concatenated tree-sitter parse output.

`tree-sitter parse --paths CHUNK` emits one s-expression per input file, each
starting with `(source_file` at column 0. tree-harness.sh keeps that
concatenated output as-is (one blob per chunk) instead of exploding it into
15k individual files, and uses this helper for the things it still needs:

  index       <RAW>                    per-tree sha256 + offset + length, one per tree
  extract     <WANTED> <OUT> <IN>...   pull the listed trees out of the given blobs
  extract-tar <WANTED> <OUT> <TGZ>     the same, from a pre-format-2 snapshot archive

All three stream: memory is one read block plus one tree.

`extract` takes its inputs as file arguments rather than on stdin, and reads
.gz inputs itself, because on Windows a pipe between an MSYS producer and this
native Python runs at 40-70 MB/s: feeding the 1.3 GB corpus through one cost
19-35s, against 1.0s for the identical scan over a file it opens itself.
Several inputs are treated as one concatenated stream, exactly as `cat` would.

Tree boundaries are exactly the boundaries the previous awk-based splitter
produced — a tree runs from its `(source_file` line to the byte before the next
one (or EOF) — so these hashes are directly comparable to hashing the old
per-tree files. `index` also repairs a blob whose final byte is not a newline,
because that would weld the last tree of one chunk onto the first tree of the
next once the chunk blobs are concatenated.
"""

import gzip
import hashlib
import os
import sys
import zlib

MARKER = b"\n(source_file"
HEAD = b"(source_file"
KEEP = len(MARKER) - 1          # bytes retained so a split marker is never missed
BUFSIZE = 1 << 20


def _die(msg):
    sys.stderr.write("tree_blob: %s\n" % msg)
    raise SystemExit(1)


def _ensure_trailing_newline(path):
    """Append a newline if the blob does not end with one. True if it was repaired."""
    if os.path.getsize(path) == 0:
        return False
    with open(path, "r+b") as fh:
        fh.seek(-1, os.SEEK_END)
        if fh.read(1) == b"\n":
            return False
        fh.write(b"\n")
    return True


class ChainedBlobs:
    """Read several blobs as one stream, transparently decompressing .gz inputs."""

    def __init__(self, paths):
        self._paths = list(paths)
        self._fh = None

    def _advance(self):
        if self._fh is not None:
            self._fh.close()
            self._fh = None
        while self._paths:
            path = self._paths.pop(0)
            self._fh = gzip.open(path, "rb") if path.endswith(".gz") else open(path, "rb")
            return True
        return False

    def read(self, size):
        while True:
            if self._fh is None and not self._advance():
                return b""          # only ever empty once every input is exhausted
            data = self._fh.read(size)
            if data:
                return data
            if not self._advance():
                return b""


def iter_trees(stream, want_hash=False, wanted=frozenset()):
    """Yield (n, offset, length, sha256hex-or-None, payload-or-None) per tree.

    n counts trees from 1. A tree's bytes are only collected when n is in
    `wanted`, and only hashed when want_hash — walking a 1.3 GB corpus to pull
    out 20 trees must not pay to hash and rebuild the other 15,338. Bytes before
    the first `(source_file` line (a tree-sitter diagnostic, say) are discarded,
    matching the awk splitter this replaced.
    """
    buf = b""
    base = 0            # file offset of buf[0]
    start = None        # file offset at which the open tree begins
    n = 0
    keep = False
    pieces = None
    digest = None
    at_stream_start = True

    def begin(offset):
        nonlocal n, start, keep, pieces, digest
        n += 1
        start = offset
        keep = n in wanted
        pieces = [] if keep else None
        digest = hashlib.sha256() if want_hash else None

    def collect(src, a, b):
        # Slice only when someone will look at the bytes. Copying every tree of a
        # 1.3 GB corpus just to throw it away cost ~15s per pass.
        if keep or digest is not None:
            piece = src[a:b]
            if keep:
                pieces.append(piece)
            if digest is not None:
                digest.update(piece)

    def emit(end):
        return (n, start, end - start,
                digest.hexdigest() if digest is not None else None,
                b"".join(pieces) if keep else None)

    while True:
        block = stream.read(BUFSIZE)
        eof = not block
        if block:
            buf += block

        pos = 0
        if at_stream_start and buf:
            at_stream_start = False
            if buf.startswith(HEAD):     # first tree sits at offset 0, no leading \n
                begin(0)

        while True:
            hit = buf.find(MARKER, pos)
            if hit < 0:
                break
            boundary = base + hit + 1    # offset of the '(' that opens the next tree
            if start is not None:
                collect(buf, pos, hit + 1)
                yield emit(boundary)
            begin(boundary)
            pos = hit + 1

        # Commit everything except the tail that could still hold a split marker.
        limit = len(buf) if eof else max(pos, len(buf) - KEEP)
        if limit > pos:
            if start is not None:
                collect(buf, pos, limit)
            pos = limit
        buf = buf[pos:]
        base += pos

        if eof:
            break

    if start is not None:
        yield emit(base + len(buf))


def _read_wanted(path):
    wanted = set()
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                wanted.add(int(line, 10))
    return wanted


def cmd_index(argv):
    if len(argv) != 1:
        _die("usage: index <RAW-BLOB>")
    path = argv[0]
    _ensure_trailing_newline(path)
    write = sys.stdout.write
    with open(path, "rb") as fh:
        for _n, off, length, sha, _payload in iter_trees(fh, want_hash=True):
            write("%s\t%d\t%d\n" % (sha, off, length))
    sys.stdout.flush()
    return 0


def cmd_extract(argv):
    if len(argv) < 3:
        _die("usage: extract <WANTED-INDEX-LIST> <OUTDIR> <BLOB>...")
    wanted_path, outdir, inputs = argv[0], argv[1], argv[2:]
    for path in inputs:
        if not os.path.exists(path):
            _die("input blob '%s' does not exist" % path)
    wanted = _read_wanted(wanted_path)
    os.makedirs(outdir, exist_ok=True)

    # An empty request extracts nothing. "Nothing was asked for" must never be
    # able to turn into "everything came out" (the tar -T trap this replaced).
    if not wanted:
        sys.stderr.write("tree_blob: extract: empty index list, nothing extracted\n")
        print("0 0 0")
        return 0

    seen = written = 0
    # The whole blob is always consumed: `seen` is the caller's proof that the
    # archive holds the number of trees it claims to. A truncated or corrupt
    # archive is reported as one line, not a traceback — this output is read in
    # a terminal and pasted into reports.
    try:
        for n, _off, _length, _sha, payload in iter_trees(ChainedBlobs(inputs), wanted=wanted):
            seen = n
            if payload is not None:
                with open(os.path.join(outdir, "%06d" % n), "wb") as fh:
                    fh.write(payload)
                written += 1
    except (OSError, EOFError, zlib.error) as exc:
        _die("archive is unreadable after %d trees: %s" % (seen, exc))
    print("%d %d %d" % (seen, written, len(wanted) - written))
    return 0


def cmd_extract_tar(argv):
    """Legacy read path: snapshots taken before format 2 stored one tar member
    per tree. Streaming the archive here keeps those baselines usable, and keeps
    the two `tar` failure modes out of the picture — an empty request extracts
    nothing, and a member that is not in the archive is simply counted missing
    instead of aborting the extraction."""
    import tarfile

    if len(argv) != 3:
        _die("usage: extract-tar <WANTED-INDEX-LIST> <OUTDIR> <ARCHIVE.tar.gz>")
    wanted_path, outdir, archive = argv
    wanted = _read_wanted(wanted_path)
    os.makedirs(outdir, exist_ok=True)
    if not wanted:
        sys.stderr.write("tree_blob: extract-tar: empty index list, nothing extracted\n")
        print("0 0 0")
        return 0

    seen = written = 0
    try:
        with tarfile.open(archive, "r|gz") as tf:
            for member in tf:
                name = member.name
                if not name.startswith("trees/"):
                    continue
                tail = name[len("trees/"):]
                if not tail.isdigit():
                    continue
                seen += 1
                n = int(tail, 10)
                if n in wanted:
                    src = tf.extractfile(member)
                    if src is None:
                        continue
                    with open(os.path.join(outdir, "%06d" % n), "wb") as fh:
                        fh.write(src.read())
                    written += 1
    except (OSError, EOFError, zlib.error, tarfile.TarError) as exc:
        _die("archive is unreadable after %d members: %s" % (seen, exc))
    print("%d %d %d" % (seen, written, len(wanted) - written))
    return 0


def main():
    if len(sys.argv) < 2:
        _die("usage: tree_blob.py {index|extract|extract-tar} ...")
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "index":
        return cmd_index(rest)
    if cmd == "extract":
        return cmd_extract(rest)
    if cmd == "extract-tar":
        return cmd_extract_tar(rest)
    _die("unknown subcommand '%s'" % cmd)


if __name__ == "__main__":
    raise SystemExit(main())
