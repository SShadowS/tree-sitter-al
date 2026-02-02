#!/usr/bin/env python3
"""Compare VS Code snippet triggers with grammar.js trigger declarations.

Identifies:
- Triggers in snippets not defined in grammar
- Trigger naming patterns
"""

import json
import re
from pathlib import Path

from config import OUTPUT_DIR, GRAMMAR_FILE


def load_snippets_data() -> dict:
    """Load snippets data from JSON."""
    snippets_file = OUTPUT_DIR / "snippets_data.json"
    if not snippets_file.exists():
        raise FileNotFoundError(f"Run extract_snippets.py first: {snippets_file}")

    with open(snippets_file, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_grammar_triggers(grammar_content: str) -> dict:
    """Extract trigger-related rules from grammar.js."""
    triggers = {
        "trigger_names": [],
        "trigger_rules": [],
    }

    # Find trigger declaration rules
    trigger_rule_pattern = r"(\w*trigger\w*)\s*:\s*\$\s*=>"
    rule_matches = re.finditer(trigger_rule_pattern, grammar_content, re.IGNORECASE)

    for match in rule_matches:
        rule_name = match.group(1)
        triggers["trigger_rules"].append(rule_name)

    # Find kw() calls that look like trigger names (On*)
    kw_pattern = r"kw\s*\(\s*['\"](\w+)['\"]"
    kw_matches = re.finditer(kw_pattern, grammar_content)

    for match in kw_matches:
        keyword = match.group(1)
        # Trigger names typically start with "On"
        if keyword.lower().startswith("on"):
            if keyword.lower() not in [t.lower() for t in triggers["trigger_names"]]:
                triggers["trigger_names"].append(keyword)

    # Also find trigger name choices
    # Look for patterns like: choice(kw('OnInsert'), kw('OnModify'), ...)
    choice_pattern = r"choice\s*\(([\s\S]*?)\)"
    choice_matches = re.finditer(choice_pattern, grammar_content)

    for match in choice_matches:
        choice_content = match.group(1)
        # Find kw() calls within this choice
        inner_kw = re.findall(r"kw\s*\(\s*['\"](\w+)['\"]", choice_content)
        for kw in inner_kw:
            if kw.lower().startswith("on"):
                if kw.lower() not in [t.lower() for t in triggers["trigger_names"]]:
                    triggers["trigger_names"].append(kw)

    return triggers


def compare_triggers() -> dict:
    """Compare snippet triggers with grammar triggers."""
    # Load snippet data
    snippets_data = load_snippets_data()

    # Load and parse grammar
    if not GRAMMAR_FILE.exists():
        raise FileNotFoundError(f"Grammar file not found: {GRAMMAR_FILE}")

    with open(GRAMMAR_FILE, "r", encoding="utf-8") as f:
        grammar_content = f.read()

    grammar_triggers = extract_grammar_triggers(grammar_content)

    # Get all trigger names from snippets
    snippet_triggers = set()
    for trigger in snippets_data.get("triggers", []):
        snippet_triggers.add(trigger.lower())

    # Get grammar trigger names (lowercase for comparison)
    grammar_trigger_names = set(t.lower() for t in grammar_triggers["trigger_names"])

    # Find differences
    missing_in_grammar = snippet_triggers - grammar_trigger_names
    extra_in_grammar = grammar_trigger_names - snippet_triggers
    common = snippet_triggers & grammar_trigger_names

    result = {
        "summary": {
            "snippet_triggers": len(snippet_triggers),
            "grammar_triggers": len(grammar_trigger_names),
            "common": len(common),
            "missing_in_grammar": len(missing_in_grammar),
            "extra_in_grammar": len(extra_in_grammar),
        },
        "snippet_triggers": sorted(list(snippet_triggers)),
        "grammar_triggers": sorted(list(grammar_trigger_names)),
        "missing_in_grammar": sorted(list(missing_in_grammar)),
        "extra_in_grammar": sorted(list(extra_in_grammar)),
        "common": sorted(list(common)),
        "extension_version": snippets_data.get("extension_version", "unknown"),
    }

    return result


def save_results(data: dict) -> Path:
    """Save comparison results to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "trigger_comparison.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print(f"Saved results to {output_file}")
    return output_file


def print_summary(data: dict):
    """Print a summary of the comparison."""
    summary = data["summary"]

    print("\n=== Trigger Comparison Summary ===")
    print(f"Extension Version: {data.get('extension_version', 'unknown')}")
    print(f"Snippet triggers: {summary['snippet_triggers']}")
    print(f"Grammar triggers: {summary['grammar_triggers']}")
    print(f"Common: {summary['common']}")
    print(f"Missing in grammar: {summary['missing_in_grammar']}")
    print(f"Extra in grammar: {summary['extra_in_grammar']}")

    if data["missing_in_grammar"]:
        print("\n=== Missing Triggers ===")
        for trigger in data["missing_in_grammar"]:
            print(f"  - {trigger}")

    if data["extra_in_grammar"]:
        print("\n=== Extra Triggers in Grammar (may be valid) ===")
        for trigger in data["extra_in_grammar"][:20]:
            print(f"  - {trigger}")
        if len(data["extra_in_grammar"]) > 20:
            print(f"  ... and {len(data['extra_in_grammar']) - 20} more")


if __name__ == "__main__":
    data = compare_triggers()
    save_results(data)
    print_summary(data)
