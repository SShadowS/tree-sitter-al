#!/usr/bin/env python3
"""check-runtime-ranges.py -- every declared tree-sitter runtime range must load our ABI.

src/parser.c declares `#define LANGUAGE_VERSION N` (the ABI). A runtime loads a
grammar only when N lies in [TREE_SITTER_MIN_COMPATIBLE_LANGUAGE_VERSION,
TREE_SITTER_LANGUAGE_VERSION] of the tree-sitter it bundles. A manifest that
admits an older runtime ships an install that resolves fine and then refuses to
load the grammar: pyproject's `core = ["tree-sitter~=0.24"]` admitted 0.24.x,
which tops out at ABI 14, for as long as this grammar was ABI 15.

This reads LANGUAGE_VERSION and every declared range, maps each range onto the
hand-maintained RUNTIMES table below, and fails when any runtime version the
range admits cannot load the ABI. The table is hand-maintained ON PURPOSE: it is
the contract, and nothing generated from this repo can tell you what a released
runtime supports.

Exit: 0 every range is safe; 1 a range admits a runtime that cannot load the ABI
(or one older than the table knows); 2 a manifest, a declaration or a range
cannot be read -- never a pass.

    python tools/check-runtime-ranges.py [--root DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

INF = (10**9,)

# runtime -> [(first version, min ABI, max ABI)], ascending. Each entry holds
# from its version up to the next entry's. A range whose lower bound is below
# the first entry admits versions this table cannot vouch for, and fails.
# Every ABI pair is the `#define TREE_SITTER_MIN_COMPATIBLE_LANGUAGE_VERSION` /
# `#define TREE_SITTER_LANGUAGE_VERSION` of the runtime's bundled api.h, read
# from the released package on 2026-10-01 (roadmap A6). The entry before the
# minimum is the newest release that does NOT load ABI 15.
RUNTIMES = {
    # PyPI `tree-sitter` sdist: tree_sitter/core/lib/include/tree_sitter/api.h
    "python": [("0.24.0", 13, 14), ("0.25.0", 13, 15)],
    # npm `tree-sitter` tarball: vendor/tree-sitter/lib/include/tree_sitter/api.h.
    # npm has no 0.23.x or 0.24.x; 0.22.4 is the release before 0.25.0.
    "node": [("0.22.4", 13, 14), ("0.25.0", 13, 15)],
    # crates.io `tree-sitter` crate: include/tree_sitter/api.h. (tree-sitter-language
    # 0.1 is only the LanguageFn pointer wrapper and is ABI-agnostic, so not checked.)
    "rust": [("0.24.7", 13, 14), ("0.25.0", 13, 15)],
    # proxy.golang.org module zip: include/tree_sitter/api.h
    "go": [("0.23.1", 13, 14), ("0.24.0", 13, 14), ("0.25.0", 13, 15)],
    # github.com/smacker/go-tree-sitter: api.h at the module root. Its newest
    # pseudo-version (v0.0.0-20240827094217-dd81d9e9be82) is still 13..14, so no
    # version of it loads ABI 15.
    "go-smacker": [("0.0.0", 13, 14)],
    # SwiftTreeSitter (ChimeHQ) bundles no api.h; its Package.swift pins the
    # tree-sitter package: 0.9.0 `.upToNextMinor(from: "0.23.0")` (ABI 13..14),
    # 0.10.0 `.upToNextMinor(from: "0.25.0")` (ABI 13..15).
    "swift": [("0.9.0", 13, 14), ("0.10.0", 13, 15)],
}


class Unreadable(Exception):
    """A manifest, declaration or range this script cannot interpret: exit 2."""


def pad(v: tuple) -> tuple:
    """0.25 and 0.25.0 must compare equal, so every version is held as 3 components."""
    return v + (0,) * (3 - len(v))


def ver(text: str, raw: bool = False) -> tuple:
    m = re.fullmatch(r"v?(\d+(?:\.\d+)*)(?:[-+].*)?", text.strip())
    if not m:
        raise Unreadable(f"not a version: {text!r}")
    v = tuple(int(p) for p in m.group(1).split("."))
    return v if raw else pad(v)


def bump(v: tuple, index: int) -> tuple:
    """The exclusive bound just past v's component `index`: bump(0.25.2, 1) = 0.26.0."""
    return pad(v[:index] + (v[index] + 1,))


def pep440(spec: str) -> tuple:
    lo, hi = (0, 0, 0), INF
    for part in spec.split(","):
        m = re.fullmatch(r"\s*(~=|>=|==|<)\s*([\w.]+)\s*", part)
        if not m:
            raise Unreadable(f"unsupported PEP 440 specifier {part.strip()!r}")
        op, v, n = m.group(1), ver(m.group(2)), len(ver(m.group(2), raw=True))
        if op == "~=":  # ~=0.25 is >=0.25,==0.*; ~=0.25.0 is >=0.25.0,==0.25.*
            if n < 2:
                raise Unreadable(f"~= needs two components: {part.strip()!r}")
            lo, hi = max(lo, v), min(hi, bump(v, n - 2))
        elif op == ">=":
            lo = max(lo, v)
        elif op == "<":
            hi = min(hi, v)
        else:
            lo, hi = max(lo, v), min(hi, bump(v, n - 1))
    return lo, hi


def caret(v: tuple) -> tuple:
    """npm/Cargo ^v: up to the first non-zero component (^0.25.0 -> <0.26.0, ^0.25 too)."""
    for i, p in enumerate(v):
        if p or i == len(v) - 1:
            return bump(v, i)


