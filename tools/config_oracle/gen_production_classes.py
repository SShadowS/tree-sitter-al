"""Generate production-classes.tsv entries from a full-tier findings.jsonl (A4).

Every non-pass record becomes one exact entry (its own configuration, never `*`). The
host of a lowering refusal is read from the multi-configuration tree: the node of the
refused type that starts at the record's offset, and its parent (with the field name).
Anything this script does not recognise is a hard error, never a default.

    cp tools/config_oracle/production-classes.tsv OUT.tsv   # its comment header is kept
    python -m tools.config_oracle.gen_production_classes <report>/findings.jsonl OUT.tsv

Regenerate after a corpus HEAD or working-tree change (the run then exits 1 on the
recorded identity), then diff OUT.tsv against production-classes.tsv record by record,
never by counts, before replacing it."""
import collections
import json
import re
import sys
from pathlib import Path

from tools.query_coverage import loader
from tools.config_oracle import __main__ as cli
from tools.config_oracle import runner

findings, out_path = Path(sys.argv[1]), Path(sys.argv[2])
parser = loader.make_parser(loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
ROOTS = {k: str(v) for k, v in cli.CORPORA.items() if k != "selftest"}

PROBES = {
    "bcapps-29.0:src/Apps/IN/INFADepreciation/app/src/table/FixedAssetShift.Table.al":
        ("fixed-asset-shift.al", "CLEANSCHEMA26"),
    "bcapps-29.0:src/Apps/W1/SalesOrderAgent/app/src/Setup/SOASetup.Table.al":
        ("soa-setup.al", "CLEANSCHEMA28"),
    "bcapps-29.0:src/Layers/FR/BaseApp/Bank/BankAccount/BankAccount.Table.al":
        ("bank-account.al", "CLEANSCHEMA31"),
}
READING = {  # contracts.py `reading=` of each one-reading type
    "preproc_split_open_statement": "arm:not-else-led",
    "preproc_split_container_reopen": "arm:if",
    "preproc_split_block_end_in_else": "arm:else",
    "preproc_split_else_begin_over_endif": "arm:inactive",
}


def ident(raw):
    """`<label>:<posix relpath>` (the A4 input id) -> (label, root, relpath)."""
    label, sep, rel = raw.partition(":")
    if not sep or label not in ROOTS:
        raise SystemExit(f"no root for {raw}")
    return label, ROOTS[label], rel


_trees = {}


def host(root, rel, typ, off):
    key = (root, rel)
    if key not in _trees:
        _trees[key] = parser.parse((Path(root) / rel).read_bytes())
    stack = [_trees[key].root_node]
    while stack:
        n = stack.pop()
        if n.type == typ and n.start_byte == off:
            par = n.parent
            i = [par.child(k).id for k in range(par.child_count)].index(n.id)
            f = par.field_name_for_child(i)
            return f"{par.type}:{f}" if f else f"{par.type}:<children>"
        stack.extend(n.children)
    raise SystemExit(f"no {typ} at {off} in {rel}")


lines, counts = [], collections.Counter()
n_cfg, n_bad = collections.Counter(), collections.Counter()
for line in findings.read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    n_cfg[r["input_id"]] += 1
    n_bad[r["input_id"]] += r["status"] != "pass"
for line in findings.read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    if r["status"] == "pass":
        continue
    if r["status"] != "cannot-validate":
        raise SystemExit(f"STOP: {r['status']} {r['input_id']} {r['config']}")
    label, root, rel = ident(r["input_id"])
    cid = f"{label}:{rel}"
    item = r["items"][0]
    key = runner.reason_key(item)
    m = re.match(r"lowering:(unsupported-type|one-reading|arm-content):\1 at (\w+)@(\d+)", item)
    if m:
        kind, typ, off = m.group(1), m.group(2), int(m.group(3))
        h = host(root, rel, typ, off)
        if kind != "arm-content":
            # The oracle records the host now (A4 fix 1, I1): it must be the tree's.
            hm = re.search(r": host (\S+?:\S+?)(?:,|$)", key)
            assert hm and hm.group(1) == h, (key, h)
        if kind == "unsupported-type":
            reason = (f"debt(C1, M3): no lowering handler is registered for {typ}; "
                      f"registry `unsupported`, milestone 3")
            if typ == "preproc_split_open_statement":
                assert key.endswith(", complete-prefix arm (milestone 3)"), key
                reason = (f"debt(C1, M3): {typ} with a complete-prefix arm chosen: "
                          f"open_statement_reading lowers no arm (every path raises; an else-led "
                          f"arm is one-reading, any other unsupported-type); missing: completing "
                          f"the arm's open prefix with the continuation after #endif, milestone 3")
            elif typ == "preproc_conditional_table_relation":
                reason = (f"debt(C1, M3): {typ} nested in an else chain: its host is registry "
                          f"policy `unsupported`; C1 builds the lowering that merges the arm's "
                          f"relation into the enclosing table_relation_expression (roadmap C1 "
                          f"names this host)")
        elif kind == "one-reading" and typ == "preproc_split_open_statement":
            # A4 fix 1, I2: every arm is else-led, so EVERY configuration of the input is
            # refused; no configuration is the declared reading.
            assert n_cfg[r["input_id"]] == n_bad[r["input_id"]], r["input_id"]
            reason = (f"debt(C1, M3): no declared reading for else-led arms (arm:not-else-led): "
                      f"every arm of this #if starts with `else`, so no configuration is the "
                      f"reading. The tree is lossless and deliberate (grammar.js: the node is the "
                      f"next sibling of the if/case whose else it continues; alc accepts every "
                      f"configuration); missing: an assembler attaching each else-led arm to that "
                      f"if/case (ElseAttachment), milestone 3")
        elif kind == "one-reading":
            reason = (f"debt(F1, F1): {typ} is declared one-reading "
                      f"({READING[typ]}); this configuration is outside that reading and needs "
                      f"the configuration-aware parse")
        else:
            reason = (f"debt(C1, M3): {typ} in a #if arm (host {h}) is not a declared arm kind "
                      f"of preproc_conditional_case; needs a re-parenting fragment design")
        counts[(label, "debt", key)] += 1
    elif key == "multi-config-parse:error":
        assert rel.endswith("EDocumentServiceDE.PageExt.al"), rel
        reason = ("debt(F1, F1): split `add*` layout headers whose bodies stay open over "
                  "#endif (deferred-work item 10): the multi-configuration tree ERRORs, every "
                  "configuration alone is valid AL (resolve tier: pass); no rule lowers it")
        counts[(label, "debt", key)] += 1
    elif key == "reference-error:error":
        probe, sym = PROBES[cid]
        assert f"{sym}=1" in r["config"], r
        reason = (f"invalid-source: {sym} defined removes a field's header and `{{` but not its "
                  f"`}}` after #endif, closing `fields` early (preproc_split_table_field_open "
                  f"family; nobody builds with {sym}); evidence: alc_probe "
                  f"tools/alc_probe/cases/production-invalid/{probe}")
        counts[(label, "invalid-source", key)] += 1
    else:
        raise SystemExit(f"unrecognised: {item[:200]}")
    lines.append(f"{cid}\t{r['config']}\tcannot-validate:{key}\t{reason}")

hdr = out_path.read_text(encoding="utf-8").split("\n")
hdr = [l for l in hdr if l.startswith("#") and not l.startswith(("# corpus-head ", "# corpus-untracked "))]
# The corpus commits these entries come from: the run's (short) HEADs, expanded.
import subprocess
summary = (findings.parent / "summary.md").read_text(encoding="utf-8").replace("\r", "")
for label, short in sorted(re.findall(r"^- corpus .*?: ([\w.-]+), (\w+)$", summary, re.M)):
    full = subprocess.run(["git", "-C", ROOTS[label], "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    assert full.startswith(short), (label, short, full)
    hdr.append(f"# corpus-head {label} {full}")
    # N1: the untracked .al files the run read, by content (cli.al_status is the check's own reader)
    hdr += [f"# corpus-untracked {label} {sha} {path}"
            for path, sha in sorted(cli.al_status(ROOTS[label])[1].items())]
out_path.write_text("\n".join(hdr + sorted(lines)) + "\n", encoding="utf-8", newline="\n")
for k, v in sorted(counts.items()):
    print(v, *k, sep="\t")
print(len(lines), "entries")
