#!/usr/bin/env python3
"""Compare VS Code keywords with grammar keywords."""

import json
from pathlib import Path

from config import (
    OUTPUT_DIR,
    PRIORITY_LEVELS,
    get_special_handling,
)


def load_vscode_keywords() -> dict:
    """Load VS Code keywords from JSON."""
    vscode_file = OUTPUT_DIR / "vscode_keywords.json"
    if not vscode_file.exists():
        raise FileNotFoundError(f"Run extract_vscode_keywords.py first: {vscode_file}")

    with open(vscode_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_grammar_keywords() -> dict:
    """Load grammar keywords from JSON."""
    grammar_file = OUTPUT_DIR / "grammar_keywords.json"
    if not grammar_file.exists():
        raise FileNotFoundError(f"Run extract_grammar_keywords.py first: {grammar_file}")

    with open(grammar_file, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_keywords() -> dict:
    """Compare VS Code and grammar keywords."""
    vscode_data = load_vscode_keywords()
    grammar_data = load_grammar_keywords()

    # Flatten VS Code keywords into a single set with categories
    vscode_keywords = {}
    for category, keywords in vscode_data.get("keywords", {}).items():
        for kw in keywords:
            vscode_keywords[kw.lower()] = {
                "category": category,
                "source": "tmlanguage",
            }

    # Add snippet enum values
    for prop_key, values in vscode_data.get("snippet_enums", {}).items():
        for val in values:
            if val.lower() not in vscode_keywords:
                vscode_keywords[val.lower()] = {
                    "category": "snippet_enums",
                    "source": prop_key,
                }

    # Get grammar keywords
    grammar_keywords = set(grammar_data.get("keywords", {}).keys())

    # Find differences
    missing_in_grammar = set(vscode_keywords.keys()) - grammar_keywords
    extra_in_grammar = grammar_keywords - set(vscode_keywords.keys())
    common = grammar_keywords & set(vscode_keywords.keys())

    # Categorize missing keywords
    missing_by_category = {}
    for kw in missing_in_grammar:
        info = vscode_keywords[kw]
        category = info["category"]
        if category not in missing_by_category:
            missing_by_category[category] = []
        missing_by_category[category].append({
            "keyword": kw,
            "source": info["source"],
            "priority": PRIORITY_LEVELS.get(category, 99),
            "special_handling": get_special_handling(kw),
        })

    # Sort by priority within each category
    for category in missing_by_category:
        missing_by_category[category].sort(key=lambda x: (x["priority"], x["keyword"]))

    # Analyze grammar keywords not in VS Code (may be valid additions)
    extra_analysis = []
    for kw in extra_in_grammar:
        kw_data = grammar_data["keywords"].get(kw, {})
        extra_analysis.append({
            "keyword": kw,
            "type": kw_data.get("type", "unknown"),
            "precedence": kw_data.get("precedence"),
        })

    result = {
        "summary": {
            "vscode_total": len(vscode_keywords),
            "grammar_total": len(grammar_keywords),
            "common": len(common),
            "missing_in_grammar": len(missing_in_grammar),
            "extra_in_grammar": len(extra_in_grammar),
        },
        "missing_in_grammar": missing_by_category,
        "extra_in_grammar": extra_analysis,
        "vscode_extension_version": vscode_data.get("extension_version", "unknown"),
    }

    return result


def save_results(data: dict) -> Path:
    """Save comparison results to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "comparison_results.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print(f"Saved results to {output_file}")
    return output_file


def print_summary(data: dict):
    """Print a summary of the comparison."""
    summary = data["summary"]

    print("\n=== Keyword Comparison Summary ===")
    print(f"VS Code Extension Version: {data['vscode_extension_version']}")
    print(f"VS Code keywords: {summary['vscode_total']}")
    print(f"Grammar keywords: {summary['grammar_total']}")
    print(f"Common keywords: {summary['common']}")
    print(f"Missing in grammar: {summary['missing_in_grammar']}")
    print(f"Extra in grammar: {summary['extra_in_grammar']}")

    if data["missing_in_grammar"]:
        print("\n=== Missing Keywords by Category ===")
        for category, keywords in sorted(
            data["missing_in_grammar"].items(),
            key=lambda x: PRIORITY_LEVELS.get(x[0], 99),
        ):
            priority = PRIORITY_LEVELS.get(category, 99)
            print(f"\n{category} (priority {priority}):")
            for kw_data in keywords[:10]:  # Show first 10
                special = f" [{kw_data['special_handling']}]" if kw_data["special_handling"] != "kw" else ""
                print(f"  - {kw_data['keyword']}{special}")
            if len(keywords) > 10:
                print(f"  ... and {len(keywords) - 10} more")


if __name__ == "__main__":
    data = compare_keywords()
    save_results(data)
    print_summary(data)
