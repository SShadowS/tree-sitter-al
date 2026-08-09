#!/usr/bin/env python3
"""
check-field-types.py - Field-shape invariant checks for node-types.json

Asserts that specific grammar node fields have exactly the declared shape
(multiple + type set) in the generated src/node-types.json.

Why this exists: a field() call that wraps more than one grammar symbol
(e.g. field('sizes', seq($.integer, repeat(seq(',', $.integer))))) can leak
an unwanted anonymous token into the field's DECLARED type set. A parse-tree
diff (tree-harness) cannot catch this - it compares parsed output, and
node-types.json is a static declaration, not a parsed tree. This script checks
the declaration directly.

Two things are asserted per row:

  * `multiple` - whether the field may hold more than one node.
  * `anon`     - the EXACT set of anonymous (unnamed) members the field may
                 carry. This is the load-bearing check: a field that mixes
                 named and anonymous types is usually a separator or
                 terminator that leaked in because the field spanned a whole
                 seq. `anon=set()` means "this field must be free of
                 punctuation".
  * `types`    - optionally, the exact set of ALL member type names. Used
                 where the set is small and stable; `None` skips it, so that
                 adding an unrelated new value type to a large choice does not
                 produce a false failure and get this check switched off.

Every row carries a verdict, so the audit that produced it cannot be
re-litigated from memory:

  FIXED      - the shape was wrong and the grammar was corrected; the row
               asserts the corrected shape.
  DELIBERATE - the anonymous member is the value itself (an operator, a
               wildcard). Mixed on purpose; the row pins that intent.
  DEFERRED   - known imprecision, deliberately not fixed yet, with the reason
               and the cost of fixing recorded here rather than in a report.

To add a new invariant: append an Invariant(...) to FIELD_INVARIANTS below.

Usage:
    python tools/check-field-types.py
"""

import json
import sys
from collections import namedtuple
from pathlib import Path

NODE_TYPES_PATH = Path(__file__).parent.parent / 'src' / 'node-types.json'

Invariant = namedtuple(
    'Invariant',
    'node field multiple types anon verdict why',
)


def inv(node, field, multiple, anon, verdict, why, types=None):
    return Invariant(node, field, multiple, types, anon, verdict, why)


