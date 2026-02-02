#!/usr/bin/env python3
"""Generate a unified comparison report across all data sources.

Combines:
- Keyword comparison (from tmlanguage)
- Property comparison (from snippets)
- Trigger comparison (from snippets)
- Enum value comparison (from snippets)
"""

import json
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR


def load_all_data() -> dict:
    """Load all comparison data files."""
    data = {}

    # Keywords comparison
    keywords_file = OUTPUT_DIR / "comparison_results.json"
    if keywords_file.exists():
        with open(keywords_file, "r", encoding="utf-8") as f:
            data["keywords"] = json.load(f)
    else:
        data["keywords"] = None

    # Property comparison
    properties_file = OUTPUT_DIR / "property_comparison.json"
    if properties_file.exists():
        with open(properties_file, "r", encoding="utf-8") as f:
            data["properties"] = json.load(f)
    else:
        data["properties"] = None

    # Trigger comparison
    triggers_file = OUTPUT_DIR / "trigger_comparison.json"
    if triggers_file.exists():
        with open(triggers_file, "r", encoding="utf-8") as f:
            data["triggers"] = json.load(f)
    else:
        data["triggers"] = None

    # Snippets data (for enum values and structural info)
    snippets_file = OUTPUT_DIR / "snippets_data.json"
    if snippets_file.exists():
        with open(snippets_file, "r", encoding="utf-8") as f:
            data["snippets"] = json.load(f)
    else:
        data["snippets"] = None

    return data


