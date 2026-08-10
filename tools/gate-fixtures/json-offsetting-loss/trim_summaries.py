#!/usr/bin/env python3
"""Drop or duplicate records in a `tree-sitter parse --json-summary` stream.

FIXTURE, not a utility.

  trim_summaries.py -N   emit every parse_summaries record but the last N
  trim_summaries.py +N   emit every record, then the last one N extra times

Reads the whole stdout of a `--json-summary` run on stdin and writes it back on
stdout. The `\\tParse:` diagnostic lines that precede the JSON are passed
through untouched; only the record list changes.

This is the JSON counterpart of ../offsetting-loss/trim_trees.py. That one
splits on `(source_file` markers, which a `-q --json-summary` run never emits —
so pointed at this script's caller it finds no trees and passes the stream
through unchanged, i.e. injects nothing at all. A counter that reads the JSON
needs a fixture that corrupts the JSON.

If the stream is not shaped as expected, this FAILS rather than passing the
input through: a fixture that silently injects nothing turns a gate test into a
tautology, which is the exact fault the gate suite exists to find.
"""
import json
import sys

mode = sys.argv[1]
n = int(mode[1:])
data = sys.stdin.read()

# The JSON object starts at the first line that is exactly "{" — the only
# unindented brace, since --json-summary pretty-prints.
lines = data.splitlines(keepends=True)
start = next((i for i, ln in enumerate(lines) if ln.rstrip("\r\n") == "{"), None)
if start is None:
    sys.exit("trim_summaries: no JSON object on stdin — nothing to corrupt")

prefix = "".join(lines[:start])
doc = json.loads("".join(lines[start:]))
records = doc.get("parse_summaries")
if not isinstance(records, list) or not records:
    sys.exit("trim_summaries: no parse_summaries records to corrupt")

if mode[0] == "-":
    if n >= len(records):
        sys.exit("trim_summaries: asked to drop %d of %d records" % (n, len(records)))
    doc["parse_summaries"] = records[:-n]
else:
    doc["parse_summaries"] = records + [records[-1]] * n

sys.stdout.write(prefix)
json.dump(doc, sys.stdout, indent=2)
sys.stdout.write("\n")
