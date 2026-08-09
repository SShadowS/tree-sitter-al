#!/usr/bin/env python3
"""
check-field-types.py - Field-shape invariant checks for node-types.json

Asserts that specific grammar node fields have exactly the declared shape
(multiple + type set) in the generated src/node-types.json.

Why this exists: a field() call that wraps more than one grammar symbol
(e.g. field('sizes', seq($.integer, repeat(seq(',', $.integer))))) can leak
an unwanted anonymous token into the field's DECLARED type set, even when
the compiled parser never actually assigns that field to that token for any
real input. A parse-tree diff (tree-harness) cannot catch this — it compares
parsed output, and node-types.json is a static declaration, not a parsed
tree. This script checks the declaration directly.

To add a new invariant: append a row to FIELD_INVARIANTS below.

Usage:
    python tools/check-field-types.py
"""

import json
import sys
from pathlib import Path

NODE_TYPES_PATH = Path(__file__).parent.parent / 'src' / 'node-types.json'

# Each row: (node_type, field_name, expected_multiple, expected_type_names)
# expected_type_names is the exact set of `type` strings the field's `types`
# list must contain -- no more, no less (order doesn't matter).
FIELD_INVARIANTS = [
    # array[10,20] of Integer -- each size dimension must field its own
    # integer individually. field('sizes', seq(int, repeat(',', int))) wraps
    # the WHOLE comma-separated seq in one field, so the anonymous ','
    # leaked into the declared type set. Fixed in grammar.js's array_type
    # rule by fielding each $.integer on its own.
    ('array_type', 'sizes', True, {'integer'}),
    # DataItemLink dotted form: DataItem.FieldName. field('value', seq(id,
    # '.', id)) wraps the WHOLE dotted seq in one field, so the anonymous
    # '.' leaked into the declared type set. Fixed in grammar.js's
    # link_value rule by fielding each identifier on its own.
    ('link_value', 'value', True, {
        'boolean', 'database_reference', 'date_literal', 'datetime_literal',
        'filter_value', 'identifier', 'integer', 'keyword_identifier',
        'qualified_enum_value', 'quoted_identifier', 'string_literal',
        'time_literal',
    }),
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


def check(node_types, node_type, field_name, expected_multiple, expected_types):
    """Return an error string describing the violation, or None if the invariant holds."""
    node = find_node(node_types, node_type)
    if node is None:
        return f"node type '{node_type}' not found in node-types.json"

    field = node.get('fields', {}).get(field_name)
    if field is None:
        return f"'{node_type}' has no field '{field_name}'"

    problems = []

    actual_multiple = field.get('multiple')
    if actual_multiple != expected_multiple:
        problems.append(f"multiple={actual_multiple!r}, expected {expected_multiple!r}")

    actual_types = {t['type'] for t in field.get('types', [])}
    if actual_types != expected_types:
        extra = actual_types - expected_types
        missing = expected_types - actual_types
        detail = []
        if extra:
            detail.append(f"unexpected members {sorted(extra)}")
        if missing:
            detail.append(f"missing members {sorted(missing)}")
        problems.append(f"type set {sorted(actual_types)} wrong ({'; '.join(detail)})")

    if problems:
        return f"'{node_type}.{field_name}': " + '; '.join(problems)
    return None


def main():
    node_types = load_node_types()

    failures = []
    for node_type, field_name, expected_multiple, expected_types in FIELD_INVARIANTS:
        error = check(node_types, node_type, field_name, expected_multiple, expected_types)
        if error:
            failures.append(error)

    total = len(FIELD_INVARIANTS)
    passed = total - len(failures)

    if failures:
        print(f"FAILED: {len(failures)}/{total} field-shape invariant(s) violated:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"PASSED: {passed}/{total} field-shape invariant(s) hold")
    return 0


if __name__ == '__main__':
    sys.exit(main())
