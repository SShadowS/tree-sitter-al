"""Evidence runner (spec 7.1, 8, 10): every audit cell measured with alc (split, flat, typed
control), the parser and the config oracle, written as canonical evidence.

SYNTAX_CODES is the set that makes an alc rejection a SYNTAX rejection (spec 7.1):
  AL0104 syntax error, 'x' expected        AL0107 identifier expected
  AL0111 semicolon expected                AL0224 expression expected
  AL0125 unexpected token / invalid statement
A flat rejection carrying any of them is `syntax`, any other rejection is `semantic`, provided the
typed control (the cell's `plain` template resolved in the same configuration, compiled flat)
ACCEPTs. A control that REJECTs means the template itself is invalid there: GeneratorBug.
Seeds have no template, so no control (`control: "none"`): their class comes from the codes alone.

Tiered alc (controller ruling): parser and oracle run on every cell; alc runs on a cell when it is
a seed, its parser/oracle outcome is not clean+pass, its intended vector excludes an assignment,
or it is its (role, family, placement) class's representative (lexicographically first id).
Every other cell is `alc: "class-sampled"` and names its representative.

alc work is deduplicated by exact (source, symbols) and cached on disk under .cache/b7_audit/alc,
keyed with the runtime and the compiler identity, so a different compiler never reads the cache.
"""
import hashlib
import itertools
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import tools.config_oracle.runner as oracle_runner
from tools.alc_probe import core
from tools.b7_audit import placements, registry, seeds
from tools.config_oracle import directives

SYNTAX_CODES = frozenset({"AL0104", "AL0107", "AL0111", "AL0224", "AL0125"})
HERE = Path(__file__).parent
REPO = HERE.parent.parent
EVIDENCE = HERE / "evidence.jsonl"
CACHE = REPO / ".cache" / "b7_audit" / "alc"
ORACLE_ITEMS = REPO / ".cache" / "b7_audit" / "oracle-items.jsonl"   # verbatim items, never committed
# A change to the project template (app.json, file layout, classification) invalidates the cache.
CORE_SHA256 = hashlib.sha256(Path(core.__file__).read_bytes()).hexdigest()


class GeneratorBug(Exception):
    pass


class OracleCrash(Exception):
    pass


class ProbeBroken(Exception):
    pass


class DiscoverMismatch(Exception):
    """The oracle's configurations (discover's free symbols) do not map one-to-one onto the
    cell's assignments."""


def _differ(split, flat):
    # The split/flat MISMATCH rule of tools.alc_probe.matrix._differ (copied: that one is private).
    return split.kind != flat.kind or (split.kind == core.REJECT and split.source_codes != flat.source_codes)


# --- alc ------------------------------------------------------------------------------------------
def _vd(v):
    return {"verdict": v.kind, "codes": list(v.source_codes)}


def identity_dict(identity):
    """The compiler identity without machine paths (what the header records and the cache keys on)."""
    return {"version": identity.version, "launcher_sha256": identity.launcher_sha256,
            "code_analysis": [{"name": Path(p).name, "sha256": h}
                              for p, h in sorted(identity.code_analysis, key=lambda t: (Path(t[0]).name, t[1]))]}


