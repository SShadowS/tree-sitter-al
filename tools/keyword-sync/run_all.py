#!/usr/bin/env python3
"""CLI entry point for keyword synchronization tools.

Runs all extraction and comparison steps:
1. Extract keywords from VS Code tmlanguage
2. Extract keywords from grammar.js
3. Compare keywords
4. Extract snippets data (properties, triggers, enums)
5. Compare properties
6. Compare triggers
7. Generate unified report
"""

import argparse
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from extract_vscode_keywords import extract_vscode_keywords, save_results as save_vscode
from extract_grammar_keywords import extract_grammar_keywords, save_results as save_grammar
from compare_keywords import compare_keywords, save_results as save_comparison, print_summary
from extract_snippets import extract_snippets, save_results as save_snippets
from compare_properties import compare_properties, save_results as save_props, print_summary as print_props_summary
from compare_triggers import compare_triggers, save_results as save_triggers, print_summary as print_triggers_summary
from generate_report import (
    load_comparison_results,
    generate_markdown_report,
    generate_code_snippets,
    save_report,
    save_code_snippets,
)
from generate_full_report import load_all_data, generate_markdown_report as generate_full_report, save_report as save_full_report
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
        "--keywords-only",
        action="store_true",
        help="Only run keyword extraction/comparison (skip snippets)",
    )
    parser.add_argument(
        "--snippets-only",
        action="store_true",
        help="Only run snippet extraction/comparison (skip keywords)",
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

    run_keywords = not args.snippets_only
    run_snippets = not args.keywords_only

    try:
        step = 1

        if not args.report_only:
            # ===== KEYWORD EXTRACTION =====
            if run_keywords:
                # Step 1: Extract VS Code keywords
                if not args.quiet:
                    print(f"\n=== Step {step}: Extracting VS Code keywords ===")
                step += 1
                vscode_data = extract_vscode_keywords()
                if not vscode_data:
                    print("Error: Failed to extract VS Code keywords")
                    return 1
                save_vscode(vscode_data)

                # Step 2: Extract grammar keywords
                if not args.quiet:
                    print(f"\n=== Step {step}: Extracting grammar keywords ===")
                step += 1
                grammar_data = extract_grammar_keywords()
                if not grammar_data:
                    print("Error: Failed to extract grammar keywords")
                    return 1
                save_grammar(grammar_data)

                # Step 3: Compare keywords
                if not args.quiet:
                    print(f"\n=== Step {step}: Comparing keywords ===")
                step += 1
                comparison_data = compare_keywords()
                save_comparison(comparison_data)

                if not args.quiet:
                    print_summary(comparison_data)

            # ===== SNIPPET EXTRACTION =====
            if run_snippets:
                # Step 4: Extract snippets data
                if not args.quiet:
                    print(f"\n=== Step {step}: Extracting snippets data ===")
                step += 1
                snippets_data = extract_snippets()
                if not snippets_data:
                    print("Error: Failed to extract snippets data")
                    return 1
                save_snippets(snippets_data)

                # Step 5: Compare properties
                if not args.quiet:
                    print(f"\n=== Step {step}: Comparing properties ===")
                step += 1
                props_data = compare_properties()
                save_props(props_data)

                if not args.quiet:
                    print_props_summary(props_data)

                # Step 6: Compare triggers
                if not args.quiet:
                    print(f"\n=== Step {step}: Comparing triggers ===")
                step += 1
                triggers_data = compare_triggers()
                save_triggers(triggers_data)

                if not args.quiet:
                    print_triggers_summary(triggers_data)

        # ===== REPORT GENERATION =====

        # Step 7: Generate keyword report (legacy)
        if run_keywords:
            if not args.quiet:
                print(f"\n=== Step {step}: Generating keyword report ===")
            step += 1

            if args.report_only:
                comparison_data = load_comparison_results()
                if not args.quiet:
                    print_summary(comparison_data)

            report = generate_markdown_report(comparison_data)
            save_report(report)

        # Step 8: Generate full unified report
        if not args.quiet:
            print(f"\n=== Step {step}: Generating full comparison report ===")
        step += 1
        all_data = load_all_data()
        full_report = generate_full_report(all_data)
        save_full_report(full_report)

        # Step 9: Optionally generate code snippets
        if args.generate_code and run_keywords:
            if not args.quiet:
                print(f"\n=== Step {step}: Generating code snippets ===")
            step += 1
            code = generate_code_snippets(comparison_data)
            save_code_snippets(code)

        # ===== SUMMARY =====
        if not args.quiet:
            print("\n=== Done ===")
            print(f"Output files in: {OUTPUT_DIR}")
            if run_keywords:
                print("  Keywords:")
                print("    - vscode_keywords.json")
                print("    - grammar_keywords.json")
                print("    - comparison_results.json")
                print("    - comparison_report.md")
            if run_snippets:
                print("  Snippets:")
                print("    - snippets_data.json")
                print("    - property_comparison.json")
                print("    - trigger_comparison.json")
            print("  Combined:")
            print("    - full_comparison_report.md")
            if args.generate_code:
                print("    - new_keywords_template.js")

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
