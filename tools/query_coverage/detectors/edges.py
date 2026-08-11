"""Detector 8: the (parent, field, child) edge census.

Every other detector in this harness asks a question about NODES. This one asks
about the FIELD GRAPH -- which node is attached to which parent, through which
field. That is a different question, and it is the one nothing here could
answer before.

A wrong-parent attachment can preserve every node's type and every byte's span.
When it does:

  * detector 1 (gaps) sees nothing -- byte coverage is a property of leaves, and
    re-attaching a subtree moves no bytes,
  * detector 2 (errors) sees nothing -- there is no ERROR node,
  * detector 5 (anchors) sees nothing -- the lexical anchor counts are unchanged,
  * detector 7 (corpus) sees nothing -- it counts node TYPES, and every type is
    still produced, in exactly the same quantity.

That is not hypothetical. The three precedence fixes on this branch rewrote 636
trees across BC.History, and the before/after census recorded 13,339,003 fielded
edges on BOTH sides with `node_types: 0 changed`. Every node type kept its exact
count while 48 edge kinds moved. A node-type census is structurally blind here.

WHAT COUNTS AS AN EDGE

For each node, each child that occupies a named field contributes one
`(parent_type, field, child_type)` edge. Anonymous children count when they sit
in a field -- `(additive_expression, operator, "+")` is an edge -- because the
operator token is exactly the kind of thing a consumer reads out of a field.
Children with no field are not edges: they have no attachment to be wrong about
in the sense this detector can check.

TWO CATEGORIES, AND WHY BOTH

`edge-kind` -- one finding per DISTINCT edge kind observed in scope. An edge
kind that is NEW relative to the baseline is a node attached somewhere it has
never been attached before, which is the direct signal for a wrong-parent
regression. One finding per kind, never per instance: 920 kinds over 13.3M edges
at corpus scope, so a per-instance shape would emit millions of findings and
drown every other detector in the report.

`field-never-populated` -- one finding per declared `(parent, field)` that NO
file in scope populated, restricted to parents whose type is itself observed.
This is the disappearance half, and it is needed because `baseline.diff` treats
a vanished cluster as `fixed` and exits 0: a silent regression that stops
producing an edge would otherwise be reported as good news. Emitting a positive
finding for the ABSENCE is the same shape `corpus.detect` uses for never-observed
node types, and it makes the disappearance gate like everything else.

The restriction to observed parents is what keeps this useful rather than
enormous. Corpus-wide, 37 of the 396 declared fields are never populated, but 33
of those belong to node types that never appear at all -- which is precisely what
detector 7 already reports, so repeating it here would be noise. Four remain.

WHY THE ABSENCE CHECK IS PER-FIELD AND NOT PER-EDGE-KIND

The declared universe of edge KINDS is `src/node-types.json`'s cross product,
2,817 of them, of which only 920 are ever produced. Emitting 1,897 findings for
the unproduced remainder would be ~12x the entire current baseline and almost
all of it structural noise: node-types.json lists the union of every alternative
each field can hold, and real code exercises a subset. At the FIELD level the
same question has 37 answers instead of 1,897, and it is the level at which the
answer is actionable -- "this field is never populated" is a defect report,
"this field never holds this particular one of its 54 declared child types" is
usually just corpus variation.

WHAT THIS STILL DOES NOT CATCH

An edge that moves between two kinds that BOTH already exist elsewhere, where
the source field also stays populated by other nodes. The kind set is unchanged
and no field goes dark, so neither category fires. Catching that needs per-kind
COUNTS in the gate, which cannot be expressed as cluster counts without one
finding per instance. `reports/edge-census.json` carries the full `{kind: count}`
map for exactly this reason: it makes the reviewer's before/after comparison
reproducible as a TOOL without turning every intentional tree change into a
build failure. Run `qc run --all --full-corpus` before and after a refactor and
diff the two files.
"""

from __future__ import annotations

from ..model import Finding

DETECTOR = "edges"

# Where a finding points when it has no instance to point at. Same convention as
# corpus.detect and fields._skip_finding: the located fields stay at zero and
# `detail` carries the specifics.
DECLARATION_PATH = "src/node-types.json"


def declared_fields(node_types: list[dict]) -> dict[tuple[str, str], dict]:
    """Every `(named_type, field)` declared in node-types.json, with its spec.

    Anonymous types are skipped: node-types.json gives them no `fields` key at
    all, so there is nothing to declare and nothing to miss.
    """
    out: dict[tuple[str, str], dict] = {}
    for entry in node_types:
        if not entry.get("named"):
            continue
        for field_name, spec in (entry.get("fields") or {}).items():
            out[(entry["type"], field_name)] = spec
    return out


