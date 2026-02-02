#!/usr/bin/env python3
"""Extract keywords from VS Code AL extension."""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from config import TEXTMATE_SCOPE_MAP, OUTPUT_DIR, find_al_extension


def parse_tmlanguage(file_path: Path) -> dict[str, list[str]]:
    """Parse alsyntax.tmlanguage XML file and extract keywords by category."""
    keywords = {}

    tree = ET.parse(file_path)
    root = tree.getroot()

    # Navigate plist structure: plist -> dict -> array (patterns)
    main_dict = root.find("dict")
    if main_dict is None:
        return keywords

    # Find the patterns array
    patterns_array = None
    keys = main_dict.findall("key")
    for i, key in enumerate(keys):
        if key.text == "patterns":
            # The array follows the key
            all_children = list(main_dict)
            key_idx = all_children.index(key)
            if key_idx + 1 < len(all_children):
                patterns_array = all_children[key_idx + 1]
            break

    if patterns_array is None:
        return keywords

    # Process each pattern dict
    for pattern_dict in patterns_array.findall("dict"):
        match_pattern = None
        scope_name = None

        pattern_keys = pattern_dict.findall("key")
        for i, key in enumerate(pattern_keys):
            children = list(pattern_dict)
            key_idx = children.index(key)
            value_elem = children[key_idx + 1] if key_idx + 1 < len(children) else None

            if key.text == "match" and value_elem is not None:
                match_pattern = value_elem.text
            elif key.text == "name" and value_elem is not None:
                scope_name = value_elem.text

        if match_pattern and scope_name and scope_name in TEXTMATE_SCOPE_MAP:
            category = TEXTMATE_SCOPE_MAP[scope_name]

            # Extract keywords from pattern like \b(?i:(WORD1|WORD2|...))\b
            keyword_match = re.search(r"\(\?i:\(([^)]+)\)\)", match_pattern)
            if keyword_match:
                keyword_list = keyword_match.group(1).split("|")
                # Normalize to lowercase
                keyword_list = [kw.lower() for kw in keyword_list]
                keywords[category] = keyword_list

    return keywords


def is_valid_keyword(value: str) -> bool:
    """Check if a value looks like a valid keyword (not a number, template, or garbage)."""
    # Skip pure numbers
    if re.match(r"^\d+$", value):
        return False
    # Skip values with brackets (like code[50], text[50])
    if "[" in value or "]" in value:
        return False
    # Skip values with colons (like codeunit::, page::)
    if "::" in value:
        return False
    # Skip very short values (like single chars)
    if len(value) < 2:
        return False
    # Skip values that don't start with a letter
    if not re.match(r"^[a-zA-Z]", value):
        return False
    # Must be alphanumeric (allow underscores)
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", value):
        return False
    return True


def parse_snippets(snippets_dir: Path) -> dict[str, list[str]]:
    """Parse snippet JSON files and extract enum values."""
    enum_values = {}

    if not snippets_dir.exists():
        return enum_values

    for snippet_file in snippets_dir.glob("*.json"):
        try:
            with open(snippet_file, "r", encoding="utf-8") as f:
                snippets = json.load(f)

            for snippet_name, snippet_data in snippets.items():
                if "body" not in snippet_data:
                    continue

                body = snippet_data["body"]
                if isinstance(body, list):
                    body = "\n".join(body)

                # Find patterns like ${N|val1,val2,...|}
                enum_matches = re.findall(r"\$\{\d+\|([^}]+)\|\}", body)
                for match in enum_matches:
                    values = [v.strip().lower() for v in match.split(",")]

                    # Try to identify the property name from context
                    # Look for PropertyName = ${N|...|}
                    prop_patterns = re.findall(
                        r"(\w+)\s*=\s*\$\{\d+\|" + re.escape(match) + r"\|\}",
                        body,
                        re.IGNORECASE,
                    )

                    property_name = prop_patterns[0].lower() if prop_patterns else "unknown"

                    key = f"snippet:{property_name}"
                    if key not in enum_values:
                        enum_values[key] = []

                    for val in values:
                        # Filter out invalid values
                        if val and is_valid_keyword(val) and val not in enum_values[key]:
                            enum_values[key].append(val)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to parse {snippet_file}: {e}")

    # Remove empty categories
    enum_values = {k: v for k, v in enum_values.items() if v}

    return enum_values


def extract_vscode_keywords() -> dict:
    """Main extraction function."""
    al_extension = find_al_extension()

    if not al_extension:
        print("Error: Could not find VS Code AL extension")
        return {}

    print(f"Found AL extension at: {al_extension}")

    result = {
        "extension_path": str(al_extension),
        "extension_version": al_extension.name.split("-")[-1],
        "keywords": {},
        "snippet_enums": {},
    }

    # Parse tmlanguage file
    tmlanguage_file = al_extension / "syntaxes" / "alsyntax.tmlanguage"
    if tmlanguage_file.exists():
        result["keywords"] = parse_tmlanguage(tmlanguage_file)
        print(f"Extracted keywords from {tmlanguage_file}")
        for category, kws in result["keywords"].items():
            print(f"  {category}: {len(kws)} keywords")
    else:
        print(f"Warning: {tmlanguage_file} not found")

    # Parse snippets
    snippets_dir = al_extension / "snippets"
    if snippets_dir.exists():
        result["snippet_enums"] = parse_snippets(snippets_dir)
        print(f"Extracted enum values from snippets")
        for prop, values in result["snippet_enums"].items():
            print(f"  {prop}: {len(values)} values")

    return result


def save_results(data: dict) -> Path:
    """Save extraction results to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "vscode_keywords.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print(f"Saved results to {output_file}")
    return output_file


if __name__ == "__main__":
    data = extract_vscode_keywords()
    if data:
        save_results(data)
