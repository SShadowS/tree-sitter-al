#!/usr/bin/env python3
"""CLI entry point for keyword synchronization tools."""

import argparse
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from extract_vscode_keywords import extract_vscode_keywords, save_results as save_vscode
from extract_grammar_keywords import extract_grammar_keywords, save_results as save_grammar
from compare_keywords import compare_keywords, save_results as save_comparison, print_summary
from generate_report import (
    load_comparison_results,
    generate_markdown_report,
    generate_code_snippets,
    save_report,
    save_code_snippets,
)
from config import OUTPUT_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Synchronize keywords between VS Code AL extension and tree-sitter grammar"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Skip extraction, only generate report from existing data",
    )
    parser.add_argument(
        "--generate-code",
        action="store_true",
        help="Generate JavaScript code snippets for missing keywords",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress detailed output",
    )

    args = parser.parse_args()

    try:
        if not args.report_only:
            # Step 1: Extract VS Code keywords
            if not args.quiet:
                print("\n=== Step 1: Extracting VS Code keywords ===")
            vscode_data = extract_vscode_keywords()
            if not vscode_data:
                print("Error: Failed to extract VS Code keywords")
                return 1
            save_vscode(vscode_data)

            # Step 2: Extract grammar keywords
            if not args.quiet:
                print("\n=== Step 2: Extracting grammar keywords ===")
            grammar_data = extract_grammar_keywords()
            if not grammar_data:
                print("Error: Failed to extract grammar keywords")
                return 1
            save_grammar(grammar_data)

            # Step 3: Compare
            if not args.quiet:
                print("\n=== Step 3: Comparing keywords ===")
            comparison_data = compare_keywords()
            save_comparison(comparison_data)

            if not args.quiet:
                print_summary(comparison_data)
        else:
            # Load existing comparison data
            comparison_data = load_comparison_results()
            if not args.quiet:
                print_summary(comparison_data)

        # Step 4: Generate report
        if not args.quiet:
            print("\n=== Step 4: Generating report ===")
        report = generate_markdown_report(comparison_data)
        save_report(report)

        # Step 5: Optionally generate code snippets
        if args.generate_code:
            if not args.quiet:
                print("\n=== Step 5: Generating code snippets ===")
            code = generate_code_snippets(comparison_data)
            save_code_snippets(code)

        if not args.quiet:
            print("\n=== Done ===")
            print(f"Output files in: {OUTPUT_DIR}")
            print("  - vscode_keywords.json")
            print("  - grammar_keywords.json")
            print("  - comparison_results.json")
            print("  - comparison_report.md")
            if args.generate_code:
                print("  - new_keywords_template.js")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