class Alc:
    """Compiles through core.compile_project; in-memory dedup plus an optional disk cache."""

    def __init__(self, identity, *, runtime=core.DEFAULT_RUNTIME, cache_dir=None, runner=core.default_runner,
                 workdir=None):
        self.identity, self.runtime, self.runner = identity, runtime, runner
        self.al = identity.path or "al"
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._owned = workdir is None
        self.workdir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="b7-alc-"))
        self._id = json.dumps(identity_dict(identity), sort_keys=True)
        self._mem, self._lock, self._n = {}, threading.Lock(), itertools.count()
        self.stats = {"requested": 0, "disk_hits": 0, "compiled": 0}

    def key(self, text, symbols):
        blob = json.dumps([text, sorted(symbols), self.runtime, self._id, CORE_SHA256])
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _path(self, k):
        return self.cache_dir / k[:2] / f"{k}.json"

    def _load(self, k):
        if self.cache_dir and self._path(k).is_file():
            d = json.loads(self._path(k).read_text(encoding="utf-8"))
            return core.Verdict(d["kind"], tuple(d["codes"]), tuple(d["source_codes"]), d["detail"])
        return None

    def _compile(self, k, text, symbols):
        v = self._load(k)
        if v is not None:
            with self._lock:
                self.stats["disk_hits"] += 1
            return v
        with self._lock:
            n = next(self._n)
            self.stats["compiled"] += 1
        v = self._project(f"p{n:06d}", text, sorted(symbols))
        if self.cache_dir and v.kind != core.BROKEN:     # a broken project is never a cached verdict
            p = self._path(k)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(f".{threading.get_ident()}.tmp")
            tmp.write_text(json.dumps({"kind": v.kind, "codes": list(v.codes), "source_codes": list(v.source_codes),
                                       "detail": v.detail}), encoding="utf-8", newline="\n")
            os.replace(tmp, p)
        return v

    def _project(self, name, text, symbols=()):
        """One compile in its own project directory, removed once the verdict is read."""
        d = self.workdir / name
        try:
            return core.compile_project(d, text, symbols, runtime=self.runtime, al=self.al, runner=self.runner)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def close(self):
        if self._owned:
            shutil.rmtree(self.workdir, ignore_errors=True)

    def prefetch(self, jobs_list, jobs=6):
        """Compile every distinct (text, symbols) not yet known, `jobs` at a time."""
        todo = {}
        for text, symbols in jobs_list:
            self.stats["requested"] += 1
            k = self.key(text, symbols)
            if k not in self._mem:
                todo.setdefault(k, (text, symbols))
        with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
            for k, v in zip(todo, pool.map(lambda kv: self._compile(kv[0], *kv[1]), todo.items())):
                self._mem[k] = v

    def verdict(self, text, symbols=()):
        k = self.key(text, symbols)
        if k not in self._mem:
            self.prefetch([(text, symbols)], jobs=1)
        return self._mem[k]

    def check_controls(self):
        """Controls first: a valid program must ACCEPT and garbage must REJECT, uncached."""
        for want, src in ((core.ACCEPT, core.VALID_CONTROL), (core.REJECT, core.GARBAGE_CONTROL)):
            v = self._project(f"control-{want}", src)
            if v.kind != want:
                raise ProbeBroken(f"control expected {want}, got {v.kind} {v.codes} {v.detail}")


# --- parser and oracle ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Observation:
    has_error: bool
    error_in_hole: bool
    oracle: dict          # {assignment frozenset: {"status", "items"}}

    @property
    def clean(self):
        return not self.has_error and all(o["status"] == "pass" for o in self.oracle.values())


def _errors(root):
    stack = [root]
    while stack:
        n = stack.pop()
        if n.is_error or n.is_missing:
            yield n
        if n.has_error:
            stack.extend(n.children)


def _in_hole(n, hole):
    a, b = hole
    return n.start_byte <= b and n.end_byte >= a if n.start_byte == n.end_byte else \
        n.start_byte < b and n.end_byte > a


def _env_of(cid):
    if cid == "-":
        return {}
    return {kv.split("=")[0]: kv.split("=")[1] == "1" for kv in cid.split(",")}


def observe(cell, parser):
    src = cell.source.encode("utf-8")
    root = parser.parse(src).root_node
    errs = list(_errors(root)) if root.has_error else []
    records = oracle_runner.check_input(parser, cell.id, src)
    for r in records:
        if any(str(i).startswith("internal-error") for i in r.items):
            raise OracleCrash(f"{cell.id} {r.config}: {r.items[0].splitlines()[0]}")
    by_env = [(_env_of(r.config), r) for r in records]
    oracle = {}
    for env in placements.assignments(cell.symbols):
        hits = [r for e, r in by_env if all((s in env) == want for s, want in e.items())]
        if len(hits) != 1:
            raise DiscoverMismatch(f"{cell.id}: {len(hits)} oracle records for {sorted(env)} "
                               f"({[r.config for r in records]})")
        oracle[env] = {"status": hits[0].status, "items": list(hits[0].items)}
    return Observation(root.has_error, any(_in_hole(n, cell.hole) for n in errs), oracle)


