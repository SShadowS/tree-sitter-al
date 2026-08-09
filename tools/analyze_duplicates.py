#!/usr/bin/env python3
"""
Analyze property patterns to identify:
1. True duplicates (identical logic, different names)
2. Intentional variants (same base concept, different contexts)
3. Consolidation opportunities

Property variants are INTENTIONAL when they exist because:
- Different contexts (entity vs option vs page vs view)
- Different value types (ml vs non-ml)
- Different object types (run_page vs sub_page)

True duplicates should be consolidated if they:
- Have identical implementation patterns
- Serve the same semantic purpose
- Could be replaced by a single parameterized rule

Run from the repository root — grammar.js is read relative to the working
directory.

Usage:
    python tools/analyze_duplicates.py           # Show analysis
    python tools/analyze_duplicates.py --strict  # Only show true duplicates
"""

import re
import sys
import argparse
from collections import defaultdict
from pathlib import Path

# Known intentional variant patterns - these are NOT duplicates
INTENTIONAL_PATTERNS = {
    # Context variants (same property, different scopes)
    'context_variants': [
        ('caption', ['caption', 'entity_caption', 'option_caption', 'view_caption', 'show_caption']),
        ('caption_ml', ['caption_ml', 'entity_caption_ml', 'option_caption_ml']),
        ('name', ['external_name', 'entity_name', 'entity_set_name']),
        ('namespace', ['default_namespace', 'use_default_namespace']),
        ('permissions', ['permissions', 'test_permissions']),
        ('filters', ['filters', 'view_filters']),
        ('link', ['run_page_link', 'sub_page_link', 'data_item_link']),
        ('layout', ['cuegroup_layout', 'word_layout', 'excel_layout', 'rdlc_layout', 'pdf_layout']),
    ],

    # ML (multi-language) variants
    'ml_variants': [
        ('ml', ['tool_tip_ml', 'instructional_text_ml', 'request_filter_heading_ml',
                'additional_search_terms_ml', 'entity_set_caption_ml']),
    ],

    # Object-specific variants (same action, different targets)
    'target_variants': [
        ('run', ['run_page', 'run_object']),
        ('source', ['source_table', 'source_table_view']),
        ('access', ['access_by_permission']),
    ],
}


def extract_property_rules(content):
    """Extract all property rule definitions from grammar.js."""
    properties = {}
    lines = content.split('\n')
    current_rule = None
    current_body = []
    brace_depth = 0

    for i, line in enumerate(lines, 1):
        # Check for property rule definition
        match = re.match(r'^\s*([a-zA-Z_]+_property):\s*\$\s*=>', line)
        if match:
            if current_rule:
                properties[current_rule] = {
                    'line': properties[current_rule]['line'],
                    'body': '\n'.join(current_body)
                }
            current_rule = match.group(1)
            current_body = [line]
            properties[current_rule] = {'line': i, 'body': ''}
            brace_depth = 0
            continue

        if current_rule:
            current_body.append(line)
            brace_depth += line.count('(') - line.count(')')
            # End of rule when we return to depth 0 and see a comma or rule end
            if brace_depth <= 0 and (line.strip().endswith(',') or
                                      re.match(r'^\s*[a-zA-Z_]+:\s*\$\s*=>', line)):
                properties[current_rule]['body'] = '\n'.join(current_body[:-1] if
                    re.match(r'^\s*[a-zA-Z_]+:\s*\$\s*=>', line) else current_body)
                current_rule = None
                current_body = []

    return properties


def normalize_property_body(body):
    """Normalize property body for comparison."""
    # Remove comments
    body = re.sub(r'//.*$', '', body, flags=re.MULTILINE)
    # Remove whitespace
    body = re.sub(r'\s+', ' ', body)
    # Remove property name from start
    body = re.sub(r'^[a-zA-Z_]+_property:\s*\$\s*=>\s*', '', body)
    # Normalize kw() calls by extracting just the keyword
    body = re.sub(r"kw\(['\"](\w+)['\"](?:,\s*\d+)?\)", r'KW(\1)', body)
    # Normalize kw_with_eq() calls
    body = re.sub(r"kw_with_eq\(['\"](\w+)['\"](?:,\s*\d+)?\)", r'KWEQ(\1)', body)
    return body.strip()


def find_base_name(prop_name):
    """Extract the base concept from a property name."""
    # Remove _property suffix
    base = prop_name.replace('_property', '')

    # Known prefixes to strip for grouping
    prefixes = [
        'page_about_', 'about_', 'entity_set_', 'entity_', 'option_',
        'run_page_', 'sub_page_', 'data_item_', 'source_table_',
        'view_', 'show_', 'use_', 'default_', 'external_',
        'additional_search_terms_', 'request_filter_', 'instructional_text_',
        'tool_tip_', 'excel_layout_', 'word_', 'rdlc_', 'pdf_',
        'cuegroup_', 'analysis_mode_', 'maximum_', 'enable_',
    ]

    for prefix in sorted(prefixes, key=len, reverse=True):
        if base.startswith(prefix):
            base = base[len(prefix):]
            break

    return base


