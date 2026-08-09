#!/usr/bin/env python3
"""Drop or duplicate trees in a `tree-sitter parse` blob. FIXTURE, not a utility.

  trim_trees.py -N   emit every tree but the last N
  trim_trees.py +N   emit every tree, then the last one N extra times

Reads the blob on stdin, writes it on stdout. Trees kept are byte-identical to
their input; only whole trees are added or removed, so the result is exactly
what tree-sitter would have produced had it parsed that many files.

Used by ./tree-sitter-offsetting-loss to build a chunk that loses N trees and
another that gains N, so a harness checking only the GLOBAL tree total sees
nothing wrong. See README.md.
"""
import sys

MARKER = b"\n(source_file"

mode = sys.argv[1]
n = int(mode[1:])
data = sys.stdin.buffer.read()

if data.startswith(b"(source_file"):
    start = 0
else:
    hit = data.find(MARKER)
    if hit < 0:                       # no trees at all — pass through untouched
        sys.stdout.buffer.write(data)
        raise SystemExit(0)
    start = hit + 1

parts = data[start:].split(MARKER)
# split() ate the "\n" that terminated each tree; put it back on every tree
# but the last, which kept its own.
trees = [parts[0]] + [MARKER[1:] + p for p in parts[1:]]
trees = [t if t.endswith(b"\n") else t + b"\n" for t in trees]

if mode[0] == "-":
    if n >= len(trees):
        sys.exit("trim_trees: asked to drop %d of %d trees" % (n, len(trees)))
    trees = trees[:-n]
else:
    trees = trees + [trees[-1]] * n

sys.stdout.buffer.write(b"".join(trees))