def generate_markdown_report(data: dict) -> str:
    """Generate a comprehensive markdown report."""
    lines = []

    # Get extension version from any available source
    version = "unknown"
    for key in ["keywords", "properties", "triggers", "snippets"]:
        if data.get(key) and data[key].get("extension_version"):
            version = data[key]["extension_version"]
            break

    lines.append("# VS Code AL Extension Sync Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"VS Code AL Extension: v{version}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This report compares the VS Code AL extension data with the tree-sitter grammar")
    lines.append("to identify gaps and potential improvements.")
    lines.append("")

    # Summary table
    lines.append("| Data Source | Snippet Items | Grammar Items | Missing | Coverage |")
    lines.append("|-------------|---------------|---------------|---------|----------|")

    if data.get("keywords") and data["keywords"].get("summary"):
        s = data["keywords"]["summary"]
        coverage = (s["common"] / s["vscode_total"] * 100) if s["vscode_total"] > 0 else 0
        lines.append(f"| Keywords (tmlanguage) | {s['vscode_total']} | {s['grammar_total']} | {s['missing_in_grammar']} | {coverage:.1f}% |")

    if data.get("properties") and data["properties"].get("summary"):
        s = data["properties"]["summary"]
        coverage = (s["common"] / s["snippet_properties"] * 100) if s["snippet_properties"] > 0 else 0
        lines.append(f"| Properties (snippets) | {s['snippet_properties']} | {s['grammar_keywords']} | {s['missing_in_grammar']} | {coverage:.1f}% |")

    if data.get("triggers") and data["triggers"].get("summary"):
        s = data["triggers"]["summary"]
        coverage = (s["common"] / s["snippet_triggers"] * 100) if s["snippet_triggers"] > 0 else 0
        lines.append(f"| Triggers (snippets) | {s['snippet_triggers']} | {s['grammar_triggers']} | {s['missing_in_grammar']} | {coverage:.1f}% |")

    lines.append("")

    # Section 1: Missing Keywords
    if data.get("keywords") and data["keywords"].get("missing_in_grammar"):
        lines.append("## 1. Missing Keywords (from tmlanguage)")
        lines.append("")
        lines.append("Keywords defined in the TextMate syntax but not found in grammar.js.")
        lines.append("")

        for category, keywords in data["keywords"]["missing_in_grammar"].items():
            if keywords:
                lines.append(f"### {category.replace('_', ' ').title()}")
                lines.append("")
                lines.append("| Keyword | Special Handling |")
                lines.append("|---------|------------------|")
                for kw in keywords[:20]:
                    special = kw.get("special_handling", "kw")
                    lines.append(f"| `{kw['keyword']}` | {special} |")
                if len(keywords) > 20:
                    lines.append(f"| ... | ({len(keywords) - 20} more) |")
                lines.append("")

    # Section 2: Missing Properties
    if data.get("properties") and data["properties"].get("missing_in_grammar"):
        lines.append("## 2. Missing Properties (from snippets)")
        lines.append("")
        lines.append("Properties used in snippets but potentially not in grammar.js.")
        lines.append("")

        # Split by priority
        with_enums = [p for p in data["properties"]["missing_in_grammar"] if p.get("has_enum_values")]
        without_enums = [p for p in data["properties"]["missing_in_grammar"] if not p.get("has_enum_values")]

        if with_enums:
            lines.append("### High Priority (have enum values)")
            lines.append("")
            lines.append("| Property | Enum Values | Sources |")
            lines.append("|----------|-------------|---------|")
            for prop in with_enums[:30]:
                values = ", ".join(prop.get("enum_values", [])[:5])
                if len(prop.get("enum_values", [])) > 5:
                    values += "..."
                sources = ", ".join(prop.get("sources", [])[:2])
                lines.append(f"| `{prop['property']}` | {values} | {sources} |")
            if len(with_enums) > 30:
                lines.append(f"| ... | | ({len(with_enums) - 30} more) |")
            lines.append("")

        if without_enums:
            lines.append("### Lower Priority (no enum values)")
            lines.append("")
            lines.append("| Property | Example Value | Sources |")
            lines.append("|----------|---------------|---------|")
            for prop in without_enums[:20]:
                examples = ", ".join(prop.get("example_values", [])[:2])
                sources = ", ".join(prop.get("sources", [])[:2])
                lines.append(f"| `{prop['property']}` | {examples} | {sources} |")
            if len(without_enums) > 20:
                lines.append(f"| ... | | ({len(without_enums) - 20} more) |")
            lines.append("")

    # Section 3: Missing Triggers
    if data.get("triggers") and data["triggers"].get("missing_in_grammar"):
        lines.append("## 3. Missing Triggers (from snippets)")
        lines.append("")
        lines.append("Triggers used in snippets but not found in grammar.js.")
        lines.append("")

        triggers = data["triggers"]["missing_in_grammar"]
        if triggers:
            lines.append("| Trigger Name |")
            lines.append("|--------------|")
            for trigger in triggers:
                lines.append(f"| `{trigger}` |")
            lines.append("")
        else:
            lines.append("*All snippet triggers are covered in grammar!*")
            lines.append("")

    # Section 4: Enum Values Summary
    if data.get("snippets") and data["snippets"].get("enum_choices"):
        lines.append("## 4. Enum Value Reference")
        lines.append("")
        lines.append("Complete list of enum values found in snippets for each property.")
        lines.append("Use this to verify grammar covers all valid values.")
        lines.append("")

        enum_choices = data["snippets"]["enum_choices"]
        for prop_name in sorted(enum_choices.keys()):
            values = enum_choices[prop_name]
            if values and prop_name != "unknown":
                lines.append(f"### {prop_name}")
                lines.append("")
                lines.append("```")
                lines.append(", ".join(sorted(values)))
                lines.append("```")
                lines.append("")

    # Section 5: Structural Elements
    if data.get("snippets"):
        lines.append("## 5. Structural Elements Reference")
        lines.append("")

        if data["snippets"].get("sections"):
            lines.append("### Section Types")
            lines.append("")
            lines.append("```")
            lines.append(", ".join(sorted(data["snippets"]["sections"])))
            lines.append("```")
            lines.append("")

        if data["snippets"].get("area_types"):
            lines.append("### Area Types")
            lines.append("")
            lines.append("```")
            lines.append(", ".join(sorted(data["snippets"]["area_types"])))
            lines.append("```")
            lines.append("")

        if data["snippets"].get("keywords"):
            lines.append("### Keywords/Constructs")
            lines.append("")
            lines.append("```")
            lines.append(", ".join(sorted(data["snippets"]["keywords"])))
            lines.append("```")
            lines.append("")

    # Section 6: Action Items
    lines.append("## 6. Recommended Actions")
    lines.append("")
    lines.append("Based on the analysis, here are the recommended next steps:")
    lines.append("")

    action_num = 1

    if data.get("keywords"):
        missing_kw = data["keywords"].get("summary", {}).get("missing_in_grammar", 0)
        if missing_kw > 0:
            lines.append(f"{action_num}. **Add {missing_kw} missing keywords** from tmlanguage to grammar.js")
            action_num += 1

    if data.get("properties"):
        missing_props = data["properties"].get("summary", {}).get("missing_in_grammar", 0)
        with_enums = len([p for p in data["properties"].get("missing_in_grammar", []) if p.get("has_enum_values")])
        if with_enums > 0:
            lines.append(f"{action_num}. **Review {with_enums} high-priority properties** that have enum values")
            action_num += 1

    if data.get("triggers"):
        missing_triggers = data["triggers"].get("summary", {}).get("missing_in_grammar", 0)
        if missing_triggers > 0:
            lines.append(f"{action_num}. **Add {missing_triggers} missing triggers** to grammar.js")
            action_num += 1

    if data.get("snippets") and data["snippets"].get("enum_choices"):
        lines.append(f"{action_num}. **Verify enum value coverage** against grammar choice() rules")
        action_num += 1

    if action_num == 1:
        lines.append("*No immediate actions needed - grammar appears well synchronized!*")

    lines.append("")
    lines.append("---")
    lines.append("*Report generated by keyword-sync tools*")
    lines.append("")

    return "\n".join(lines)


def save_report(report: str) -> Path:
    """Save the unified report."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "full_comparison_report.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Saved report to {output_file}")
    return output_file


if __name__ == "__main__":
    data = load_all_data()
    report = generate_markdown_report(data)
    save_report(report)