def reduce_oracle(o):
    """The committed form of an oracle record: its status and the sorted, deduplicated item prefixes
    before the first `@offset` (offsets churn with every template edit; the verbatim items go to
    ORACLE_ITEMS, uncommitted). Idempotent."""
    if "reasons" in o:
        return o
    return {"status": o["status"], "reasons": sorted({re.split(r"@\d", i, maxsplit=1)[0] for i in o["items"]})}


# --- measuring one cell ---------------------------------------------------------------------------
def _flat(text, env):
    return directives.resolve(text.encode("utf-8"), env).masked.decode("utf-8")


def alc_jobs(cell):
    """Every (text, symbols) compile a measured cell needs."""
    out = []
    for env in placements.assignments(cell.symbols):
        out += [(cell.source, tuple(sorted(env))), (_flat(cell.source, env), ())]
        if cell.plain is not None:
            out.append((_flat(cell.plain, env), ()))
    return out


def measure(cell, parser, alc, sampled_by=None, observed=None):
    """-> one record per assignment of cell.symbols (sorted by config)."""
    obs = observed or observe(cell, parser)
    seed = cell.plain is None
    free = tuple(sorted(cell.symbols))
    sha = hashlib.sha256(cell.source.encode("utf-8")).hexdigest()
    recs = []
    for env in placements.assignments(cell.symbols):
        rec = {"cell": cell.id, "key": cell.key, "host": cell.host, "placement": cell.placement,
               "config": directives.config_id(env, free), "source_sha256": sha,
               "intended_valid": env in cell.intended_valid, "control": "none" if seed else "typed",
               "parser_has_error": obs.has_error, "error_in_hole": obs.error_in_hole,
               "oracle": reduce_oracle(obs.oracle[env]),
               "alc": "class-sampled" if sampled_by else "measured", "alc_split": None, "alc_flat": None,
               "alc_control": None, "reject_class": None}
        if sampled_by:
            rec["alc_representative"] = sampled_by
            recs.append(rec)
            continue
        split, flat = alc.verdict(cell.source, tuple(sorted(env))), alc.verdict(_flat(cell.source, env))
        for kind, v in (("split", split), ("flat", flat)):
            if v.kind == core.BROKEN:
                raise ProbeBroken(f"{cell.id} {rec['config']} {kind}: BROKEN {v.codes} {v.detail}")
        if _differ(split, flat):
            raise ProbeBroken(f"{cell.id} {rec['config']}: split/flat MISMATCH "
                              f"{split.kind}{split.source_codes} vs {flat.kind}{flat.source_codes}")
        rec["alc_split"], rec["alc_flat"] = _vd(split), _vd(flat)
        if not seed:
            ctrl = alc.verdict(_flat(cell.plain, env))
            if ctrl.kind != core.ACCEPT:
                raise GeneratorBug(f"{cell.id} {rec['config']}: typed control {ctrl.kind} {ctrl.source_codes}")
            rec["alc_control"] = _vd(ctrl)
        if flat.kind == core.REJECT:
            rec["reject_class"] = "syntax" if set(flat.source_codes) & SYNTAX_CODES else "semantic"
        recs.append(rec)
    if not seed and not cell.intended_valid and any(r["alc_flat"]["verdict"] == core.ACCEPT for r in recs):
        raise GeneratorBug(f"{cell.id}: alc accepts a configuration of an all-invalid vector")
    return recs


# --- tiers ----------------------------------------------------------------------------------------
@dataclass(frozen=True)
class TierInfo:
    id: str
    cls: tuple            # (role, family, placement)
    clean: bool           # parser clean and oracle pass in every configuration
    all_valid: bool       # the intended vector holds every assignment
    seed: bool


def representatives(pairs):
    """{class: lexicographically first cell id} over (id, class) pairs."""
    reps = {}
    for cid, cls in pairs:
        if cls not in reps or cid < reps[cls]:
            reps[cls] = cid
    return reps


def tiers(infos, reps):
    """-> {id: None (alc measures it) | representative id (class-sampled)}."""
    return {i.id: None if (i.seed or not i.clean or not i.all_valid or reps[i.cls] == i.id) else reps[i.cls]
            for i in infos}