FIELD_INVARIANTS = [
    # ---------------------------------------------------------------- FIXED
    # array[10,20] of Integer -- each size dimension must field its own
    # integer individually. field('sizes', seq(int, repeat(',', int))) wraps
    # the WHOLE comma-separated seq in one field, so the anonymous ','
    # leaked into the declared type set. Fixed in grammar.js's array_type
    # rule by fielding each $.integer on its own.
    inv('array_type', 'sizes', True, set(), 'FIXED',
        "',' leaked from a seq-spanning field; each size now fielded alone",
        types={'integer'}),

    # DataItemLink dotted form: DataItem.FieldName. field('value', seq(id,
    # '.', id)) wraps the WHOLE dotted seq in one field, so the anonymous
    # '.' leaked into the declared type set. Fixed in grammar.js's
    # link_value rule by fielding each identifier on its own.
    inv('link_value', 'value', True, set(), 'FIXED',
        "'.' leaked from a seq-spanning field; each name part now fielded alone",
        types={
            'boolean', 'database_reference', 'date_literal', 'datetime_literal',
            'filter_value', 'identifier', 'integer', 'keyword_identifier',
            'qualified_enum_value', 'quoted_identifier', 'string_literal',
            'time_literal',
        }),

    # case ... else body: field('body', repeat($._statement)) fielded EACH
    # statement in the repeat individually, so 'body' was multiple:true and
    # broke the single-node body invariant the textobject queries rely on
    # (issue #19). Fixed in grammar.js's case_else_branch rule by wrapping
    # the repeat in $.statement_block, matching repeat_statement's shape.
    inv('case_else_branch', 'body', False, set(), 'FIXED',
        'single-node body invariant for textobject queries (issue #19)',
        types={'code_block', 'statement_block'}),

    # -- Task 17: dotted references -----------------------------------------
    # All seven below fielded the shared hidden rule `_namespaced_or_simple_ref`
    # as one unit, so on `Record System.Reflection.Field` a consumer calling
    # children_by_field_name('reference') got back
    #   [System, '.', Reflection, '.', Field]
    # -- the separators inherited the field. Verified reachable at runtime with
    # a TSTreeCursor walk (the mechanism children_by_field_name uses), not just
    # declared: tree-sitter's --cst/--xml output cannot show fields on
    # anonymous nodes, and the query engine reports only the first name part,
    # so neither tool can settle this.
    #
    # Fixed by grammar.js's namespacedRefFielded() helper plus one hidden
    # variant per distinct field name, so every name part carries the field
    # individually and the '.' carries nothing.
    inv('record_type', 'reference', True, set(), 'FIXED',
        "'.' separator inherited the field from a seq-spanning field",
        types={'identifier', 'integer', 'quoted_identifier'}),
    inv('dotnet_type', 'reference', True, set(), 'FIXED',
        "'.' separator inherited the field from a seq-spanning field",
        types={'identifier', 'integer', 'quoted_identifier', 'string_literal'}),
    inv('object_reference_type', 'reference', True, set(), 'FIXED',
        "'.' separator inherited the field from a seq-spanning field",
        types={'identifier', 'integer', 'quoted_identifier'}),
    inv('simple_table_relation', 'table', True, set(), 'FIXED',
        "'.' separator inherited the field from a seq-spanning field",
        types={'identifier', 'integer', 'member_expression', 'quoted_identifier'}),
    inv('report_dataitem', 'table_name', True, set(), 'FIXED',
        "'.' separator inherited the field from a seq-spanning field",
        types={'identifier', 'integer', 'quoted_identifier'}),
    inv('query_dataitem', 'table_name', True, set(), 'FIXED',
        "'.' separator inherited the field from a seq-spanning field",
        types={'identifier', 'integer', 'quoted_identifier'}),

    # CalcFormula = - sum(...) -- `_calc_formula_expression` carried a
    # `seq('-', $.aggregate_formula)` branch. Being hidden, the '-' landed as a
    # direct child of `property` and inherited the `value` field, so
    # children_by_field_name('value') returned ['-', aggregate_formula].
    # Fixed by absorbing the optional sign into `aggregate_formula` itself, so
    # the value is one node. Deliberately NOT done by introducing a
    # `negated_aggregate_formula` node type: a new node type risks an
    # unhandled-variant panic in the owned-IR consumer, and this fix adds none.
    # `types` is not pinned -- this is a 30-member choice of every legal
    # property value, and pinning it would fail on unrelated additions.
    inv('property', 'value', True, set(), 'FIXED',
        "'-' of a negated CalcFormula inherited the value field"),

    # ----------------------------------------------------------- DELIBERATE
    # `Permissions = tabledata * = RIMD` -- the wildcard IS the table name, so
    # an anonymous member in this field's type set is correct, exactly as for
    # the `operator` fields on the expression rules. The '.' that also used to
    # appear here was a real defect and is fixed above; the '*' stays.
    inv('tabledata_permission', 'table_name', True, {'*'}, 'DELIBERATE',
        "'*' wildcard IS the table name, like an operator field",
        types={'*', 'identifier', 'integer', 'quoted_identifier'}),

    # -- Task 17: statement bodies and branches ------------------------------
    # The 14 rows below all used to carry a ';'. Root cause was single and
    # shared: `_statement` is `seq(choice(...23 statements...), optional(';'))`
    # and is hidden, so ANY `field(X, $._statement)` spanned the terminator.
    # The ';' was never inside the statement node -- it was a loose sibling
    # that inherited the field.
    #
    # Reachable at runtime, not merely declared: before the fix, a TSTreeCursor
    # walk of `while i > 0 do i := 2;` showed children_by_field_name('body')
    # returning [assignment_statement, ';'] -- two nodes, multiple:true. Note
    # that `tree-sitter parse -c` CANNOT show this, because it does not print
    # field names on anonymous nodes at all (see the note on the dotted
    # references above); the cursor is the only instrument that settles it.
    #
    # Fixed by splitting `_statement` into `_statement_inner` plus its
    # terminator, and giving every body/branch position its own field via
    # fieldedStatement(), so the ';' stays outside the field. All 14 are now
    # `multiple: False` with a single named node, matching the
    # `case_else_branch.body` invariant above (issue #19) -- previously one
    # construct honoured that invariant and fourteen siblings contradicted it.
    #
    # No parse tree moved: this only drops a field label from a ';' that was
    # already there. `multiple=False` is the load-bearing half of each row --
    # it is what the textobject queries depend on.
    inv('case_branch', 'body', False, set(), 'FIXED',
        "single-node body; ';' no longer inherits the field"),
    inv('for_statement', 'body', False, set(), 'FIXED',
        "single-node body; ';' no longer inherits the field"),
    inv('foreach_statement', 'body', False, set(), 'FIXED',
        "single-node body; ';' no longer inherits the field"),
    inv('if_statement', 'then_branch', False, set(), 'FIXED',
        "single-node branch; ';' no longer inherits the field"),
    inv('if_statement', 'else_branch', False, set(), 'FIXED',
        "single-node branch; ';' no longer inherits the field"),
    inv('preproc_guarded_statement', 'then_branch', False, set(), 'FIXED',
        "single-node branch; ';' no longer inherits the field"),
    inv('preproc_split_case_branch', 'body', False, set(), 'FIXED',
        "single-node body; ';' no longer inherits the field"),
    inv('preproc_split_case_extended', 'body', False, set(), 'FIXED',
        "single-node body; ';' no longer inherits the field"),
    inv('preproc_split_if_statement', 'then_branch', False, set(), 'FIXED',
        "single-node branch; ';' no longer inherits the field"),
    inv('preproc_split_if_statement', 'else_branch', False, set(), 'FIXED',
        "single-node branch; ';' no longer inherits the field"),
    # multiple=True here is correct and unrelated to the ';' defect: this rule
    # has three separate then_branch positions (the base #if plus its #elif and
    # #else header variants), so one node legitimately carries the field more
    # than once. What matters is that the anonymous ';' is gone.
    inv('preproc_split_if_else_statement', 'then_branch', True, set(), 'FIXED',
        "';' no longer inherits the field (multiple: one per #if/#elif/#else header)"),
    inv('preproc_split_if_else_statement', 'else_branch', False, set(), 'FIXED',
        "single-node branch; ';' no longer inherits the field"),
    inv('while_statement', 'body', False, set(), 'FIXED',
        "single-node body; ';' no longer inherits the field"),
    inv('with_statement', 'body', False, set(), 'FIXED',
        "single-node body; ';' no longer inherits the field"),
]