def semver(spec: str) -> tuple:
    """npm range or Cargo requirement: ^X, ~X, >=X, =X or bare X."""
    m = re.fullmatch(r"\s*(\^|~|>=|=)?\s*v?(\d+(?:\.\d+){0,2})\s*", spec)
    if not m:
        raise Unreadable(f"unsupported range {spec!r}")
    op, raw = m.group(1), ver(m.group(2), raw=True)
    if op == ">=":
        return pad(raw), INF
    if op == "~":
        return pad(raw), bump(raw, min(1, len(raw) - 1))
    return pad(raw), caret(raw)


def declarations(root: Path):
    """Yield (where, runtime, spec, (lo, hi_exclusive)). Raises Unreadable."""
    def read(rel):
        p = root / rel
        if not p.is_file():
            raise Unreadable(f"{rel}: missing")
        return p.read_text(encoding="utf-8")

    deps = tomllib.loads(read("pyproject.toml")).get("project", {}).get("optional-dependencies", {}).get("core", [])
    reqs = [d for d in deps if re.match(r"tree[-_]sitter(?![-_\w])", d)]
    if len(reqs) != 1:
        raise Unreadable(f"pyproject.toml: expected one tree-sitter in [project.optional-dependencies].core, found {reqs}")
    spec = reqs[0][len("tree-sitter"):]
    yield "pyproject.toml [core]", "python", reqs[0], pep440(spec)

    req = [line.strip() for line in read("tools/query_coverage/requirements.txt").splitlines()
           if re.match(r"tree[-_]sitter(?![-_\w])", line.strip())]
    if len(req) != 1:
        raise Unreadable("tools/query_coverage/requirements.txt: expected one tree-sitter line")
    yield "tools/query_coverage/requirements.txt", "python", req[0], pep440(req[0][len("tree-sitter"):])

    peer = json.loads(read("package.json")).get("peerDependencies", {}).get("tree-sitter")
    if peer is None:
        raise Unreadable("package.json: no peerDependencies.tree-sitter")
    yield "package.json peerDependencies", "node", f"tree-sitter {peer}", semver(peer)

    dev = tomllib.loads(read("Cargo.toml")).get("dev-dependencies", {}).get("tree-sitter")
    if isinstance(dev, dict):
        dev = dev.get("version")
    if not isinstance(dev, str):
        raise Unreadable("Cargo.toml: no [dev-dependencies] tree-sitter version")
    yield "Cargo.toml [dev-dependencies]", "rust", f'tree-sitter = "{dev}"', semver(dev)

    # The root module, plus any nested binding module (bindings/go/go.mod was one until A6).
    gomods = ["go.mod"] + sorted(p.relative_to(root).as_posix() for p in root.glob("bindings/**/go.mod"))
    found = 0
    for rel in gomods:
        for m in re.finditer(r"github\.com/(tree-sitter|smacker)/go-tree-sitter\s+(v\S+)", read(rel)):
            found += 1
            # Go's minimal version selection: the required version IS the floor.
            runtime = "go" if m.group(1) == "tree-sitter" else "go-smacker"
            yield rel, runtime, m.group(0), (ver(m.group(2)), INF)
    if not found:
        raise Unreadable("no go.mod requires a go-tree-sitter runtime")

    m = re.search(r'\.package\(\s*url:\s*"[^"]*(?:SwiftTreeSitter|swift-tree-sitter)[^"]*",\s*from:\s*"([^"]+)"\s*\)',
                  read("Package.swift"))
    if not m:
        raise Unreadable('Package.swift: no SwiftTreeSitter `.package(url: ..., from: "X")`')
    v = ver(m.group(1))
    yield "Package.swift", "swift", f'from: "{m.group(1)}"', (v, bump(v, 0))  # SPM from: = up to next major


def fmt(v: tuple) -> str:
    return "inf" if v == INF else ".".join(map(str, v))


def check(runtime: str, lo: tuple, hi: tuple, abi: int) -> list[str]:
    """The problems with admitting [lo, hi) of `runtime` for a grammar of ABI `abi`."""
    table = [(ver(v), a, b) for v, a, b in RUNTIMES[runtime]]
    if lo < table[0][0]:
        return [f"admits {fmt(lo)}, older than the table's first entry {fmt(table[0][0])}"]
    bad = []
    for i, (start, amin, amax) in enumerate(table):
        end = table[i + 1][0] if i + 1 < len(table) else INF
        if start < hi and lo < end and not amin <= abi <= amax:
            bad.append(f"admits {fmt(max(lo, start))}..<{fmt(min(hi, end))}, which loads ABI {amin}..{amax}, not {abi}")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args(argv)
    try:
        m = re.search(r"^#define LANGUAGE_VERSION (\d+)$", (args.root / "src/parser.c").read_text(encoding="utf-8"), re.M)
        if not m:
            raise Unreadable("src/parser.c: no `#define LANGUAGE_VERSION N`")
        abi = int(m.group(1))
        decls = list(declarations(args.root))
    except (Unreadable, OSError, ValueError) as e:
        print(f"check-runtime-ranges: cannot run: {e}", file=sys.stderr)
        return 2
    print(f"grammar ABI {abi} (src/parser.c LANGUAGE_VERSION)")
    failed = 0
    for where, runtime, spec, (lo, hi) in decls:
        problems = check(runtime, lo, hi, abi)
        failed += bool(problems)
        print(f"{'FAIL' if problems else 'ok  '} {runtime:10} {where}: {spec}  [{fmt(lo)}, {fmt(hi)})")
        for p in problems:
            print(f"       {p}")
    print(f"{len(decls)} range(s), {failed} admit a runtime that cannot load ABI {abi}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