# --- universe -------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Entry:
    cell: placements.Cell
    role: str
    family: str

    @property
    def cls(self):
        return (self.role, self.family, self.cell.placement)


def universe(registry_path=HERE / "registry.tsv", seed_root=seeds.SEEDS):
    out = [Entry(c, r.role, r.family) for r in registry.load(registry_path) for c in placements.cells_for(r)]
    out += [Entry(c, "seed", "seed") for c in seeds.load(seed_root)]
    ids = [e.cell.id for e in out]
    if len(set(ids)) != len(ids):
        raise GeneratorBug("duplicate cell ids in the universe")
    return out


def select(entries, only):
    """The --only slice (family, key or placement, exact) plus the representative of each of its
    classes, so a class-sampled cell's representative is always measured in the same run."""
    if not only:
        return list(entries)
    picked = [e for e in entries if only in (e.family, e.cell.key, e.cell.placement)]
    reps = representatives((e.cell.id, e.cls) for e in entries)
    want = {e.cell.id for e in picked} | {reps[e.cls] for e in picked}
    return [e for e in entries if e.cell.id in want]


# --- output ---------------------------------------------------------------------------------------
def write(records, header, path):
    lines = [json.dumps({"header": header}, sort_keys=True, ensure_ascii=False)]
    lines += [json.dumps(r, sort_keys=True, ensure_ascii=False)
              for r in sorted(records, key=lambda r: (r["cell"], r["config"]))]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def read(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return json.loads(lines[0])["header"], [json.loads(l) for l in lines[1:] if l]


def diff_records(old, new, cells):
    """Differences between committed and fresh records, restricted to `cells`."""
    def norm(r):
        return {**r, "oracle": reduce_oracle(r["oracle"])} if "oracle" in r else r
    o = {(r["cell"], r["config"]): norm(r) for r in old if r["cell"] in cells}
    n = {(r["cell"], r["config"]): norm(r) for r in new if r["cell"] in cells}
    out = []
    for k in sorted(set(o) | set(n)):
        if k not in n:
            out.append(f"missing {k[0]} {k[1]}")
        elif k not in o:
            out.append(f"new {k[0]} {k[1]}")
        else:
            out += [f"changed {k[0]} {k[1]} {f}: {o[k].get(f)} -> {n[k].get(f)}"
                    for f in sorted(set(o[k]) | set(n[k])) if o[k].get(f) != n[k].get(f)]
    return out


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _git_head(root):
    try:
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel", "HEAD"],
                             capture_output=True, text=True)
    except OSError:
        return None
    lines = top.stdout.split()
    if top.returncode or len(lines) != 2 or Path(lines[0]).resolve() != Path(root).resolve():
        return None             # not a repository of its own (BC.History sits inside this one)
    return lines[1]


def corpus_roots():
    return {name: (REPO / p if ":" not in p else Path(p)) for name, p in seeds.ROOTS.items()}


def corpus_entry(root):
    """{present, head} for a root that is its own git toplevel; otherwise {present, head: None,
    manifest: {al_files, sha256 of the sorted relative paths and sizes}}."""
    root = Path(root)
    if not root.is_dir():
        return {"present": False, "head": None}
    head = _git_head(root)
    if head:
        return {"present": True, "head": head}
    files = sorted((p.relative_to(root).as_posix(), p.stat().st_size) for p in root.rglob("*.al") if p.is_file())
    blob = "".join(f"{f}\t{n}\n" for f, n in files).encode("utf-8")
    return {"present": True, "head": None, "manifest": {"al_files": len(files), "sha256": hashlib.sha256(blob).hexdigest()}}


def corpus_warnings(old, new):
    return [f"WARNING: corpus {n} changed since the evidence was taken"
            for n in sorted(set(old) | set(new)) if old.get(n) != new.get(n)]