def is_intentional_variant(prop_name, group):
    """Check if a property is part of a known intentional variant pattern."""
    for category, patterns in INTENTIONAL_PATTERNS.items():
        for base, variants in patterns:
            if any(v in prop_name for v in variants):
                # Check if other group members are also in this variant family
                variant_count = sum(1 for p in group if any(v in p for v in variants))
                if variant_count > 1:
                    return True, category, base
    return False, None, None


def analyze_duplicates(content, strict=False):
    """Analyze grammar for true duplicates vs intentional variants."""
    properties = extract_property_rules(content)

    # Group by normalized body (true duplicates have same implementation)
    by_body = defaultdict(list)
    for name, info in properties.items():
        normalized = normalize_property_body(info['body'])
        by_body[normalized].append((name, info['line']))

    # Group by base name (potential variants)
    by_base = defaultdict(list)
    for name in properties:
        base = find_base_name(name)
        by_base[base].append(name)

    results = {
        'true_duplicates': [],
        'intentional_variants': [],
        'consolidation_candidates': [],
        'summary': {}
    }

    # Find true duplicates (same implementation)
    for body, props in by_body.items():
        if len(props) > 1:
            names = [p[0] for p in props]
            is_variant, category, _ = is_intentional_variant(names[0], names)
            if not is_variant:
                results['true_duplicates'].append({
                    'properties': props,
                    'normalized_body': body[:100] + '...' if len(body) > 100 else body
                })

    # Find intentional variants (same base, different contexts)
    for base, names in by_base.items():
        if len(names) > 1:
            is_variant, category, pattern_base = is_intentional_variant(names[0], names)
            if is_variant:
                results['intentional_variants'].append({
                    'base': base,
                    'category': category,
                    'properties': names
                })
            elif not strict:
                # Check if these could potentially be consolidated
                bodies = [normalize_property_body(properties[n]['body']) for n in names]
                unique_bodies = len(set(bodies))
                if unique_bodies == 1:
                    results['consolidation_candidates'].append({
                        'base': base,
                        'properties': names,
                        'reason': 'Identical implementations'
                    })
                elif unique_bodies < len(names):
                    results['consolidation_candidates'].append({
                        'base': base,
                        'properties': names,
                        'reason': f'{unique_bodies} unique implementations for {len(names)} properties'
                    })

    results['summary'] = {
        'total_properties': len(properties),
        'true_duplicates': len(results['true_duplicates']),
        'intentional_variants': len(results['intentional_variants']),
        'consolidation_candidates': len(results['consolidation_candidates'])
    }

    return results


def print_report(results, strict=False):
    """Print analysis report."""
    print("=" * 70)
    print("PROPERTY DUPLICATE ANALYSIS")
    print("=" * 70)
    print()

    summary = results['summary']
    print("SUMMARY:")
    print(f"  Total properties analyzed: {summary['total_properties']}")
    print(f"  True duplicates found:     {summary['true_duplicates']}")
    print(f"  Intentional variants:      {summary['intentional_variants']}")
    print(f"  Consolidation candidates:  {summary['consolidation_candidates']}")
    print()

    if results['true_duplicates']:
        print("TRUE DUPLICATES (same implementation, different names):")
        print("-" * 50)
        for dup in results['true_duplicates']:
            print(f"\n  Identical implementation found in:")
            for name, line in dup['properties']:
                print(f"    - {name} (line {line})")
        print()

    if not strict and results['consolidation_candidates']:
        print("CONSOLIDATION CANDIDATES (may benefit from refactoring):")
        print("-" * 50)
        for cand in results['consolidation_candidates']:
            print(f"\n  Base: {cand['base']}")
            print(f"  Reason: {cand['reason']}")
            for prop in cand['properties']:
                print(f"    - {prop}")
        print()

    if results['intentional_variants'] and not strict:
        print("INTENTIONAL VARIANTS (different contexts, expected):")
        print("-" * 50)
        for var in results['intentional_variants'][:5]:  # Show first 5
            print(f"\n  {var['base']} ({var['category']}): {len(var['properties'])} variants")
        if len(results['intentional_variants']) > 5:
            print(f"\n  ... and {len(results['intentional_variants']) - 5} more variant groups")
        print()

    if not results['true_duplicates'] and not results['consolidation_candidates']:
        print("No actionable duplicates found.")
        print()


def main():
    parser = argparse.ArgumentParser(description='Analyze property duplicates')
    parser.add_argument('--strict', action='store_true',
                       help='Only show true duplicates, ignore potential consolidations')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    grammar_path = Path('grammar.js')
    if not grammar_path.exists():
        print("Error: grammar.js not found", file=sys.stderr)
        return 1

    content = grammar_path.read_text(encoding='utf-8')
    results = analyze_duplicates(content, strict=args.strict)

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print_report(results, strict=args.strict)

    return 0


if __name__ == '__main__':
    sys.exit(main())
