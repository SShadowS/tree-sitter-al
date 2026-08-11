#!/usr/bin/env python3
"""Total validation of ONE AL file: is the tree complete, and is it right?

Two questions, and they are not the same one:

  SOUNDNESS    everything the parser reports is true of the source
  COMPLETENESS everything in the source reaches the tree

A parser can be perfectly sound and still drop half the file. 4.0.0 shipped
because 574,694 source bytes belonged to no node while every gate in the repo
was green: `parse-al-parallel.sh` counted zero errors, the tree hash matched,
and `tree-sitter test` passed. None of those can see a token that was lexed
and then thrown away.

Every check below is written so that it CAN FAIL, and `--self-test` proves each
one does by breaking something on purpose and requiring the right check --
not merely some check -- to report it. A validator whose checks have only ever
passed is indistinguishable from a validator that checks nothing; that is the
single most expensive lesson of this project, and it is why this file has a
self-test at all.

Usage:
    python tools/validate_al_file.py path/to/File.al
    python tools/validate_al_file.py path/to/File.al --json
    python tools/validate_al_file.py --self-test

Exit codes:
    0  every check passed
    1  at least one check failed
    2  could not run (unreadable file, parser build failure)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field as dc_field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import tree_sitter  # noqa: E402

from tools.query_coverage import anchors, loader  # noqa: E402

EXIT_OK, EXIT_FAIL, EXIT_CANNOT_RUN = 0, 1, 2


@dataclass
class Finding:
    check: str
    detail: str
    where: str = ""


@dataclass
class CheckResult:
    name: str
    headline: str
    findings: list[Finding] = dc_field(default_factory=list)
    # A check that could not run is NOT a pass. Reporting "0 findings" when the
    # check never executed is the exact shape this whole file exists to prevent.
    ran: bool = True

    @property
    def ok(self) -> bool:
        return self.ran and not self.findings


# --------------------------------------------------------------------------
# 1. Parse integrity
# --------------------------------------------------------------------------

def check_parse_integrity(tree, src: bytes) -> CheckResult:
    """ERROR and MISSING nodes, with positions.

    This is the check every other tool in the repo already performs, and it is
    the weakest of the six: every defect found in 4.0.0 produced a clean error
    count. It is here to be first and to be insufficient.
    """
    findings: list[Finding] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.is_error or node.is_missing:
            kind = "MISSING" if node.is_missing else "ERROR"
            r, c = node.start_point
            findings.append(
                Finding(
                    "parse-integrity",
                    f"{kind} node of type {node.type!r}",
                    f"line {r + 1}, col {c + 1}",
                )
            )
        stack.extend(node.children)
    return CheckResult(
        "parse-integrity",
        f"{len(findings)} ERROR/MISSING node(s)",
        findings,
    )


# --------------------------------------------------------------------------
# 2. Byte-exact round trip  (COMPLETENESS)
# --------------------------------------------------------------------------

def _leaves(root):
    stack, out = [root], []
    while stack:
        n = stack.pop()
        if n.child_count == 0:
            out.append(n)
        else:
            stack.extend(reversed(n.children))
    out.sort(key=lambda n: n.start_byte)
    return out


def check_byte_roundtrip(tree, src: bytes, *, _drop_leaf: int | None = None) -> CheckResult:
    """Every non-whitespace byte must belong to some leaf node.

    Reconstructs the file from the leaves and the gaps between them. A gap
    holding anything other than whitespace is a byte the parser lexed and
    dropped -- invisible to every error count, because a dropped token leaves
    no ERROR behind. This is the check that would have caught the 574,694.

    `_drop_leaf` is for --self-test only: it removes one leaf from the walk to
    prove this check reports what it is supposed to report.
    """
    leaves = _leaves(tree.root_node)
    if _drop_leaf is not None and 0 <= _drop_leaf < len(leaves):
        leaves = leaves[:_drop_leaf] + leaves[_drop_leaf + 1:]

    findings: list[Finding] = []
    rebuilt = bytearray()
    cursor = 0
    for leaf in leaves:
        if leaf.start_byte < cursor:
            continue  # overlapping leaf; covered by the reconstruction compare
        gap = src[cursor:leaf.start_byte]
        if gap.strip():
            r = src[:cursor].count(b"\n") + 1
            findings.append(
                Finding(
                    "byte-roundtrip",
                    f"{len(gap.strip())} non-whitespace byte(s) in no node: "
                    f"{gap.strip()[:60]!r}",
                    f"line {r}, byte {cursor}",
                )
            )
        rebuilt += gap
        rebuilt += src[leaf.start_byte:leaf.end_byte]
        cursor = max(cursor, leaf.end_byte)
    tail = src[cursor:]
    if tail.strip():
        findings.append(
            Finding(
                "byte-roundtrip",
                f"{len(tail.strip())} trailing non-whitespace byte(s) in no node: "
                f"{tail.strip()[:60]!r}",
                f"byte {cursor}",
            )
        )
    rebuilt += tail

    if bytes(rebuilt) != src:
        findings.append(
            Finding(
                "byte-roundtrip",
                f"reconstruction differs from source "
                f"({len(rebuilt)} bytes rebuilt vs {len(src)} original)",
            )
        )
    return CheckResult(
        "byte-roundtrip",
        f"{len(leaves)} leaves cover {len(src)} bytes",
        findings,
    )


# --------------------------------------------------------------------------
# 3. Independent-lexer reconciliation  (COMPLETENESS)
# --------------------------------------------------------------------------

def _count_nodes(root, wanted: set[str]) -> dict[str, int]:
    counts = dict.fromkeys(wanted, 0)
    stack = [root]
    while stack:
        n = stack.pop()
        # `is_named` is load-bearing -- see the note on _named_nodes below.
        if n.is_named and n.type in counts:
            counts[n.type] += 1
        stack.extend(n.children)
    return counts


def _named_nodes(root):
    """Walk NAMED nodes only.

    Matching on `node.type` alone is wrong in this grammar, and the reason is
    the keyword design rather than a defect. Every keyword rule is
    `alias(kw('word'), 'word')`, which gives the named `x_keyword` node exactly
    one ANONYMOUS child whose type string is the canonical lowercase spelling.
    Several of those spellings are also named rule types:

        procedure          named=True   kids=6   <- the rule
          procedure_keyword  named=True   kids=1
            procedure          named=False  kids=0   <- anonymous child

    Both report `node.type == "procedure"`. A type-keyed lookup that ignores
    `is_named` therefore finds a childless "procedure" with no fields on it and
    reports every one of them as a required field returning None. That is what
    this validator did on its own first run, against a six-line file.

    The same collision exists for `table`, `key`, `value`, `field`, `record`
    and every other keyword whose spelling doubles as a rule name.
    """
    stack, out = [root], []
    while stack:
        n = stack.pop()
        if n.is_named:
            out.append(n)
        stack.extend(n.children)
    return out


def check_anchor_reconciliation(tree, src: bytes, *, _skip_type: str | None = None) -> CheckResult:
    """Read the file a SECOND time, with a regex, and require the two to agree.

    The point is independence. A count derived from the parser cannot detect
    the parser failing to produce a node -- it would be counting the same
    absence twice. These regexes know nothing about the grammar.

    Shares `anchors.ANCHORS` with the corpus-wide harness so the two cannot
    drift apart into disagreeing definitions of the same word.
    """
    text = src.decode("utf-8", errors="replace")
    findings: list[Finding] = []
    lines = []
    for anchor in anchors.ANCHORS:
        lexical = len(re.findall(anchor.pattern, text, re.IGNORECASE))
        types = tuple(t for t in anchor.node_types if t != _skip_type)
        nodes = sum(_count_nodes(tree.root_node, set(types)).values()) if types else 0
        lines.append(f"{anchor.name}={lexical}/{nodes}")
        if lexical != nodes:
            findings.append(
                Finding(
                    "anchor-reconciliation",
                    f"{anchor.name!r}: {lexical} lexical occurrence(s) in the source "
                    f"but {nodes} node(s) of {'+'.join(types) or '(none)'}",
                )
            )
    return CheckResult(
        "anchor-reconciliation",
        " ".join(lines),
        findings,
    )


# --------------------------------------------------------------------------
# 4. Required-field population  (SOUNDNESS)
# --------------------------------------------------------------------------

def _declared_required_fields() -> dict[str, list[str]]:
    node_types = json.loads((REPO_ROOT / "src" / "node-types.json").read_text("utf-8"))
    out: dict[str, list[str]] = {}
    for entry in node_types:
        if not entry.get("named"):
            continue
        req = [n for n, spec in (entry.get("fields") or {}).items() if spec.get("required")]
        if req:
            out[entry["type"]] = req
    return out


def check_required_fields(
    tree, src: bytes, *, _force_miss: bool = False, _ignore_is_named: bool = False
) -> CheckResult:
    """A field `node-types.json` declares required must be populated on every
    real instance in this file.

    `node-types.json` is generated from the grammar, so it can only say what
    the grammar currently does -- it can never fail a contract. What it CAN do
    is describe an expectation that a live instance then violates, which is a
    grammar defect rather than a documentation one. Release defects 4 and 5
    were exactly this shape and surfaced only because those fields happened to
    be `required`.
    """
    required = _declared_required_fields()
    findings: list[Finding] = []
    seen = 0
    if _ignore_is_named:
        # --self-test only: the naive walk, kept so the trap it falls into
        # stays pinned rather than being rediscovered.
        walk, stack = [], [tree.root_node]
        while stack:
            n = stack.pop()
            walk.append(n)
            stack.extend(n.children)
    else:
        walk = _named_nodes(tree.root_node)

    for node in walk:
        for name in required.get(node.type, ()):
            seen += 1
            missing = _force_miss or node.child_by_field_name(name) is None
            if missing:
                r, c = node.start_point
                findings.append(
                    Finding(
                        "required-fields",
                        f"{node.type}.{name} is declared required but is None",
                        f"line {r + 1}, col {c + 1}",
                    )
                )
    return CheckResult(
        "required-fields",
        f"{seen} required-field slot(s) checked",
        findings,
    )


# --------------------------------------------------------------------------
# 5. Extraction fidelity  (SOUNDNESS)
# --------------------------------------------------------------------------

EXTRACT_QUERY = """
(table_declaration object_id: (integer) @id object_name: (_) @name) @obj
(codeunit_declaration object_id: (integer) @id object_name: (_) @name) @obj
(page_declaration object_id: (integer) @id object_name: (_) @name) @obj
(report_declaration object_id: (integer) @id object_name: (_) @name) @obj
(field_declaration id: (integer) @f.id name: (_) @f.name type: (_) @f.type)
(property name: (property_name) @p.name value: (_) @p.value)
(procedure name: (identifier) @proc)
(trigger_declaration name: (_) @trig)
(key_declaration name: (_) @key)
(variable_declaration name: (identifier) @var type: (_) @var.type)
"""


def check_extraction_fidelity(tree, src: bytes, language, *, _corrupt: bool = False) -> CheckResult:
    """Every captured value must equal the source bytes at its own span.

    Byte-span agreement is cheap but not the point; the point is that a value
    is reachable BY FIELD NAME at all. A consumer that has to descend by child
    index is reading a different tree from the one node-types.json describes,
    and `..` / precedence defects moved exactly that kind of attachment while
    every byte stayed where it was.
    """
    try:
        query = tree_sitter.Query(language, EXTRACT_QUERY)
    except tree_sitter.QueryError as exc:
        # A query naming a type the grammar does not declare raises rather than
        # returning nothing -- so this is a hard failure, never a quiet zero.
        return CheckResult(
            "extraction-fidelity",
            f"query failed to compile: {exc}",
            [Finding("extraction-fidelity", f"QueryError: {exc}")],
            ran=False,
        )

    cursor = tree_sitter.QueryCursor(query)
    findings: list[Finding] = []
    captured = 0
    kinds: dict[str, int] = {}
    for _idx, caps in cursor.matches(tree.root_node):
        for name, nodes in caps.items():
            for node in nodes:
                captured += 1
                kinds[name] = kinds.get(name, 0) + 1
                actual = src[node.start_byte:node.end_byte]
                if _corrupt:
                    actual = actual + b"!"
                if actual != node.text:
                    r, c = node.start_point
                    findings.append(
                        Finding(
                            "extraction-fidelity",
                            f"@{name} text {node.text!r} != source span {actual!r}",
                            f"line {r + 1}, col {c + 1}",
                        )
                    )
    if captured == 0:
        findings.append(
            Finding(
                "extraction-fidelity",
                "the extraction query captured NOTHING -- an empty result and a "
                "correct-but-empty file are indistinguishable, so this is a failure",
            )
        )
    summary = " ".join(f"{k}={v}" for k, v in sorted(kinds.items()))
    return CheckResult("extraction-fidelity", summary or "(no captures)", findings)


# --------------------------------------------------------------------------
# 6. Query reachability  (COMPLETENESS, for consumers)
# --------------------------------------------------------------------------

def check_query_reachability(tree, src: bytes, language, *, _pretend_unmatched: str | None = None) -> CheckResult:
    """Named node types this file produces that NO shipped query matches.

    Losslessness puts a byte in a node; this asks whether anyone can address
    it. A node type nothing captures is data the CST holds and no consumer can
    retrieve, which is the other half of "queries retrieve the expected data".
    """
    produced: set[str] = set()
    stack = [tree.root_node]
    while stack:
        n = stack.pop()
        if n.is_named:
            produced.add(n.type)
        stack.extend(n.children)

    matched: set[str] = set()
    qdir = REPO_ROOT / "queries"
    scanned = 0
    for scm in sorted(qdir.glob("*.scm")):
        try:
            q = tree_sitter.Query(language, scm.read_text("utf-8"))
        except tree_sitter.QueryError as exc:
            return CheckResult(
                "query-reachability",
                f"{scm.name} does not compile",
                [Finding("query-reachability", f"{scm.name}: {exc}")],
                ran=False,
            )
        scanned += 1
        cur = tree_sitter.QueryCursor(q)
        for _idx, caps in cur.matches(tree.root_node):
            for nodes in caps.values():
                for node in nodes:
                    if node.is_named:
                        matched.add(node.type)

    if _pretend_unmatched:
        matched.discard(_pretend_unmatched)

    unmatched = sorted(produced - matched)
    findings = [
        Finding("query-reachability", f"{t} is produced by this file but no shipped query matches it")
        for t in unmatched
    ]
    return CheckResult(
        "query-reachability",
        f"{len(produced)} named type(s) produced, {len(matched)} reachable, "
        f"{scanned} query file(s) scanned",
        findings,
    )


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

def _parser():
    lib = loader.ensure_library(REPO_ROOT)
    language = loader.load_language(lib)
    return loader.make_parser(language), language


def validate(path: Path, *, informational: frozenset[str] = frozenset({"query-reachability"})):
    src = path.read_bytes()
    parser, language = _parser()
    tree = parser.parse(src)
    results = [
        check_parse_integrity(tree, src),
        check_byte_roundtrip(tree, src),
        check_anchor_reconciliation(tree, src),
        check_required_fields(tree, src),
        check_extraction_fidelity(tree, src, language),
        check_query_reachability(tree, src, language),
    ]
    return results, informational


def _render(path: Path, results, informational) -> int:
    print(f"AL total validation -- {path}")
    print("=" * 72)
    failed = 0
    for r in results:
        if r.ok:
            mark, note = "PASS", ""
        elif not r.ran:
            mark, note = "CANNOT RUN", "  <- not a pass"
        elif r.name in informational:
            mark, note = "NOTE", "  (informational, not gating)"
        else:
            mark, note = "FAIL", ""
        if not r.ok and r.name not in informational:
            failed += 1
        print(f"  {mark:<10} {r.name:<24} {r.headline}{note}")
        for f in r.findings[:20]:
            where = f" [{f.where}]" if f.where else ""
            print(f"             - {f.detail}{where}")
        if len(r.findings) > 20:
            print(f"             ... and {len(r.findings) - 20} more")
    print("=" * 72)
    print("RESULT:", "PASS" if failed == 0 else f"FAIL ({failed} gating check(s))")
    return EXIT_OK if failed == 0 else EXIT_FAIL


# --------------------------------------------------------------------------
# Self-test: every check must be shown to fail on purpose
# --------------------------------------------------------------------------

SELF_TEST_AL = b"""codeunit 50100 SelfTest
{
    procedure P()
    var
        Cust: Record Customer;
    begin
        if Cust.Get('X') then
            Cust.Delete(true);
    end;

    trigger OnRun()
    begin
    end;
}
"""


def self_test() -> int:
    """Break something on purpose; require the RIGHT check to notice.

    Each case names the check it targets. A case that fails the wrong check is
    not a pass -- that distinction is the whole value of the exercise, because
    a validator where any breakage trips any check tells you nothing about
    which property actually held.
    """
    parser, language = _parser()
    ok = True

    def report(case: str, target: str, res: CheckResult, want_fail: bool) -> None:
        nonlocal ok
        fired = not res.ok
        good = fired == want_fail
        ok = ok and good
        verb = "fires" if want_fail else "stays silent"
        print(f"  {'PASS' if good else 'FAIL'}  {case:<44} {target} {verb}")
        if not good and res.findings:
            print(f"        unexpected: {res.findings[0].detail[:90]}")

    src = SELF_TEST_AL
    tree = parser.parse(src)

    # Control. If this is not clean, every case below is meaningless.
    base = [
        check_parse_integrity(tree, src),
        check_byte_roundtrip(tree, src),
        check_anchor_reconciliation(tree, src),
        check_required_fields(tree, src),
        check_extraction_fidelity(tree, src, language),
    ]
    for r in base:
        report(f"control: clean file, {r.name}", r.name, r, want_fail=False)

    # 1. parse integrity -- remove a closing brace
    broken = src.replace(b"}\n", b"", 1)
    report(
        "unbalanced braces",
        "parse-integrity",
        check_parse_integrity(parser.parse(broken), broken),
        want_fail=True,
    )

    # 2. byte round trip -- drop one leaf from the walk. There is no source
    #    mutation that makes a CORRECT grammar drop a byte, so the fault has to
    #    be injected into the checker's own view.
    report(
        "one leaf removed from the walk",
        "byte-roundtrip",
        check_byte_roundtrip(tree, src, _drop_leaf=3),
        want_fail=True,
    )

    # 3. anchor reconciliation -- stop counting one node type
    report(
        "anchor's node type not counted",
        "anchor-reconciliation",
        check_anchor_reconciliation(tree, src, _skip_type="procedure_keyword"),
        want_fail=True,
    )

    # 4. required fields -- force a miss
    report(
        "required field forced to None",
        "required-fields",
        check_required_fields(tree, src, _force_miss=True),
        want_fail=True,
    )

    # 4b. The anonymous-child collision. `procedure_keyword`'s anonymous child
    #     reports type "procedure", the same string as the named rule, so a
    #     type-keyed walk that ignores `is_named` finds a childless "procedure"
    #     and reports its every required field as None. This validator did
    #     exactly that on its first run. Pinned so the filter cannot be
    #     "simplified" away.
    report(
        "type-keyed walk ignoring is_named",
        "required-fields",
        check_required_fields(tree, src, _ignore_is_named=True),
        want_fail=True,
    )

    # 5. extraction fidelity -- corrupt the compared span
    report(
        "captured span corrupted",
        "extraction-fidelity",
        check_extraction_fidelity(tree, src, language, _corrupt=True),
        want_fail=True,
    )

    # 5b. extraction fidelity -- a file with nothing to extract must NOT read as
    #     a pass. An empty result and a correct-but-empty file look identical.
    empty = b"// just a comment\n"
    report(
        "file with no extractable data",
        "extraction-fidelity",
        check_extraction_fidelity(parser.parse(empty), empty, language),
        want_fail=True,
    )

    # 6. query reachability -- pretend a produced type is unmatched
    report(
        "produced type marked unreachable",
        "query-reachability",
        check_query_reachability(tree, src, language, _pretend_unmatched="procedure_keyword"),
        want_fail=True,
    )

    print()
    print("self-test:", "all cases behaved as specified" if ok else "SOME CASES MISBEHAVED")
    return EXIT_OK if ok else EXIT_FAIL


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", type=Path, help="the .al file to validate")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="prove every check can fail")
    ap.add_argument(
        "--strict-reachability",
        action="store_true",
        help="treat unreachable node types as a gating failure rather than a note",
    )
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.file is None:
        ap.error("give a file, or --self-test")
    if not args.file.is_file():
        print(f"cannot read {args.file}", file=sys.stderr)
        return EXIT_CANNOT_RUN

    informational = frozenset() if args.strict_reachability else frozenset({"query-reachability"})
    results, informational = validate(args.file, informational=informational)

    if args.json:
        payload = {
            "file": str(args.file),
            "checks": [
                {
                    "name": r.name,
                    "ran": r.ran,
                    "ok": r.ok,
                    "headline": r.headline,
                    "findings": [
                        {"detail": f.detail, "where": f.where} for f in r.findings
                    ],
                }
                for r in results
            ],
        }
        print(json.dumps(payload, indent=2))
        gating = [r for r in results if not r.ok and r.name not in informational]
        return EXIT_OK if not gating else EXIT_FAIL

    return _render(args.file, results, informational)


if __name__ == "__main__":
    raise SystemExit(main())