def load_node_types():
    if not NODE_TYPES_PATH.exists():
        print(f"ERROR: {NODE_TYPES_PATH} not found -- run `tree-sitter generate` first.",
              file=sys.stderr)
        sys.exit(1)
    return json.loads(NODE_TYPES_PATH.read_text(encoding='utf-8'))


def find_node(node_types, node_type):
    matches = [n for n in node_types if n.get('type') == node_type]
    return matches[0] if matches else None


def check(node_types, want):
    """Return an error string describing the violation, or None if it holds."""
    node = find_node(node_types, want.node)
    if node is None:
        return f"node type '{want.node}' not found in node-types.json"

    field = node.get('fields', {}).get(want.field)
    if field is None:
        return f"'{want.node}' has no field '{want.field}'"

    problems = []

    actual_multiple = field.get('multiple')
    if actual_multiple != want.multiple:
        problems.append(f"multiple={actual_multiple!r}, expected {want.multiple!r}")

    members = field.get('types', [])

    actual_anon = {t['type'] for t in members if not t.get('named')}
    if actual_anon != want.anon:
        extra = actual_anon - want.anon
        missing = want.anon - actual_anon
        detail = []
        if extra:
            detail.append(f"unexpected anonymous members {sorted(extra)}")
        if missing:
            detail.append(f"missing anonymous members {sorted(missing)}")
        problems.append(
            f"anonymous member set {sorted(actual_anon)} wrong ({'; '.join(detail)})")

    if want.types is not None:
        actual_types = {t['type'] for t in members}
        if actual_types != want.types:
            extra = actual_types - want.types
            missing = want.types - actual_types
            detail = []
            if extra:
                detail.append(f"unexpected members {sorted(extra)}")
            if missing:
                detail.append(f"missing members {sorted(missing)}")
            problems.append(
                f"type set {sorted(actual_types)} wrong ({'; '.join(detail)})")

    if problems:
        return (f"[{want.verdict}] '{want.node}.{want.field}': "
                + '; '.join(problems)
                + f"  (invariant: {want.why})")
    return None


def main():
    node_types = load_node_types()

    failures = []
    for want in FIELD_INVARIANTS:
        error = check(node_types, want)
        if error:
            failures.append(error)

    total = len(FIELD_INVARIANTS)
    passed = total - len(failures)

    if failures:
        print(f"FAILED: {len(failures)}/{total} field-shape invariant(s) violated:")
        for f in failures:
            print(f"  - {f}")
        return 1

    by_verdict = {}
    for want in FIELD_INVARIANTS:
        by_verdict[want.verdict] = by_verdict.get(want.verdict, 0) + 1
    summary = ', '.join(f"{v.lower()} {n}" for v, n in sorted(by_verdict.items()))
    print(f"PASSED: {passed}/{total} field-shape invariant(s) hold ({summary})")
    return 0


if __name__ == '__main__':
    sys.exit(main())
