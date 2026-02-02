#!/usr/bin/env python3
"""Extract structured data from VS Code AL extension snippets.

Extracts:
- Property names
- Trigger names
- Section/area names
- Enum value choices
- Object structure patterns
"""

import json
import re
from pathlib import Path
from collections import defaultdict

from config import OUTPUT_DIR, find_al_extension


def extract_enum_choices(body_text: str) -> list[dict]:
    """Extract ${N|val1,val2,...|} patterns from snippet body."""
    choices = []

    # Find all ${N|...|}  patterns
    pattern = r"\$\{(\d+)\|([^}]+)\|\}"
    matches = re.finditer(pattern, body_text)

    for match in matches:
        placeholder_num = int(match.group(1))
        values = [v.strip() for v in match.group(2).split(",")]

        # Try to find context - what property/section is this for?
        # Look backwards for PropertyName = ${N|...|}
        before_match = body_text[:match.start()]

        # Try to find property name: PropertyName = ${N|
        prop_match = re.search(r"(\w+)\s*=\s*$", before_match.strip())
        property_name = prop_match.group(1) if prop_match else None

        # Try to find section/keyword context: area(${N|...
        section_match = re.search(r"(\w+)\s*\(\s*$", before_match.strip())
        section_context = section_match.group(1) if section_match else None

        choices.append({
            "values": values,
            "property_name": property_name,
            "section_context": section_context,
            "placeholder": placeholder_num,
        })

    return choices


def extract_property_assignments(body_text: str) -> list[dict]:
    """Extract PropertyName = Value; patterns from snippet body."""
    properties = []

    # Match PropertyName = ... ; (various value types)
    # Including placeholder values like ${N|...|}
    pattern = r"(\w+)\s*=\s*([^;\n]+);"
    matches = re.finditer(pattern, body_text)

    for match in matches:
        prop_name = match.group(1)
        value = match.group(2).strip()

        # Extract actual value if it's a simple placeholder ${N:value}
        simple_placeholder = re.match(r"\$\{\d+:([^}]+)\}", value)
        if simple_placeholder:
            value = simple_placeholder.group(1)

        # If it's an enum placeholder ${N|...|}, keep the property but mark value as enum
        enum_placeholder = re.match(r"\$\{\d+\|([^}]+)\|\}", value)
        if enum_placeholder:
            value = f"[enum: {enum_placeholder.group(1)[:30]}...]"

        properties.append({
            "name": prop_name,
            "example_value": value,
        })

    return properties


def extract_trigger_names(body_text: str) -> list[str]:
    """Extract trigger names from snippet body."""
    triggers = []

    # Placeholder names to skip (generic snippet placeholders)
    placeholder_names = {
        "onwhat", "mytrigger", "onsomething", "triggerhere",
        "myevent", "myhandler", "triggerplaceholder",
    }

    # Match 'trigger OnSomething()' or 'trigger ${N:OnSomething}()'
    pattern = r"trigger\s+(?:\$\{\d+:)?(\w+)\}?\s*\("
    matches = re.finditer(pattern, body_text, re.IGNORECASE)

    for match in matches:
        trigger_name = match.group(1)
        # Skip placeholder names
        if trigger_name.lower() in placeholder_names:
            continue
        if trigger_name not in triggers:
            triggers.append(trigger_name)

    return triggers


def extract_section_names(body_text: str) -> list[dict]:
    """Extract section/area names from snippet body."""
    sections = []

    # Match 'sectiontype(Name)' patterns like area(Content), layout, etc.
    # Common sections: layout, actions, area, group, repeater, etc.
    pattern = r"\b(area|layout|actions|group|repeater|dataset|requestpage|rendering|keys|fields|fieldgroups|views|dataitem)\s*(?:\(|\{)"
    matches = re.finditer(pattern, body_text, re.IGNORECASE)

    for match in matches:
        section_type = match.group(1).lower()
        if {"type": section_type} not in sections:
            sections.append({"type": section_type})

    # Also find area types: area(Content), area(Factboxes), etc.
    area_pattern = r"area\s*\((\w+)\)"
    area_matches = re.finditer(area_pattern, body_text, re.IGNORECASE)

    for match in area_matches:
        area_type = match.group(1)
        entry = {"type": "area", "name": area_type}
        if entry not in sections:
            sections.append(entry)

    return sections


def extract_object_keywords(body_text: str) -> list[str]:
    """Extract object type keywords from snippet body."""
    keywords = []

    # Keywords that appear as standalone constructs
    construct_patterns = [
        r"\b(field|column|key|part|systempart|usercontrol|view|analysisview)\s*\(",
        r"\b(action|actionref|customaction|systemaction)\s*\(",
        r"\b(event|procedure)\s+",
    ]

    for pattern in construct_patterns:
        matches = re.finditer(pattern, body_text, re.IGNORECASE)
        for match in matches:
            keyword = match.group(1).lower()
            if keyword not in keywords:
                keywords.append(keyword)

    return keywords


