"""Baseline persistence, downward ratchet, and the exit-code policy."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .model import Cluster

EXIT_OK = 0
EXIT_REGRESSION = 1
EXIT_CORPUS_BROKEN = 2
EXIT_STALE_PARSER = 3


@dataclass(frozen=True)
class Baseline:
    manifest_hash: str
    counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Diff:
    new: list[Cluster] = field(default_factory=list)
    regressed: list[tuple[Cluster, int]] = field(default_factory=list)
    fixed: list[str] = field(default_factory=list)
    ratcheted: list[tuple[str, int, int]] = field(default_factory=list)


def load(path: Path) -> Baseline | None:
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Baseline(manifest_hash=raw["manifest_hash"], counts=dict(raw["counts"]))


def save(path: Path, base: Baseline) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"manifest_hash": base.manifest_hash, "counts": dict(sorted(base.counts.items()))}
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def diff(base: Baseline, clusters: list[Cluster]) -> Diff:
    observed = {c.key: c for c in clusters}
    result = Diff()

    for key, cluster in sorted(observed.items()):
        accepted = base.counts.get(key)
        if accepted is None:
            result.new.append(cluster)
        elif cluster.count > accepted:
            result.regressed.append((cluster, accepted))
        elif cluster.count < accepted:
            result.ratcheted.append((key, accepted, cluster.count))

    for key, accepted in sorted(base.counts.items()):
        if key not in observed and accepted > 0:
            result.fixed.append(key)
            result.ratcheted.append((key, accepted, 0))

    return result


def apply_ratchet(base: Baseline, changes: Diff) -> Baseline:
    """Lower accepted counts to what was observed. The bar only ever moves down."""
    counts = dict(base.counts)
    for key, _accepted, observed in changes.ratcheted:
        counts[key] = observed
    return Baseline(manifest_hash=base.manifest_hash, counts=counts)


def exit_code(changes: Diff) -> int:
    if changes.new or changes.regressed:
        return EXIT_REGRESSION
    return EXIT_OK
