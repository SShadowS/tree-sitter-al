#!/usr/bin/env python3
"""Generate markdown report and optional code snippets."""

import json
from datetime import datetime
from pathlib import Path

from config import (
    OUTPUT_DIR,
    PRIORITY_LEVELS,
    OPERATORS_USE_CHOICE,
    CONTEXTUAL_KEYWORDS_USE_KW_WITH_EQ,
    LITERAL_EXCEPTIONS,
)


def load_comparison_results() -> dict:
    """Load comparison results from JSON."""
    results_file = OUTPUT_DIR / "comparison_results.json"
    if not results_file.exists():
        raise FileNotFoundError(f"Run compare_keywords.py first: {results_file}")

    with open(results_file, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_markdown_report(data: dict) -> str:
    """Generate a markdown report."""
    lines = []
    summary = data["summary"]

    lines.append("# Keyword Synchronization Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"VS Code AL Extension: v{data['vscode_extension_version']}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| VS Code keywords | {summary['vscode_total']} |")
    lines.append(f"| Grammar keywords | {summary['grammar_total']} |")
    lines.append(f"| Common (matched) | {summary['common']} |")
    lines.append(f"| Missing in grammar | {summary['missing_in_grammar']} |")
    lines.append(f"| Extra in grammar | {summary['extra_in_grammar']} |")
    lines.append("")

    coverage = (summary['common'] / summary['vscode_total'] * 100) if summary['vscode_total'] > 0 else 0
    lines.append(f"**Coverage**: {coverage:.1f}% of VS Code keywords are in grammar")
    lines.append("")

    # Missing keywords by category
    if data["missing_in_grammar"]:
        lines.append("## Missing Keywords")
        lines.append("")
        lines.append("Keywords found in VS Code AL extension but not in grammar.js.")
        lines.append("")

        # Sort categories by priority
        sorted_categories = sorted(
            data["missing_in_grammar"].items(),
            key=lambda x: PRIORITY_LEVELS.get(x[0], 99),
        )

        for category, keywords in sorted_categories:
            priority = PRIORITY_LEVELS.get(category, 99)
            lines.append(f"### {category.replace('_', ' ').title()} (Priority {priority})")
            lines.append("")

            if keywords:
                lines.append("| Keyword | Special Handling | Source |")
                lines.append("|---------|------------------|--------|")
                for kw_data in keywords:
                    special = kw_data.get("special_handling", "kw")
                    source = kw_data.get("source", "-")
                    lines.append(f"| `{kw_data['keyword']}` | {special} | {source} |")
            else:
                lines.append("*None*")
            lines.append("")

    # Extra keywords (in grammar but not in VS Code)
    if data.get("extra_in_grammar"):
        lines.append("## Extra Keywords in Grammar")
        lines.append("")
        lines.append("Keywords in grammar.js but not in VS Code extension. These may be:")
        lines.append("- Valid additions specific to tree-sitter parsing")
        lines.append("- Obsolete keywords that could be removed")
        lines.append("- Aliases or variations")
        lines.append("")

        extra = data["extra_in_grammar"]
        if len(extra) > 50:
            lines.append(f"*{len(extra)} keywords - showing first 50*")
            lines.append("")
            extra = extra[:50]

        lines.append("| Keyword | Type | Precedence |")
        lines.append("|---------|------|------------|")
        for kw_data in sorted(extra, key=lambda x: x["keyword"]):
            prec = kw_data.get("precedence") or "-"
            kw_type = kw_data.get("type", "unknown")
            lines.append(f"| `{kw_data['keyword']}` | {kw_type} | {prec} |")
        lines.append("")

    # Special handling reference
    lines.append("## Special Handling Reference")
    lines.append("")
    lines.append("Some keywords require special handling per project guidelines:")
    lines.append("")
    lines.append("### Operators (use `choice()` not `kw()`)")
    lines.append("```javascript")
    lines.append("// These conflict with expressions when using kw()")
    for op in OPERATORS_USE_CHOICE:
        variations = ", ".join([f"'{op}'", f"'{op.upper()}'", f"'{op.title()}'"])
        lines.append(f"choice({variations})")
    lines.append("```")
    lines.append("")

    lines.append("### Contextual Keywords (use `kw_with_eq()`)")
    lines.append("```javascript")
    lines.append("// Property names that conflict with variable names")
    for kw in CONTEXTUAL_KEYWORDS_USE_KW_WITH_EQ:
        lines.append(f"kw_with_eq('{kw}')  // Matches '{kw}=' including the equals")
    lines.append("```")
    lines.append("")

    lines.append("### Literal Exceptions")
    lines.append("```javascript")
    lines.append("// When kw_with_eq() doesn't work, use literal strings")
    for kw in LITERAL_EXCEPTIONS:
        lines.append(f"// '{kw}' - use choice('{kw}', '{kw.upper()}', '{kw.title()}')")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def generate_code_snippets(data: dict) -> str:
    """Generate JavaScript code snippets for missing keywords."""
    lines = []

    lines.append("// =============================================================")
    lines.append("// Auto-generated keyword additions for grammar.js")
    lines.append(f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("// Review carefully before integrating!")
    lines.append("// =============================================================")
    lines.append("")

    if not data.get("missing_in_grammar"):
        lines.append("// No missing keywords found!")
        return "\n".join(lines)

    # Group by special handling type
    by_handling = {"kw": [], "choice": [], "kw_with_eq": [], "literal": []}

    for category, keywords in data["missing_in_grammar"].items():
        for kw_data in keywords:
            handling = kw_data.get("special_handling", "kw")
            by_handling[handling].append(kw_data)

    # Standard kw() keywords
    if by_handling["kw"]:
        lines.append("// Standard keywords - add to appropriate rules")
        lines.append("// ------------------------------------------------")
        for kw_data in sorted(by_handling["kw"], key=lambda x: x["keyword"]):
            kw = kw_data["keyword"]
            lines.append(f"kw('{kw}'),  // from {kw_data.get('source', 'unknown')}")
        lines.append("")

    # choice() operators
    if by_handling["choice"]:
        lines.append("// Operators - use choice() pattern, NOT kw()")
        lines.append("// ------------------------------------------------")
        for kw_data in sorted(by_handling["choice"], key=lambda x: x["keyword"]):
            kw = kw_data["keyword"]
            lines.append(f"choice('{kw}', '{kw.upper()}', '{kw.title()}'),  // operator")
        lines.append("")

    # kw_with_eq() keywords
    if by_handling["kw_with_eq"]:
        lines.append("// Contextual keywords - use kw_with_eq() pattern")
        lines.append("// ------------------------------------------------")
        for kw_data in sorted(by_handling["kw_with_eq"], key=lambda x: x["keyword"]):
            kw = kw_data["keyword"]
            lines.append(f"kw_with_eq('{kw}'),  // property=value disambiguation")
        lines.append("")

    # Literal exceptions
    if by_handling["literal"]:
        lines.append("// Literal exceptions - kw() causes conflicts")
        lines.append("// ------------------------------------------------")
        for kw_data in sorted(by_handling["literal"], key=lambda x: x["keyword"]):
            kw = kw_data["keyword"]
            variations = ", ".join([f"'{kw}'", f"'{kw.upper()}'", f"'{kw.title()}'"])
            lines.append(f"choice({variations}),  // literal exception")
        lines.append("")

    return "\n".join(lines)


def save_report(report: str) -> Path:
    """Save markdown report."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "comparison_report.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Saved report to {output_file}")
    return output_file


def save_code_snippets(code: str) -> Path:
    """Save code snippets."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "new_keywords_template.js"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"Saved code snippets to {output_file}")
    return output_file


if __name__ == "__main__":
    import sys

    generate_code = "--generate-code" in sys.argv

    data = load_comparison_results()

    # Always generate the report
    report = generate_markdown_report(data)
    save_report(report)

    # Optionally generate code snippets
    if generate_code:
        code = generate_code_snippets(data)
        save_code_snippets(code)
