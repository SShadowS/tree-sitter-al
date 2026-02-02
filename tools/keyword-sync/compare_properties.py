#!/usr/bin/env python3
"""Compare VS Code snippet properties with grammar.js property rules.

Identifies:
- Properties in snippets not defined in grammar
- Properties defined in grammar but not used in snippets
- Properties that may need special handling
"""

import json
import re
from pathlib import Path

from config import OUTPUT_DIR, GRAMMAR_FILE, get_special_handling


def load_snippets_data() -> dict:
    """Load snippets data from JSON."""
    snippets_file = OUTPUT_DIR / "snippets_data.json"
    if not snippets_file.exists():
        raise FileNotFoundError(f"Run extract_snippets.py first: {snippets_file}")

    with open(snippets_file, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_grammar_properties(grammar_content: str) -> dict:
    """Extract property-related rules from grammar.js."""
    properties = {}

    # Match property rules: property_name: $ => ... or _property_name: $ =>
    # Common patterns:
    # - xxx_property: $ => _value_property_template(kw('xxx'), ...)
    # - xxx_property: $ => seq(kw('xxx'), ...)
    # - xxx_property: $ => prec(N, seq(kw('xxx'), ...))

    # Find all rules that look like property definitions
    rule_pattern = r"(\w*property\w*)\s*:\s*\$\s*=>"
    rule_matches = re.finditer(rule_pattern, grammar_content, re.IGNORECASE)

    for match in rule_matches:
        rule_name = match.group(1)
        properties[rule_name.lower()] = {
            "rule_name": rule_name,
            "type": "property_rule",
        }

    # Also find kw() calls that look like property names
    kw_pattern = r"kw\s*\(\s*['\"](\w+)['\"]"
    kw_matches = re.finditer(kw_pattern, grammar_content)

    for match in kw_matches:
        keyword = match.group(1).lower()
        # Check if this looks like a property (ends in common suffixes or is a known property)
        if keyword not in properties:
            properties[keyword] = {
                "keyword": keyword,
                "type": "kw_call",
            }

    # Find property category lists (_universal_properties, etc.)
    category_pattern = r"(_\w*properties)\s*:\s*\$\s*=>\s*(?:prec(?:\.\w+)?\s*\(\s*\d*\s*,?\s*)?choice\s*\(([\s\S]*?)\)(?:\s*\))?,"
    category_matches = re.finditer(category_pattern, grammar_content)

    for match in category_matches:
        category_name = match.group(1)
        category_content = match.group(2)

        # Extract $. references
        rule_refs = re.findall(r"\$\.(\w+)", category_content)
        properties[f"category:{category_name}"] = {
            "category": category_name,
            "rules": rule_refs,
            "type": "property_category",
        }

    return properties


def normalize_property_name(name: str) -> set[str]:
    """Generate normalized variants of a property name for comparison.

    Returns a set of possible normalized forms (lowercase, no underscores, with underscores).
    """
    name_lower = name.lower()
    # Without underscores
    no_underscore = name_lower.replace("_", "")
    # With underscores at word boundaries (simple heuristic)
    return {name_lower, no_underscore}


def compare_properties() -> dict:
    """Compare snippet properties with grammar properties."""
    # Load snippet data
    snippets_data = load_snippets_data()

    # Load and parse grammar
    if not GRAMMAR_FILE.exists():
        raise FileNotFoundError(f"Grammar file not found: {GRAMMAR_FILE}")

    with open(GRAMMAR_FILE, "r", encoding="utf-8") as f:
        grammar_content = f.read()

    grammar_properties = extract_grammar_properties(grammar_content)

    # Get all property names from snippets
    snippet_properties = set()
    for prop_name in snippets_data.get("properties", {}).keys():
        snippet_properties.add(prop_name.lower())

    # Get all enum choice property names
    for prop_name in snippets_data.get("enum_choices", {}).keys():
        if prop_name != "unknown":
            snippet_properties.add(prop_name.lower())

    # Get grammar keywords (lowercase for comparison) with normalized variants
    grammar_keywords = set()
    grammar_keywords_normalized = set()  # All normalized forms
    for key, value in grammar_properties.items():
        if value.get("type") == "kw_call":
            keyword = value["keyword"]
            grammar_keywords.add(keyword)
            grammar_keywords_normalized.update(normalize_property_name(keyword))
        elif value.get("type") == "property_rule":
            # Extract property name from rule name
            rule_name = value["rule_name"]
            # Remove common suffixes
            prop_name = re.sub(r"_property$", "", rule_name, flags=re.IGNORECASE)
            grammar_keywords.add(prop_name.lower())
            grammar_keywords_normalized.update(normalize_property_name(prop_name))

    # Find differences using normalized comparison
    # A snippet property is "missing" if none of its normalized forms match grammar
    missing_in_grammar = set()
    common = set()

    for prop in snippet_properties:
        prop_normalized = normalize_property_name(prop)
        if prop_normalized & grammar_keywords_normalized:
            common.add(prop)
        else:
            missing_in_grammar.add(prop)

    extra_in_grammar = grammar_keywords - snippet_properties

    # Create case-insensitive lookup for properties
    props_lower_map = {}
    for key, value in snippets_data.get("properties", {}).items():
        props_lower_map[key.lower()] = value

    enum_lower_map = {}
    for key, value in snippets_data.get("enum_choices", {}).items():
        enum_lower_map[key.lower()] = value

    # Categorize missing properties
    missing_details = []
    for prop in sorted(missing_in_grammar):
        prop_info = props_lower_map.get(prop, {})
        enum_info = enum_lower_map.get(prop, [])

        detail = {
            "property": prop,
            "special_handling": get_special_handling(prop),
            "sources": prop_info.get("sources", []),
            "example_values": prop_info.get("example_values", [])[:3],  # Limit examples
            "has_enum_values": bool(enum_info),
            "enum_values": enum_info[:10] if enum_info else [],  # Limit enum values
        }
        missing_details.append(detail)

    # Sort by whether they have enum values (more structured = higher priority)
    missing_details.sort(key=lambda x: (not x["has_enum_values"], x["property"]))

    result = {
        "summary": {
            "snippet_properties": len(snippet_properties),
            "grammar_keywords": len(grammar_keywords),
            "common": len(common),
            "missing_in_grammar": len(missing_in_grammar),
            "extra_in_grammar": len(extra_in_grammar),
        },
        "missing_in_grammar": missing_details,
        "extra_in_grammar": sorted(list(extra_in_grammar)),
        "extension_version": snippets_data.get("extension_version", "unknown"),
    }

    return result


def save_results(data: dict) -> Path:
    """Save comparison results to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "property_comparison.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print(f"Saved results to {output_file}")
    return output_file


def print_summary(data: dict):
    """Print a summary of the comparison."""
    summary = data["summary"]

    print("\n=== Property Comparison Summary ===")
    print(f"Extension Version: {data.get('extension_version', 'unknown')}")
    print(f"Snippet properties: {summary['snippet_properties']}")
    print(f"Grammar keywords: {summary['grammar_keywords']}")
    print(f"Common: {summary['common']}")
    print(f"Missing in grammar: {summary['missing_in_grammar']}")
    print(f"Extra in grammar: {summary['extra_in_grammar']}")

    if data["missing_in_grammar"]:
        print("\n=== Missing Properties (High Priority - with enum values) ===")
        high_priority = [p for p in data["missing_in_grammar"] if p["has_enum_values"]]
        for prop in high_priority[:10]:
            special = f" [{prop['special_handling']}]" if prop["special_handling"] != "kw" else ""
            values = ", ".join(prop["enum_values"][:5])
            if len(prop["enum_values"]) > 5:
                values += "..."
            print(f"  {prop['property']}{special}: {values}")

        if len(high_priority) > 10:
            print(f"  ... and {len(high_priority) - 10} more")

        print("\n=== Missing Properties (Lower Priority - no enum values) ===")
        low_priority = [p for p in data["missing_in_grammar"] if not p["has_enum_values"]]
        for prop in low_priority[:10]:
            special = f" [{prop['special_handling']}]" if prop["special_handling"] != "kw" else ""
            sources = ", ".join(prop["sources"][:2])
            print(f"  {prop['property']}{special} (from: {sources})")

        if len(low_priority) > 10:
            print(f"  ... and {len(low_priority) - 10} more")


if __name__ == "__main__":
    data = compare_properties()
    save_results(data)
    print_summary(data)
