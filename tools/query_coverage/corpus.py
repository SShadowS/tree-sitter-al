"""Corpus selection by greedy set-cover, and the committed manifest.

Not biggest-file-per-type: the biggest Query file (13.6 KB) produces zero
findings, and the biggest Table burns 580 KB repeating `record` and `:=`.
Big means repetitive, not diverse.

Object type comes from the tree root, never the filename. BC.History suffixes
are inconsistent — 527 *.PermissionSet.al, 276 *.permissionset.al,
15 *.Permissionset.al, plus 30 files with no suffix at all.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .model import Finding

MANIFEST_HEADER = "# object_types\tpath\tsha256\tbytes\treason"
DETECTOR = "corpus"


@dataclass(frozen=True)
class ManifestEntry:
    object_types: tuple[str, ...]
    path: str
    sha256: str
    bytes: int
    reason: str


def select(vocabularies: dict[str, set[str]]) -> list[str]:
    """Greedy set-cover. Ties break on path ascending so `select` is reproducible.

    Non-deterministic tie-breaking churns the manifest, which invalidates every
    baseline count.
    """
    remaining = {path: set(vocab) for path, vocab in vocabularies.items()}
    covered: set[str] = set()
    picked: list[str] = []

    while True:
        best_path = None
        best_gain = 0
        for path in sorted(remaining):
            gain = len(remaining[path] - covered)
            if gain > best_gain:
                best_path, best_gain = path, gain

        if best_path is None:
            return picked

        picked.append(best_path)
        covered |= remaining.pop(best_path)


def object_types(tree) -> tuple[str, ...]:
    """Object types declared in this file, from the tree root.

    `namespace_declaration` is excluded explicitly: a namespace directive is
    not an object, even though its name also ends in `_declaration`.

    Objects wrapped in a top-level `#if`/`#endif` are still found. Per
    node-types.json, only `source_file` and `preproc_conditional_object`
    itself can directly hold an object declaration, and
    `preproc_conditional_object` nests arbitrarily deep for nested `#if`
    blocks, so the walk recurses into it. Recursion (not an explicit stack)
    is fine here: depth is bounded by `#if` nesting, which the scanner caps
    at 255 and which in practice runs a handful of levels deep at most --
    nothing like the AST-depth hazard in detectors/_tree.py's walk().

    Branches of an `#if`/`#else` are not deduplicated or resolved to "the
    active one" -- every declaration shape found in the source is reported,
    in source order, because this tool tracks grammar/query coverage, not
    compiled semantics. Two branches with the same object type report that
    type twice; branches with different object types report both.
    """
    types: list[str] = []

    def visit(node) -> None:
        for child in node.named_children:
            if child.type == "namespace_declaration":
                continue
            if child.type == "preproc_conditional_object":
                visit(child)
            elif child.type.endswith("_declaration"):
                types.append(child.type)

    visit(tree.root_node)
    return tuple(types)


def write_manifest(path: Path, entries: list[ManifestEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(MANIFEST_HEADER + "\n")
        for entry in sorted(entries, key=lambda e: e.path):
            handle.write(
                "\t".join(
                    (
                        ",".join(entry.object_types),
                        entry.path,
                        entry.sha256,
                        str(entry.bytes),
                        entry.reason,
                    )
                )
                + "\n"
            )


def read_manifest(path: Path) -> list[ManifestEntry]:
    entries: list[ManifestEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        types, file_path, digest, size, reason = line.split("\t")
        entries.append(
            ManifestEntry(
                object_types=tuple(t for t in types.split(",") if t),
                path=file_path,
                sha256=digest,
                bytes=int(size),
                reason=reason,
            )
        )
    return entries


def manifest_hash(entries: list[ManifestEntry]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda e: e.path):
        digest.update(f"{entry.path}:{entry.sha256}\n".encode("utf-8"))
    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(repo_root: Path, entries: list[ManifestEntry]) -> list[str]:
    """Empty list means the corpus on disk matches the manifest."""
    problems: list[str] = []
    for entry in entries:
        target = repo_root / entry.path
        if not target.is_file():
            problems.append(f"missing: {entry.path}")
            continue
        actual = file_sha256(target)
        if actual != entry.sha256:
            problems.append(f"sha256 drift: {entry.path} (manifest {entry.sha256[:12]}, disk {actual[:12]})")
    return problems


def never_observed(node_types: list[dict], seen: set[str]) -> list[str]:
    """Named types the corpus never produced: dead grammar or uncovered constructs."""
    return sorted(
        entry["type"]
        for entry in node_types
        if entry.get("named") and entry["type"] not in seen
    )


def detect(node_types: list[dict], seen: set[str]) -> list[Finding]:
    """A named type still declared in node-types.json but produced by nothing
    in scope is a grammar-visible defect with byte coverage intact: the type
    stays a possible parse output, but nothing this run parsed ever emitted
    it. `never_observed` already computes the right set; this is what turns
    it into a Finding, so it clusters, baselines and gates like every other
    detector instead of living only in a gitignored report nobody diffs.

    This does NOT catch a rule inlined to a bare string literal -- the type
    then leaves node_types too, so this function never iterates it -- nor a
    keyword rule reverting from `alias(kw('word'), 'word')` to a bare
    `kw('word')`, which still yields a childless `(x_keyword)` leaf and so
    stays observed. See tools/query_coverage/README.md's "Known limitations".

    No source location exists for a type that was never produced, so this is
    the same "detail carries the specifics, the located fields stay at zero"
    shape as fields._skip_finding.
    """
    return [
        Finding(
            detector=DETECTOR,
            category="never-observed",
            fingerprint=("never-observed", name),
            path="src/node-types.json",
            byte_offset=0,
            line=0,
            column=0,
            enclosing=name,
            snippet=f"named node type {name!r} was not produced by any file in scope",
            detail={"type": name},
        )
        for name in never_observed(node_types, seen)
    ]
