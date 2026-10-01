"""test/corpus cases as oracle INPUT (their expected trees play no part in the verdict).

A line-based reader, deliberately not count_corpus_cases' regex: two readers
of the corpus format must agree (spec section 4), which is only a check if
they are different implementations.

Source-byte extraction mirrors tree-sitter's own corpus reader (vendored at
`.cache/tree-sitter-0.25.10/cli/src/test.rs`; header/divider regexes around
line 28-48, the slicing logic around line 883-911):

  * The divider for a case is the LONGEST `-{3,}` line between the end of its
    header and the start of the next header (or EOF), ties won by the LAST
    one -- not the first `-{3,}` line encountered. A short `----` inside a
    block comment must not pre-empt the real divider below it.
  * `source` is the RAW byte slice from the end of the header's closing `===`
    line to the start of that divider line, then exactly one trailing byte is
    popped unconditionally (mirrors Rust's `Vec::pop`, which does not check
    it is actually `\n`), and one more trailing `\r` is popped if present
    (`#[cfg(target_os = "windows")]` in test.rs; this project's platform).
    No blank-line assumption, no re-appended `\n` -- a case with no blank
    line before its divider has NO trailing newline in `source`.
  * A `===`/`---` marker line tolerates no trailing content at all, not even
    trailing whitespace. Real tree-sitter ties this to a file-wide "first
    suffix" convention (test.rs's `first_suffix`); every header/divider line
    in this corpus uses none (verified: zero lines here carry anything after
    the marker run), so requiring a bare marker line reproduces the real
    behaviour without modelling that convention. Verified against the
    installed tree-sitter 0.27.0 CLI: a `---` line with trailing spaces is
    REJECTED (its case silently dropped), the same as a missing divider.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_EQ = re.compile(rb"^={3,}\r?$")
_DASH = re.compile(rb"^-{3,}\r?$")


def _esc(name: str) -> str:
    """`%`, `#`, `|` and tab would collide with the id, discrepancy-id and TSV separators."""
    return name.replace("%", "%25").replace("#", "%23").replace("|", "%7C").replace("\t", "%09")


@dataclass(frozen=True)
class Case:
    file: str
    name: str
    ordinal: int  # among the cases of THIS name in this file: inserting a case shifts no other id
    source: bytes
    offset: int  # byte offset in the file where `source` (pre-strip) begins

    @property
    def id(self):
        return f"{self.file}#{_esc(self.name)}#{self.ordinal}"


def _is_skip_line(line: bytes) -> bool:
    """Mirrors test.rs: trim the line, split on the first '(', exact-match ':skip'."""
    return line.strip().split(b"(", 1)[0] == b":skip"


def _line_offsets(data: bytes):
    lines = data.split(b"\n")
    offsets = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1
    return lines, offsets


def _headers(lines):
    """[(name, skip, open_idx, close_idx), ...] in file order.

    open_idx/close_idx are line indices of the opening and closing '=' lines.
    A blank line inside the name block aborts that header attempt entirely
    (mechanism 1); scanning resumes one line past the failed opener, exactly
    like a regex engine retrying at the next position.
    """
    out = []
    i, n = 0, len(lines)
    while i < n:
        if _EQ.match(lines[i]) and i + 1 < n and lines[i + 1].strip() and not _EQ.match(lines[i + 1]):
            open_idx = i
            j = i + 1
            name_lines = []
            broken = False
            while j < n and not _EQ.match(lines[j]):
                if not lines[j].strip():
                    broken = True
                    break
                name_lines.append(lines[j])
                j += 1
            if broken or j >= n:
                i += 1
                continue
            skip = any(_is_skip_line(l) for l in name_lines)
            name = name_lines[0].strip().decode("utf8", "replace")
            out.append((name, skip, open_idx, j))
            i = j + 1
        else:
            i += 1
    return out


def _best_divider(lines, lo, hi):
    """Index of the longest '-{3,}' line in lines[lo:hi]; ties keep the LAST
    one (mirrors Rust's Iterator::max_by_key). None if no candidate."""
    best = None
    for idx in range(lo, hi):
        if _DASH.match(lines[idx]):
            length = len(lines[idx].rstrip(b"\r"))
            if best is None or length >= best[0]:
                best = (length, idx)
    return best[1] if best else None


def _strip_trailing_newline(raw: bytes) -> bytes:
    if raw:
        raw = raw[:-1]          # unconditional pop, mirrors Rust's Vec::pop()
    if raw[-1:] == b"\r":
        raw = raw[:-1]          # Windows-only in tree-sitter; this project's platform
    return raw


def extract(root: Path) -> list:
    out = []
    for path in sorted(root.rglob("*.txt")):
        rel = str(path.relative_to(root)).replace("\\", "/")
        data = path.read_bytes()
        lines, offsets = _line_offsets(data)
        headers = _headers(lines)
        seen = {}
        for k, (name, skip, open_idx, close_idx) in enumerate(headers):
            body_lo = close_idx + 1
            body_hi = headers[k + 1][2] if k + 1 < len(headers) else len(lines)
            div_idx = _best_divider(lines, body_lo, body_hi)
            if div_idx is None or skip:
                continue
            start_off = offsets[body_lo] if body_lo < len(offsets) else len(data)
            end_off = offsets[div_idx]
            source = _strip_trailing_newline(data[start_off:end_off])
            out.append(Case(rel, name, seen.get(name, 0), source, start_off))
            seen[name] = seen.get(name, 0) + 1
    return out


# The roadmap's sub-project ids (docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md):
# a debt entry's owner is the one that removes it. A production entry also names the
# milestone it goes by: a sub-project id, or M3/M4/M5 (the oracle milestones C1/C2/C3 run).
ROADMAP = frozenset({*(f"A{i}" for i in range(1, 8)), *(f"B{i}" for i in range(1, 10)),
                     "C1", "C2", "C3", "D1", "D2", "E1", "E2", "E3", "F1"})
MILESTONES = ROADMAP | {"M3", "M4", "M5"}

# kind -> (category pattern, categories that claim alc rejects the input, the probe's
# line naming the input it stands for). The two files share everything else.
_KINDS = {
    "fixture": (re.compile(r"(?P<cat>negative|invalid-config|debt\((?P<owner>[A-Za-z0-9]+)\)):"),
                ("negative", "invalid-config"), "// Fixture "),
    "production": (re.compile(r"(?P<cat>invalid-source|other|"
                              r"debt\((?P<owner>[A-Za-z0-9]+), (?P<milestone>[A-Za-z0-9]+)\)):"),
                   ("invalid-source",), "// Source "),
}
# A production `lowering:` prefix names at least the refusal kind and the node type, and
# for an unsupported-type or one-reading refusal of a special node also its host (the
# oracle records it as `: host <parent>:<slot>`): a shorter prefix would absorb a
# different refusal, or the same one re-parented by a grammar change.
_PRODUCTION_LOWERING = re.compile(r"lowering:(?P<k>[a-z-]+):(?P=k) at (?P<t>\w+)(?P<tail>: .+)?$")
# The host an unsupported-type or one-reading entry pins: `<parent>:<slot>`, the slot required.
# A slotless `: host if_statement` would match every slot of that parent (N2).
_HOST_TAIL = re.compile(r": host \w+:(?:<children>|\w+)(?:, |$)")
_EVIDENCE = re.compile(r"evidence: (?:alc_probe (?P<case>\S+\.al)|probe_alc (?P<raw>\w+)|alc manual,)")


def category(reason: str) -> str:
    """`negative`, `invalid-source`, `other`, `debt(C1, M3)`: the reason up to its first `:`."""
    return reason.split(":", 1)[0]


def load_classes(path: Path, kind: str = "fixture") -> dict:
    """Classifications of cannot-validate records (the headers of fixture-classes.tsv and
    production-classes.tsv state the rules). `expected` is `cannot-validate:<reason
    prefix>`: nothing else can be classified (there is no baseline), and a bare status
    would excuse any failure of that status. Every reason starts with a category of its
    `kind`; a debt owner (and a production milestone) must be a known roadmap id; the
    categories that claim alc rejects the input need compiler evidence, checked by
    `_check_evidence`. The runner reports an entry that matches no record as stale."""
    pattern, rejecting, marker = _KINDS[kind]
    classes = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        case_id, config, expected, reason = line.split("\t")
        status, _, prefix = expected.partition(":")
        if status != "cannot-validate" or not prefix:
            raise ValueError(f"classification must be cannot-validate:<reason>: {case_id} {config} {expected}")
        if not reason.strip():
            raise ValueError(f"classification without a reason: {case_id} {config}")
        m = pattern.match(reason)
        if not m or not reason[m.end():].strip():
            raise ValueError(f"reason must start with one of {pattern.pattern} and say why: {case_id} {config}")
        if m.group("owner") and m.group("owner") not in ROADMAP:
            raise ValueError(f"debt owner {m.group('owner')} is not a roadmap sub-project: {case_id} {config}")
        if kind == "production" and m.group("milestone") and m.group("milestone") not in MILESTONES:
            raise ValueError(f"debt milestone {m.group('milestone')} is not a roadmap milestone: {case_id} {config}")
        if kind == "production" and prefix.startswith("lowering"):
            lm = _PRODUCTION_LOWERING.match(prefix)
            if not lm or (lm.group("k") in ("unsupported-type", "one-reading") and lm.group("t").startswith("preproc")
                          and not _HOST_TAIL.match(lm.group("tail") or "")):
                raise ValueError(f"a production lowering prefix must be `lowering:<kind>:<kind> at <type>`, "
                                 f"plus `: host <parent>:<slot>` for unsupported-type and one-reading: "
                                 f"{case_id} {config} {prefix}")
        if m.group("cat") in rejecting:
            _check_evidence(path, case_id, config, reason, marker)
        if (case_id, config) in classes:
            raise ValueError(f"duplicate classification: {case_id} {config}")
        classes[(case_id, config)] = (expected, reason)
    return classes


def _check_evidence(path: Path, case_id: str, config: str, reason: str, marker: str) -> None:
    """A claim that alc rejects input must name its evidence, and an alc_probe case must
    expect a reject for every configuration the entry covers: all of them for `*`."""
    m = _EVIDENCE.search(reason)
    if not m:
        raise ValueError(f"no `evidence: alc_probe <case>`, `evidence: probe_alc <name>` or "
                         f"`evidence: alc manual`: {case_id} {config}")
    if m.group("raw") is not None:
        # A raw compile recorded in tools/config_oracle/probe_alc.py, which `--check` keeps
        # honest. It is ONE compile, so it cannot stand for every configuration of a `*`.
        from tools.config_oracle.probe_alc import PROBES   # lazy, like the alc_probe import
        expected = {name: accept for name, _, _, accept in PROBES}
        if m.group("raw") not in expected:
            raise ValueError(f"evidence probe_alc {m.group('raw')} is not in probe_alc.PROBES: {case_id} {config}")
        if expected[m.group("raw")]:
            raise ValueError(f"evidence probe_alc {m.group('raw')} expects an ACCEPT: {case_id} {config}")
        if config == "*":
            raise ValueError(f"a `*` entry needs alc_probe evidence for every configuration, "
                             f"not one raw compile: {case_id}")
        return
    if m.group("case") is None:
        if config == "*":
            raise ValueError(f"a `*` entry needs alc_probe evidence for every configuration, "
                             f"not a manual note: {case_id}")
        return
    from tools.alc_probe import matrix      # lazy: only the loader needs the probe's case parser
    probe = Path(__file__).resolve().parents[2] / m.group("case")   # repo-relative
    if not probe.is_file():
        raise ValueError(f"evidence case does not exist: {m.group('case')} ({case_id} {config})")
    text = probe.read_text(encoding="utf-8")
    # The probe must say which input it is (`// Fixture <case id>`, `// Source <label>:<path>`):
    # a path alone lets an unrelated probe that happens to share the symbol names stand in.
    named = [l[len(marker):].strip() for l in text.splitlines() if l.startswith(marker)]
    if named != [case_id]:
        raise ValueError(f"{m.group('case')} is the probe for {named or 'no input'}, not {case_id}")
    case = matrix.parse_case(probe, probe.name, text, check=False)
    if config == "*":
        envs = case.envs
    else:
        pairs = dict(kv.split("=") for kv in config.split(",")) if config != "-" else {}
        if sorted(pairs) != sorted(case.symbols):
            raise ValueError(f"config {config} does not name the symbols of {m.group('case')} "
                             f"({list(case.symbols)}): {case_id}")
        envs = [frozenset(k for k, v in pairs.items() if v == "1")]
    for env in envs:
        exp = case.expected(env)
        if exp is None or exp.kind != "REJECT":
            raise ValueError(f"{m.group('case')} does not expect a reject for "
                             f"{sorted(env) or 'no symbols'}, which {case_id} {config} claims is rejected")
