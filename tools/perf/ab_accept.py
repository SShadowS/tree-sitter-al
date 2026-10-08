"""B7b-3 perf acceptance: two `python -m tools.perf ab --out` results must both have
identical trees, the same lib_a/lib_b (path, and sha256 when recorded), at least 24 rounds
and a median time(A)/time(B) of at least 0.97.

    python -m tools.perf.ab_accept RUN1.json RUN2.json

Exit 0 both pass; 1 a run is below 0.97 or built different trees; 2 a file cannot be read."""
from __future__ import annotations

import json
import sys
from pathlib import Path

FLOOR = 0.97
MIN_ROUNDS = 24


def _libs(r):
    return tuple((r[k]["path"], r[k].get("sha256")) for k in ("lib_a", "lib_b"))


def main(argv=None):
    paths = argv if argv is not None else sys.argv[1:]
    if len(paths) != 2:
        print("usage: ab_accept.py RUN1.json RUN2.json", file=sys.stderr)
        return 2
    code, libs = 0, set()
    for p in paths:
        try:
            r = json.loads(Path(p).read_text(encoding="utf-8"))["groups"]["ab"]
            libs.add(_libs(r))
            if not r["trees_identical"]:
                print(f"ab_accept: {p}: trees differ, no ratio")
                code = 1
                continue
            m, rounds = r["ratio_a_over_b"]["median"], r["rounds"]
        except (OSError, ValueError, KeyError) as e:
            print(f"ab_accept: cannot read {p}: {e!r}", file=sys.stderr)
            return 2
        print(f"ab_accept: {p}: median time A / time B {m:.3f} ({'ok' if m >= FLOOR else f'below {FLOOR}'})")
        code = code or (0 if m >= FLOOR else 1)
        if rounds < MIN_ROUNDS:
            print(f"ab_accept: {p}: {rounds} rounds, need >= {MIN_ROUNDS}")
            code = 1
    if len(libs) > 1:
        print(f"ab_accept: the runs used different libraries: {sorted(libs)}")
        code = 1
    return code


if __name__ == "__main__":
    sys.exit(main())