def parse_snippet_file(file_path: Path) -> dict:
    """Parse a single snippet JSON file."""
    result = {
        "file": file_path.name,
        "snippets": [],
        "all_properties": [],
        "all_enum_choices": [],
        "all_triggers": [],
        "all_sections": [],
        "all_keywords": [],
    }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            snippets = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Warning: Failed to parse {file_path}: {e}")
        return result

    for snippet_name, snippet_data in snippets.items():
        if "body" not in snippet_data:
            continue

        body = snippet_data["body"]
        if isinstance(body, list):
            body = "\n".join(body)

        snippet_info = {
            "name": snippet_name,
            "prefix": snippet_data.get("prefix", ""),
            "enum_choices": extract_enum_choices(body),
            "properties": extract_property_assignments(body),
            "triggers": extract_trigger_names(body),
            "sections": extract_section_names(body),
            "keywords": extract_object_keywords(body),
        }

        result["snippets"].append(snippet_info)

        # Aggregate
        for choice in snippet_info["enum_choices"]:
            if choice not in result["all_enum_choices"]:
                result["all_enum_choices"].append(choice)

        for prop in snippet_info["properties"]:
            if prop["name"] not in [p["name"] for p in result["all_properties"]]:
                result["all_properties"].append(prop)

        for trigger in snippet_info["triggers"]:
            if trigger not in result["all_triggers"]:
                result["all_triggers"].append(trigger)

        for section in snippet_info["sections"]:
            if section not in result["all_sections"]:
                result["all_sections"].append(section)

        for keyword in snippet_info["keywords"]:
            if keyword not in result["all_keywords"]:
                result["all_keywords"].append(keyword)

    return result


def parse_all_snippets(snippets_dir: Path) -> dict:
    """Parse all snippet files in the directory."""
    result = {
        "snippets_dir": str(snippets_dir),
        "files_parsed": 0,
        "by_file": {},
        # Aggregated across all files
        "properties": {},  # name -> {sources, example_values}
        "enum_choices": {},  # property_name -> [values]
        "triggers": [],
        "sections": [],
        "area_types": [],
        "keywords": [],
    }

    if not snippets_dir.exists():
        print(f"Snippets directory not found: {snippets_dir}")
        return result

    for snippet_file in sorted(snippets_dir.glob("*.json")):
        file_data = parse_snippet_file(snippet_file)
        result["by_file"][snippet_file.name] = file_data
        result["files_parsed"] += 1

        # Aggregate properties
        for prop in file_data["all_properties"]:
            name = prop["name"]
            if name not in result["properties"]:
                result["properties"][name] = {
                    "sources": [snippet_file.name],
                    "example_values": [prop["example_value"]],
                }
            else:
                if snippet_file.name not in result["properties"][name]["sources"]:
                    result["properties"][name]["sources"].append(snippet_file.name)
                if prop["example_value"] not in result["properties"][name]["example_values"]:
                    result["properties"][name]["example_values"].append(prop["example_value"])

        # Aggregate enum choices
        for choice in file_data["all_enum_choices"]:
            prop = choice.get("property_name") or choice.get("section_context") or "unknown"
            if prop not in result["enum_choices"]:
                result["enum_choices"][prop] = []
            for val in choice["values"]:
                if val not in result["enum_choices"][prop]:
                    result["enum_choices"][prop].append(val)

        # Aggregate triggers
        for trigger in file_data["all_triggers"]:
            if trigger not in result["triggers"]:
                result["triggers"].append(trigger)

        # Aggregate sections
        for section in file_data["all_sections"]:
            if section.get("type") == "area" and section.get("name"):
                area_name = section["name"]
                if area_name not in result["area_types"]:
                    result["area_types"].append(area_name)
            else:
                section_type = section.get("type")
                if section_type and section_type not in result["sections"]:
                    result["sections"].append(section_type)

        # Aggregate keywords
        for keyword in file_data["all_keywords"]:
            if keyword not in result["keywords"]:
                result["keywords"].append(keyword)

    return result


def extract_snippets() -> dict:
    """Main extraction function."""
    al_extension = find_al_extension()

    if not al_extension:
        print("Error: Could not find VS Code AL extension")
        return {}

    print(f"Found AL extension at: {al_extension}")

    snippets_dir = al_extension / "snippets"
    result = parse_all_snippets(snippets_dir)

    result["extension_path"] = str(al_extension)
    result["extension_version"] = al_extension.name.split("-")[-1]

    # Print summary
    print(f"\nParsed {result['files_parsed']} snippet files")
    print(f"Found {len(result['properties'])} unique properties")
    print(f"Found {len(result['enum_choices'])} enum choice sets")
    print(f"Found {len(result['triggers'])} triggers")
    print(f"Found {len(result['sections'])} section types")
    print(f"Found {len(result['area_types'])} area types")
    print(f"Found {len(result['keywords'])} keywords")

    return result


def save_results(data: dict) -> Path:
    """Save extraction results to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "snippets_data.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print(f"\nSaved results to {output_file}")
    return output_file


if __name__ == "__main__":
    data = extract_snippets()
    if data:
        save_results(data)
