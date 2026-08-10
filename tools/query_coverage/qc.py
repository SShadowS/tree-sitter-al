"""Query-coverage harness entry point.

    python -m tools.query_coverage.qc select
    python -m tools.query_coverage.qc run [--all] [--full-corpus] [--full-query-scan]
    python -m tools.query_coverage.qc accept
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import anchors as anchor_table
from . import baseline, corpus, inventory, loader, model
from .detectors import PER_FILE, fields, shipped_queries

# Detector 6 audits the SHIPPED editor queries. They were written for
# highlighting, not exhaustive extraction, so a gap in them is a note, not a
# regression. Nothing in the Finding/Cluster model distinguishes advisory from
# gating findings, so the distinction lives here and is applied before diff().
INFORMATIONAL_DETECTORS = frozenset({"shipped_queries"})

DEFAULT_MANIFEST = Path("tools/query_coverage/manifest.tsv")
DEFAULT_BASELINE = Path("tools/query_coverage/baseline.json")
REPORTS = Path("tools/query_coverage/reports")

# Corpus root swept by --full-corpus. Not parameterized on the CLI: `select`
# already fixes BC.History as the vocabulary source via its own --corpus
# default, and the dead-pattern --full-query-scan sweep hardcodes the same
# root, so this stays consistent with both rather than adding a second knob.
FULL_CORPUS_ROOT = "BC.History"

# model.Provenance.scope values. A baseline is only meaningful against the
# manifest (the 59-file regression gate): cmd_accept refuses anything else,
# because the two scopes' finding counts are not comparable (see cmd_run's
# own --full-corpus refusal, which exists for the identical reason).
SCOPE_MANIFEST = "manifest"
SCOPE_FULL_CORPUS = "full-corpus"


def exit_for(diff: baseline.Diff, report_all: bool) -> int:
    return baseline.EXIT_OK if report_all else baseline.exit_code(diff)


def _load_node_types(repo_root: Path) -> list[dict]:
    return json.loads((repo_root / "src" / "node-types.json").read_text(encoding="utf-8"))


def _load_grammar(repo_root: Path) -> dict:
    return json.loads((repo_root / "src" / "grammar.json").read_text(encoding="utf-8"))


def cmd_select(args) -> int:
    repo_root = Path(args.repo_root)
    lib = loader.ensure_library(repo_root)
    language = loader.load_language(lib)
    parser = loader.make_parser(language)

    roots = [repo_root / part for part in args.corpus]
    files = sorted(
        str(path.relative_to(repo_root).as_posix())
        for root in roots
        for path in root.rglob("*.al")
    )
    print(f"scanning {len(files)} files for node-type vocabulary")

    vocab: dict[str, set[str]] = {}
    types_by_file: dict[str, tuple[str, ...]] = {}
    seen: set[str] = set()

    for rel in files:
        source = (repo_root / rel).read_bytes()
        tree = parser.parse(source)
        names = _named_types(tree.root_node)
        vocab[rel] = names
        types_by_file[rel] = corpus.object_types(tree)
        seen |= names

    picked = corpus.select(vocab)
    entries = [
        corpus.ManifestEntry(
            object_types=types_by_file[rel],
            path=rel,
            sha256=corpus.file_sha256(repo_root / rel),
            bytes=(repo_root / rel).stat().st_size,
            reason="set-cover",
        )
        for rel in picked
    ]
    corpus.write_manifest(repo_root / args.manifest, entries)

    never = corpus.never_observed(_load_node_types(repo_root), seen)
    (repo_root / REPORTS).mkdir(parents=True, exist_ok=True)
    (repo_root / REPORTS / "never-observed.json").write_text(
        json.dumps(never, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    print(f"selected {len(entries)} files; {len(never)} named node types never observed")
    return baseline.EXIT_OK


def _named_types(node) -> set[str]:
    out: set[str] = set()
    stack = [node]
    while stack:
        current = stack.pop()
        if current.is_named:
            out.add(current.type)
        stack.extend(current.children)
    return out


def cmd_run(args) -> int:
    repo_root = Path(args.repo_root)
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path

    # The manifest (59 files) is a regression gate; the full corpus (15,358
    # files) is a discovery sweep. Their finding counts are categorically
    # different -- a manifest run cannot see detector 4's sparse findings
    # (16 findings across 11 files), and a full-corpus run would swamp the
    # manifest baseline with "new" clusters that are really just files the
    # baseline never covered. Refuse the combination outright rather than
    # silently diff apples against oranges.
    if args.full_corpus and not args.all:
        print(
            "--full-corpus counts are not comparable to the manifest baseline; "
            "combine it with --all",
            file=sys.stderr,
        )
        return baseline.EXIT_CORPUS_BROKEN

    if not manifest_path.is_file():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return baseline.EXIT_CORPUS_BROKEN

    entries = corpus.read_manifest(manifest_path)
    problems = corpus.verify(repo_root, entries)
    if problems:
        for problem in problems:
            print(f"corpus: {problem}", file=sys.stderr)
        return baseline.EXIT_CORPUS_BROKEN

    try:
        lib = loader.ensure_library(repo_root)
    except loader.StaleParserError as exc:
        print(f"stale parser: {exc}", file=sys.stderr)
        return baseline.EXIT_STALE_PARSER

    language = loader.load_language(lib)
    parser = loader.make_parser(language)
    node_types = _load_node_types(repo_root)
    grammar = _load_grammar(repo_root)

    findings: list[model.Finding] = []
    findings.extend(fields.detect_static(grammar, node_types))
    findings.extend(inventory.meta_check(language, node_types))

    # Scope: the manifest (default) or every .al file under the corpus root
    # (--full-corpus). Print which one ran, every time -- a report that
    # doesn't say whether it saw 59 files or 15,358 cannot be interpreted.
    # `scope` (not just the print statement) also travels into Provenance
    # below, since that's what lets cmd_accept refuse a full-corpus report
    # baselined under the manifest's hash -- printing alone doesn't stop that,
    # it just describes it after the fact.
    if args.full_corpus:
        scope = SCOPE_FULL_CORPUS
        corpus_root = repo_root / FULL_CORPUS_ROOT
        scope_paths = sorted(
            str(path.relative_to(repo_root).as_posix()) for path in corpus_root.rglob("*.al")
        )
        print(f"scope: {scope} -- {len(scope_paths)} files under {FULL_CORPUS_ROOT}")
    else:
        scope = SCOPE_MANIFEST
        scope_paths = [entry.path for entry in entries]
        print(f"scope: {scope} -- {len(scope_paths)} files")

    # Run-level state, hoisted out of the per-file loop. Both were measured
    # costs, not stylistic ones: detect_keyword_coverage used to recompile the
    # highlights query per file (32.9 ms x 15,358 files = ~8.4 min of a ~31
    # minute full-corpus run) and rebuild its operator set per anonymous node
    # (~6 more minutes). One QueryTally per shipped .scm likewise compiles
    # each query exactly once for the whole run.
    highlights = repo_root / "queries" / "highlights.scm"
    keyword_context = shipped_queries.keyword_coverage_context(
        language, highlights, node_types
    )
    tallies = [
        shipped_queries.QueryTally(language, query_file)
        for query_file in sorted((repo_root / "queries").glob("*.scm"))
    ]
    # Dead-pattern scope. The spec calls for the FULL corpus: a manifest-only
    # tally false-flags patterns for rare constructs that set-cover happened to
    # satisfy from a single file. Under --full-corpus the per-file loop below
    # already visits every file, so the tallies feed inline; --full-query-scan
    # is the narrower knob that sweeps every file for dead patterns (in its own
    # loop further down) without paying for every other detector too.
    tally_inline = args.full_corpus or not args.full_query_scan

    # One streaming pass: every consumer of a tree runs here, inside the
    # file's own iteration, so no tree outlives it. The previous shape
    # accumulated all 15,358 (tree, source) tuples in a `parsed` list to feed
    # two later passes -- ~2.8 GB resident at once, measured -- and the second
    # of those passes re-ran the very query this loop's tally already ran.
    seen_types: set[str] = set()
    for rel in scope_paths:
        source = (repo_root / rel).read_bytes()
        tree = parser.parse(source)
        seen_types |= _named_types(tree.root_node)
        for _name, detect in PER_FILE:
            findings.extend(detect(tree, source, rel))
        findings.extend(fields.detect_dynamic(tree, source, rel, node_types))
        if tally_inline:
            for tally in tallies:
                tally.add(tree)
        # Keyword coverage runs over EVERY file in scope, not just the first.
        # A keyword absent from one file says nothing; the invariant is "no
        # *_keyword node type anywhere in the corpus goes uncaptured".
        # detect_keyword_coverage already dedupes by node type internally, so
        # the union stays small.
        findings.extend(
            shipped_queries.detect_keyword_coverage(keyword_context, tree, source, rel)
        )

    # A named type still declared in node-types.json that stops being
    # produced by anything in scope is grammar-visible with byte coverage
    # intact. Emitting these as real Findings (not just an echoed report) is
    # what makes that class of defect gate like every other one; see
    # corpus.detect's docstring for what this does and does not catch.
    corpus_findings = corpus.detect(node_types, seen_types)
    findings.extend(corpus_findings)
    never = sorted(f.detail["type"] for f in corpus_findings)

    if args.full_corpus:
        print(f"query scan: {len(scope_paths)} files (full corpus, via --full-corpus)")
    elif args.full_query_scan:
        scan_paths = sorted((repo_root / FULL_CORPUS_ROOT).rglob("*.al"))
        for path in scan_paths:
            tree = parser.parse(path.read_bytes())
            for tally in tallies:
                tally.add(tree)
        print(f"query scan: {len(scan_paths)} files (full corpus, via --full-query-scan)")
    else:
        print(
            f"query scan: {len(scope_paths)} files "
            "(manifest subset; use --full-query-scan or --full-corpus for all)"
        )

    for tally in tallies:
        findings.extend(shipped_queries.detect_dead(tally.usages()))

    clusters = model.cluster(findings)

    # Detector 6 is informational and must never change the exit code. That is
    # not enforced by anything in the data model — its findings cluster and
    # baseline exactly like everyone else's — so it must be enforced HERE, by
    # partitioning before the diff. Everything still reaches findings.jsonl and
    # summary.md; only the gate ignores it.
    gating_clusters = [
        c for c in clusters if c.detector not in INFORMATIONAL_DETECTORS
    ]

    baseline_path = repo_root / args.baseline
    manifest_digest = corpus.manifest_hash(entries)
    # Loaded unconditionally, not just inside the `else` below: apply_ratchet
    # near the bottom of this function needs `base` whenever diff.ratcheted is
    # non-empty. That never happens on the full-corpus branch today (an empty
    # baseline.Diff() always has an empty .ratcheted), but that is an
    # invariant a reader has to trace through two branches to see, and a type
    # checker can't see it at all -- it flags `base` as possibly unbound.
    # Loading it here is cheap (one small JSON read) and makes the binding
    # unconditional instead of relying on that invariant staying true.
    base = baseline.load(baseline_path) or baseline.Baseline(manifest_hash=manifest_digest)

    # A full-corpus sweep is a pure reporting pass: its counts are never
    # diffed against the manifest baseline (see the refusal above, which
    # guarantees --all is set whenever we reach this branch).
    if args.full_corpus:
        diff = baseline.Diff()
    else:
        if base.manifest_hash != manifest_digest and not args.all:
            print(
                "baseline was accepted under a different manifest; run `accept` after `select`",
                file=sys.stderr,
            )
            return baseline.EXIT_CORPUS_BROKEN
        diff = baseline.diff(base, gating_clusters)

    provenance = model.Provenance(
        build_stamp=loader.compute_stamp(repo_root),
        manifest_hash=manifest_digest,
        tree_sitter_version=_tree_sitter_version(),
        scope=scope,
    )
    reports = repo_root / REPORTS
    model.write_jsonl(reports / "findings.jsonl", provenance, findings)

    # `never` was computed above from THIS run's own scope, not read back
    # from `select`'s gitignored reports/never-observed.json -- a fresh clone
    # that never ran `select` still gets this section, and it can never drift
    # from what this run actually observed.
    write_summary(reports / "summary.md", clusters, diff, never)

    if diff.ratcheted and not args.all:
        for key, was, now in diff.ratcheted:
            print(f"ratchet: {key} {was} -> {now}")
        baseline.save(baseline_path, baseline.apply_ratchet(base, diff))

    for cluster in diff.new:
        print(f"NEW      {cluster.key}  x{cluster.count}")
    for cluster, accepted in diff.regressed:
        print(f"REGRESS  {cluster.key}  {accepted} -> {cluster.count}")
    for key in diff.fixed:
        print(f"FIXED    {key}")

    return exit_for(diff, args.all)


def cmd_accept(args) -> int:
    repo_root = Path(args.repo_root)
    findings_path = repo_root / REPORTS / "findings.jsonl"
    if not findings_path.is_file():
        print("no report to accept; run `run --all` first", file=sys.stderr)
        return baseline.EXIT_CORPUS_BROKEN

    lines = findings_path.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])

    # A baseline is only meaningful against the manifest: full-corpus counts
    # are ~260x larger (15,358 files vs. 59) for reasons that have nothing to
    # do with regressions, so baselining one under the manifest's hash lets a
    # later plain `run` -- which always diffs against the manifest scope --
    # read every one of those extra findings as newly "fixed". A report from
    # before this field existed has no "scope" key at all; treating that as
    # manifest by default would have silently accepted the exact contaminated
    # baseline this check exists to catch, so a missing key is refused right
    # alongside an explicit non-manifest one rather than assumed benign.
    scope = header.get("scope")
    if scope is None:
        print(
            "refusing to accept: findings.jsonl has no 'scope' field (it predates "
            "scope tracking) and cannot be trusted as manifest-scope. Run "
            "`qc run --all` to regenerate it, then accept again.",
            file=sys.stderr,
        )
        return baseline.EXIT_CORPUS_BROKEN
    if scope != SCOPE_MANIFEST:
        print(
            f"refusing to accept a '{scope}' report; a baseline is only meaningful "
            "against the manifest scope (--full-corpus counts are not comparable). "
            "Run `qc run --all` (without --full-corpus) and accept that instead.",
            file=sys.stderr,
        )
        return baseline.EXIT_CORPUS_BROKEN

    counts: dict[str, int] = {}
    for line in lines[1:]:
        record = json.loads(line)
        # Mirror cmd_run's gating_clusters filter. INFORMATIONAL_DETECTORS
        # findings are excluded from the diff there, so baselining them here
        # would desync the two: the accepted count would sit above zero
        # forever while `run` never re-observes it (having filtered it out
        # before diffing), so every future run would see it as freshly
        # "fixed" and ratchet it back to zero -- spurious churn on every
        # single run, not just the first one after accept.
        if record["detector"] in INFORMATIONAL_DETECTORS:
            continue
        key = record["cluster"]
        counts[key] = counts.get(key, 0) + 1

    baseline.save(
        repo_root / args.baseline,
        baseline.Baseline(manifest_hash=header["manifest_hash"], counts=counts),
    )
    print(f"accepted {len(counts)} clusters")
    return baseline.EXIT_OK


def write_summary(path: Path, clusters, diff, never_seen: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Query-coverage summary", ""]

    if diff.new:
        lines += ["## New clusters", ""]
        lines += [f"- `{c.key}` x{c.count}" for c in diff.new] + [""]
    if diff.regressed:
        lines += ["## Regressed", ""]
        lines += [f"- `{c.key}` {was} -> {c.count}" for c, was in diff.regressed] + [""]
    if diff.fixed:
        lines += ["## Fixed", ""]
        lines += [f"- `{key}`" for key in diff.fixed] + [""]

    lines += ["## All clusters", ""]
    # Most-frequent-first, regardless of the order clusters arrived in.
    # model.cluster() already sorts this way, but write_summary must not
    # depend on its caller having done so -- mirror the same (-count, key)
    # key here so this reads correctly given any input order.
    for cluster in sorted(clusters, key=lambda c: (-c.count, c.key)):
        lines.append(f"### `{cluster.key}` — {cluster.count}")
        lines.append("")
        for example in cluster.examples:
            lines.append(f"- `{example.path}:{example.line}` — {example.snippet}")
        lines.append("")

    if never_seen:
        lines += ["## Never-observed named node types", ""]
        lines += [f"- `{name}`" for name in never_seen] + [""]

    # No silent caps: anything the harness deliberately does not check must say
    # so in its own output. anchors.py defines EXCLUDED_ANCHORS with the comment
    # "Report it, never silently drop it" — this is the consumer that keeps that
    # promise. Without it the dict is source-level documentation only, invisible
    # to anyone actually running the tool.
    if anchor_table.EXCLUDED_ANCHORS:
        lines += ["## Coverage deliberately not checked", ""]
        lines += [
            f"- `{name}` — {reason}"
            for name, reason in sorted(anchor_table.EXCLUDED_ANCHORS.items())
        ] + [""]

    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))


def _tree_sitter_version() -> str:
    import importlib.metadata as metadata

    try:
        return metadata.version("tree-sitter")
    except metadata.PackageNotFoundError:
        return "unknown"


def _add_common_args(subparser: argparse.ArgumentParser) -> None:
    """--repo-root/--manifest/--baseline, shared by every subcommand.

    These live on each SUBPARSER rather than the top-level parser. Defined
    only on the parent (as originally written), argparse accepts them BEFORE
    the subcommand token (`qc --repo-root X run`) but rejects them after it
    (`qc run --repo-root X`) outright: `unrecognized arguments: --repo-root
    X`, exit 2. Every real caller -- including this module's own
    test_run_exits_corpus_broken_when_manifest_drifted -- uses the second
    form, so the parent-only definition doesn't work.

    Defining them on BOTH the parent and every subparser (e.g. via
    `parents=`) doesn't fix it either, just trades one failure for a quieter
    one: SubParsersAction parses the subcommand's tail into a fresh
    namespace and copies every one of its dests onto the parent namespace --
    including ones the user never touched, at the subparser's own default --
    which silently overwrites a same-named option already parsed before the
    subcommand token. `qc --repo-root X run` would then parse but discard X.

    Defining them ONLY on each subparser, as done here, avoids both: nothing
    on the parent to silently win. The tradeoff is that these options are now
    only accepted AFTER the subcommand (`qc run --repo-root X`), never
    before (`qc --repo-root X run` goes back to being rejected) -- but that
    is the form every real caller already uses, so it costs nothing in
    practice.
    """
    subparser.add_argument("--repo-root", default=str(loader.REPO_ROOT))
    subparser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    subparser.add_argument("--baseline", default=str(DEFAULT_BASELINE))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qc")
    sub = parser.add_subparsers(dest="command", required=True)

    select = sub.add_parser("select")
    _add_common_args(select)
    select.add_argument("--corpus", nargs="+", default=["BC.History"])
    select.set_defaults(func=cmd_select)

    run = sub.add_parser("run")
    _add_common_args(run)
    run.add_argument("--all", action="store_true")
    run.add_argument("--full-query-scan", action="store_true", dest="full_query_scan")
    run.add_argument("--full-corpus", action="store_true", dest="full_corpus")
    run.set_defaults(func=cmd_run)

    accept = sub.add_parser("accept")
    _add_common_args(accept)
    accept.set_defaults(func=cmd_accept)

    args = parser.parse_args(argv)
    if not hasattr(args, "all"):
        args.all = False
    if not hasattr(args, "full_query_scan"):
        args.full_query_scan = False
    if not hasattr(args, "full_corpus"):
        args.full_corpus = False
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