class EdgeCensus:
    """Run-level accumulator for the field graph.

    Deliberately NOT a per-file `detect(tree, source, path)` like detectors 1-5.
    A finding here is "this edge kind exists in the corpus", which is a property
    of the whole run, not of one file. Written per-file it would emit the same
    kind once per file containing it -- up to 920 x 15,358 duplicate findings
    that clustering would then collapse anyway, for no gain and a large cost.
    `shipped_queries.QueryTally` is the existing precedent for this shape, and
    for the same reason.
    """

    def __init__(self) -> None:
        self.counts: dict[tuple[str, str, str], int] = {}
        self.parent_fields: set[tuple[str, str]] = set()
        self.node_types: set[str] = set()
        # First place each kind was seen, so a finding can point at real source
        # instead of at zeros. Recorded at most once per kind.
        self.first_seen: dict[tuple[str, str, str], tuple[str, int, int, int]] = {}

    def add(self, tree, source: bytes, path: str) -> None:
        counts = self.counts
        parent_fields = self.parent_fields
        node_types = self.node_types
        first_seen = self.first_seen

        # Explicit stack, never recursion -- same hazard _tree.walk documents: a
        # deeply nested AL file blows Python's recursion limit long before the C
        # stack. Order is irrelevant to a census, so children are pushed as-is.
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            if node.is_named:
                node_types.add(node.type)
            children = node.children
            if not children:
                continue
            parent_type = node.type
            field_name_for_child = node.field_name_for_child
            for index, child in enumerate(children):
                name = field_name_for_child(index)
                if name is None:
                    continue
                key = (parent_type, name, child.type)
                counts[key] = counts.get(key, 0) + 1
                parent_fields.add((parent_type, name))
                if key not in first_seen:
                    line = source[: child.start_byte].count(b"\n") + 1
                    first_seen[key] = (path, child.start_byte, line, child.start_point[1] + 1)
            stack.extend(children)

    def as_report(self) -> dict:
        """The full {kind: count} map, for reports/edge-census.json."""
        return {
            "edge_kinds": len(self.counts),
            "edge_total": sum(self.counts.values()),
            "edges": {"|".join(key): value for key, value in sorted(self.counts.items())},
        }


def detect(census: EdgeCensus, node_types: list[dict]) -> list[Finding]:
    """Findings for the observed edge kinds and the fields nothing populated."""
    findings: list[Finding] = []

    for key in sorted(census.counts):
        parent_type, field_name, child_type = key
        path, byte_offset, line, column = census.first_seen[key]
        findings.append(
            Finding(
                detector=DETECTOR,
                category="edge-kind",
                fingerprint=("edge", parent_type, field_name, child_type),
                path=path,
                byte_offset=byte_offset,
                line=line,
                column=column,
                enclosing=parent_type,
                snippet=f"{parent_type}.{field_name} -> {child_type}",
                detail={
                    "parent": parent_type,
                    "field": field_name,
                    "child": child_type,
                    # Reported, never fingerprinted. A count in the fingerprint
                    # would make every intentional tree change a NEW cluster and
                    # turn the gate into a tripwire; see the module docstring.
                    "instances": census.counts[key],
                },
            )
        )

    for (parent_type, field_name), spec in sorted(declared_fields(node_types).items()):
        if (parent_type, field_name) in census.parent_fields:
            continue
        # A field of a type nothing produced is detector 7's finding, not this
        # one. Reporting it here too would add 33 duplicates at corpus scope.
        if parent_type not in census.node_types:
            continue
        findings.append(
            Finding(
                detector=DETECTOR,
                category="field-never-populated",
                fingerprint=("field-never-populated", parent_type, field_name),
                path=DECLARATION_PATH,
                byte_offset=0,
                line=0,
                column=0,
                enclosing=parent_type,
                snippet=(
                    f"field {parent_type}.{field_name} is declared but no node in "
                    f"scope populated it, while {parent_type} itself was produced"
                ),
                detail={
                    "parent": parent_type,
                    "field": field_name,
                    "required": bool(spec.get("required")),
                    "declared_children": sorted(
                        child["type"] for child in spec.get("types", ())
                    ),
                },
            )
        )

    return findings
