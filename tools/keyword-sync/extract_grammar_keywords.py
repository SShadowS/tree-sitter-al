#!/usr/bin/env python3
"""Extract keywords from grammar.js."""

import json
import re
from pathlib import Path

from config import GRAMMAR_FILE, OUTPUT_DIR


def extract_kw_calls(content: str) -> list[dict]:
    """Extract all kw('keyword') and kw('keyword', precedence) calls."""
    keywords = []

    # Match kw('keyword') or kw('keyword', number) or kw("keyword")
    pattern = r"kw\s*\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*(\d+))?\s*\)"
    matches = re.finditer(pattern, content)

    for match in matches:
        keyword = match.group(1).lower()
        precedence = int(match.group(2)) if match.group(2) else None
        keywords.append({
            "keyword": keyword,
            "precedence": precedence,
            "type": "kw",
        })

    return keywords


def extract_kw_with_eq_calls(content: str) -> list[dict]:
    """Extract all kw_with_eq('keyword') calls."""
    keywords = []

    pattern = r"kw_with_eq\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
    matches = re.finditer(pattern, content)

    for match in matches:
        keyword = match.group(1).lower()
        keywords.append({
            "keyword": keyword,
            "type": "kw_with_eq",
        })

    return keywords


def extract_choice_operators(content: str) -> list[dict]:
    """Extract operators defined using choice('op1', 'OP1', ...)."""
    keywords = []

    # Look for operator-related choice patterns
    # This is a heuristic - we look for choice() with case variations
    pattern = r"choice\s*\(\s*(['\"][a-zA-Z]+['\"](?:\s*,\s*['\"][a-zA-Z]+['\"])+)\s*\)"
    matches = re.finditer(pattern, content)

    for match in matches:
        values = re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))
        if values:
            # Check if this looks like case variations of the same word
            normalized = set(v.lower() for v in values)
            if len(normalized) == 1:
                keyword = list(normalized)[0]
                keywords.append({
                    "keyword": keyword,
                    "type": "choice_operator",
                })

    return keywords


def extract_semantic_categories(content: str) -> dict[str, list[str]]:
    """Extract semantic category definitions like _universal_properties."""
    categories = {}

    # Match patterns like: _category_name: $ => choice(...) or _category_name: $ => prec.left(choice(...))
    # Also match array-style definitions
    category_pattern = r"(_\w+_properties|\w+_properties)\s*:\s*\$\s*=>\s*(?:prec(?:\.\w+)?\s*\(\s*\d*\s*,?\s*)?choice\s*\("

    matches = list(re.finditer(category_pattern, content))

    for match in matches:
        category_name = match.group(1)
        start_pos = match.end()

        # Find the matching closing paren by counting brackets
        depth = 1
        pos = start_pos
        while pos < len(content) and depth > 0:
            if content[pos] == "(":
                depth += 1
            elif content[pos] == ")":
                depth -= 1
            pos += 1

        choice_content = content[start_pos : pos - 1]

        # Extract $. references (rule references)
        rule_refs = re.findall(r"\$\.(\w+)", choice_content)
        categories[category_name] = rule_refs

    return categories


def extract_externals(content: str) -> list[str]:
    """Extract external scanner tokens."""
    externals = []

    pattern = r"externals\s*:\s*\$\s*=>\s*\[([\s\S]*?)\]"
    match = re.search(pattern, content)

    if match:
        externals_content = match.group(1)
        token_refs = re.findall(r"\$\.(\w+)", externals_content)
        externals = token_refs

    return externals


def extract_grammar_keywords() -> dict:
    """Main extraction function."""
    if not GRAMMAR_FILE.exists():
        print(f"Error: Grammar file not found at {GRAMMAR_FILE}")
        return {}

    print(f"Reading grammar from: {GRAMMAR_FILE}")

    with open(GRAMMAR_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract all keyword types
    kw_calls = extract_kw_calls(content)
    kw_with_eq_calls = extract_kw_with_eq_calls(content)
    choice_operators = extract_choice_operators(content)

    # Deduplicate keywords
    all_keywords = {}
    for kw_data in kw_calls + kw_with_eq_calls + choice_operators:
        keyword = kw_data["keyword"]
        if keyword not in all_keywords:
            all_keywords[keyword] = kw_data
        else:
            # Prefer more specific types
            if kw_data["type"] in ("kw_with_eq", "choice_operator"):
                all_keywords[keyword] = kw_data

    # Extract semantic categories
    categories = extract_semantic_categories(content)

    # Extract externals
    externals = extract_externals(content)

    result = {
        "grammar_file": str(GRAMMAR_FILE),
        "total_kw_calls": len(kw_calls),
        "total_kw_with_eq_calls": len(kw_with_eq_calls),
        "total_choice_operators": len(choice_operators),
        "unique_keywords": len(all_keywords),
        "keywords": all_keywords,
        "semantic_categories": categories,
        "externals": externals,
    }

    print(f"Found {result['total_kw_calls']} kw() calls")
    print(f"Found {result['total_kw_with_eq_calls']} kw_with_eq() calls")
    print(f"Found {result['total_choice_operators']} choice operators")
    print(f"Unique keywords: {result['unique_keywords']}")
    print(f"Semantic categories: {len(categories)}")
    print(f"External tokens: {len(externals)}")

    return result


def save_results(data: dict) -> Path:
    """Save extraction results to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "grammar_keywords.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print(f"Saved results to {output_file}")
    return output_file


if __name__ == "__main__":
    data = extract_grammar_keywords()
    if data:
        save_results(data)