def header(identity, runtime, corpora=None):
    oracle = hashlib.sha256()
    pkg = REPO / "tools" / "config_oracle"
    for p in sorted(pkg.rglob("*.py")):
        if "tests" not in p.relative_to(pkg).parts:
            oracle.update(p.relative_to(pkg).as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    if corpora is None:
        corpora = {n: corpus_entry(r) for n, r in corpus_roots().items()}
    return {"alc": identity_dict(identity), "runtime": runtime, "corpora": corpora,
            "production_shapes": json.loads(seeds.SHAPES_JSON.read_text(encoding="utf-8")),
            "production_shapes_sha256": _sha(seeds.SHAPES_JSON),
            "parser": {f"src/{f}": _sha(REPO / "src" / f) for f in ("parser.c", "scanner.c")},
            "oracle_sha256": oracle.hexdigest()}


# --- run ------------------------------------------------------------------------------------------
def run(only=None, jobs=6, check=False, accept_tool=False, out=EVIDENCE, al="al", runner=core.default_runner,
        cache_dir=CACHE, log=print):
    t0 = time.time()
    identity = core.compiler_identity(al, runner)
    if identity.error:
        log(f"cannot run: {identity.error}")
        return 2
    committed = read(out) if Path(out).is_file() else None
    if check:
        missing = [n for n, r in corpus_roots().items() if not r.is_dir()]
        if missing or committed is None:
            log(f"cannot run: --check needs every corpus root and {out}; missing {missing or out}")
            return 2
    if committed and committed[0]["alc"] != identity_dict(identity):
        if only and not check:
            log("cannot run: --only would merge records of another alc identity under a new header; "
                "re-run the whole matrix instead")
            return 2
        if check and not accept_tool:
            log("cannot run: alc identity differs from the committed evidence (pass --accept-tool)")
            return 2
    every = universe()
    entries = select(every, only)
    if not entries:
        log(f"cannot run: --only {only!r} matches no cell")
        return 2
    from tools.query_coverage import loader
    parser = loader.make_parser(loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
    obs = {e.cell.id: observe(e.cell, parser) for e in entries}
    ORACLE_ITEMS.parent.mkdir(parents=True, exist_ok=True)
    with open(ORACLE_ITEMS, "w", encoding="utf-8", newline="\n") as f:     # last run's verbatim items
        for cid, o in sorted(obs.items()):
            for env, rec in sorted(o.oracle.items(), key=lambda kv: sorted(kv[0])):
                f.write(json.dumps({"cell": cid, "env": sorted(env), **rec}, sort_keys=True) + "\n")
    t1 = time.time()
    allreps = representatives((e.cell.id, e.cls) for e in every)
    tier = tiers([TierInfo(e.cell.id, e.cls, obs[e.cell.id].clean,
                           len(e.cell.intended_valid) == len(placements.assignments(e.cell.symbols)),
                           e.role == "seed") for e in entries], allreps)
    alc = Alc(identity, cache_dir=cache_dir, runner=runner)
    try:
        alc.check_controls()
        measured = [e for e in entries if tier[e.cell.id] is None]
        alc.prefetch([j for e in measured for j in alc_jobs(e.cell)], jobs=jobs)
        t2 = time.time()
        records = [r for e in entries for r in measure(e.cell, parser, alc, tier[e.cell.id], obs[e.cell.id])]
    finally:
        alc.close()
    hdr = header(identity, alc.runtime)
    s = alc.stats
    log(f"{len(entries)} cells ({len(measured)} alc-measured, {len(entries) - len(measured)} class-sampled), "
        f"{len(records)} records; compiles requested {s['requested']}, distinct {s['disk_hits'] + s['compiled']}, "
        f"cache hits {s['disk_hits']}, compiled {s['compiled']}; parser+oracle {t1 - t0:.1f}s, "
        f"alc {t2 - t1:.1f}s, total {time.time() - t0:.1f}s")
    cells = {e.cell.id for e in entries}
    if check:
        for w in corpus_warnings(committed[0].get("corpora", {}), hdr["corpora"]):
            log(w)
        diffs = diff_records(committed[1], records, cells)
        for d in diffs:
            log(d)
        log(f"{len(diffs)} differences")
        return 1 if diffs else 0
    if only and committed:
        records += [r for r in committed[1] if r["cell"] not in cells]
    write(records, hdr, out)
    log(f"wrote {Path(out).relative_to(REPO).as_posix() if Path(out).is_relative_to(REPO) else out}")
    return 0
