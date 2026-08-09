#!/usr/bin/env python3
"""
Grammar Health Check - Regression detection for tree-sitter-al grammar

Captures grammar metrics and compares to baseline to detect regressions.
Use --save-baseline to create/update the baseline after verified changes.
Use without arguments to check current state against baseline.

Run from the repository root — grammar.js and src/scanner.c are read relative to
the working directory.

Usage:
    python tools/check_grammar_health.py              # Check against baseline
    python tools/check_grammar_health.py --save-baseline  # Save current state as baseline
    python tools/check_grammar_health.py --json       # Output as JSON
    python tools/check_grammar_health.py --ci         # CI mode (exit code 1 on regression)
"""

import re
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Repository root, not tools/ — the baseline is a repo-level artifact and lived
# beside grammar.js before this script moved under tools/.
BASELINE_FILE = Path(__file__).resolve().parent.parent / '.grammar_baseline.json'

class GrammarHealthChecker:
    def __init__(self):
        self.metrics = {}
        self.issues = []

    def collect_metrics(self):
        """Collect all grammar health metrics."""
        self.metrics = {
            'timestamp': datetime.now().isoformat(),
            'rule_count': self._count_rules(),
            'conflict_count': self._count_conflicts(),
            'external_count': self._count_externals(),
            'test_results': self._run_tests(),
            'unused_rules': self._find_unused_rules(),
            'missing_definitions': self._find_missing_definitions(),
            'scanner_lines': self._count_scanner_lines(),
        }
        return self.metrics

    def _count_rules(self):
        """Count rule definitions in grammar.js."""
        try:
            content = Path('grammar.js').read_text(encoding='utf-8')
            # Pattern for rule definitions: rule_name: $ =>
            pattern = r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*:\s*\$\s*=>'
            return len(re.findall(pattern, content, re.MULTILINE))
        except Exception as e:
            self.issues.append(f"Could not count rules: {e}")
            return -1

    def _count_conflicts(self):
        """Count conflict declarations."""
        try:
            content = Path('grammar.js').read_text(encoding='utf-8')
            # Find conflicts array and count entries
            match = re.search(r'conflicts:\s*\$\s*=>\s*\[(.*?)\],\s*\n\s*externals:', content, re.DOTALL)
            if match:
                conflicts_content = match.group(1)
                # Count lines with [$. pattern
                return len(re.findall(r'\[\$\.', conflicts_content))
            return 0
        except Exception as e:
            self.issues.append(f"Could not count conflicts: {e}")
            return -1

    def _count_externals(self):
        """Count external scanner tokens."""
        try:
            content = Path('grammar.js').read_text(encoding='utf-8')
            match = re.search(r'externals:\s*\$\s*=>\s*\[(.*?)\],', content, re.DOTALL)
            if match:
                externals_content = match.group(1)
                return len(re.findall(r'\$\.[a-zA-Z_]+', externals_content))
            return 0
        except Exception as e:
            self.issues.append(f"Could not count externals: {e}")
            return -1

    def _count_scanner_lines(self):
        """Count lines in scanner.c."""
        try:
            scanner = Path('src/scanner.c')
            if scanner.exists():
                return len(scanner.read_text(encoding='utf-8').splitlines())
            return 0
        except Exception as e:
            self.issues.append(f"Could not count scanner lines: {e}")
            return -1

    def _run_tests(self):
        """Run tree-sitter test and capture results."""
        try:
            result = subprocess.run(
                ['tree-sitter', 'test'],
                capture_output=True,
                timeout=300
            )
            # Decode with utf-8 to properly handle checkmarks
            output = result.stdout.decode('utf-8', errors='replace') + result.stderr.decode('utf-8', errors='replace')

            # Strip ANSI color codes for reliable parsing
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_output = ansi_escape.sub('', output)

            # Parse test results
            failures = 0
            passes = 0

            # Look for failure count
            fail_match = re.search(r'(\d+)\s+failures?:', clean_output)
            if fail_match:
                failures = int(fail_match.group(1))

            # Count checkmarks for passes (both UTF-8 checkmark and numbered lines with checkmark)
            passes = clean_output.count('\u2713')  # ✓ character
            if passes == 0:
                # Fallback: count numbered test lines that passed
                passes = len(re.findall(r'^\s*\d+\.\s+\S', clean_output, re.MULTILINE)) - failures

            return {
                'passed': passes,
                'failed': failures,
                'total': passes + failures,
                'success': failures == 0
            }
        except subprocess.TimeoutExpired:
            self.issues.append("Test suite timed out")
            return {'passed': 0, 'failed': -1, 'total': 0, 'success': False}
        except Exception as e:
            self.issues.append(f"Could not run tests: {e}")
            return {'passed': 0, 'failed': -1, 'total': 0, 'success': False}

    def _find_unused_rules(self):
        """Find unused rule definitions."""
        try:
            content = Path('grammar.js').read_text(encoding='utf-8')
            lines = content.split('\n')

            # Find all rule definitions
            defined = set()
            definition_pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*\$\s*=>'
            for line in lines:
                match = re.match(definition_pattern, line)
                if match:
                    defined.add(match.group(1))

            # Find all rule references
            referenced = set()
            for line in lines:
                for match in re.finditer(r'\$\.([a-zA-Z_][a-zA-Z0-9_]*)', line):
                    referenced.add(match.group(1))

            # Exclude special rules
            special = {'word', 'conflicts', 'extras', 'externals', 'inline',
                      'supertypes', 'precedences', 'source_file'}

            unused = defined - referenced - special
            return sorted(list(unused))
        except Exception as e:
            self.issues.append(f"Could not find unused rules: {e}")
            return []

    def _find_missing_definitions(self):
        """Find referenced but undefined rules."""
        try:
            content = Path('grammar.js').read_text(encoding='utf-8')
            lines = content.split('\n')

            # Find all rule definitions
            defined = set()
            definition_pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*\$\s*=>'
            for line in lines:
                match = re.match(definition_pattern, line)
                if match:
                    defined.add(match.group(1))

            # Find all rule references
            referenced = set()
            for line in lines:
                # Skip comments
                if line.strip().startswith('//'):
                    continue
                for match in re.finditer(r'\$\.([a-zA-Z_][a-zA-Z0-9_]*)', line):
                    referenced.add(match.group(1))

            missing = referenced - defined
            return sorted(list(missing))
        except Exception as e:
            self.issues.append(f"Could not find missing definitions: {e}")
            return []

    def save_baseline(self):
        """Save current metrics as baseline."""
        self.collect_metrics()
        baseline = {
            'created': datetime.now().isoformat(),
            'metrics': self.metrics,
            'known_unused': self.metrics.get('unused_rules', []),
            'known_missing': self.metrics.get('missing_definitions', []),
        }
        BASELINE_FILE.write_text(json.dumps(baseline, indent=2), encoding='utf-8')
        return baseline

    def load_baseline(self):
        """Load baseline from file."""
        if not BASELINE_FILE.exists():
            return None
        try:
            return json.loads(BASELINE_FILE.read_text(encoding='utf-8'))
        except Exception:
            return None

    def compare_to_baseline(self, baseline):
        """Compare current metrics to baseline and identify regressions."""
        if not baseline:
            return {'has_baseline': False, 'regressions': [], 'improvements': []}

        current = self.metrics
        base = baseline['metrics']

        regressions = []
        improvements = []

        # Check test failures
        if current['test_results']['failed'] > base['test_results']['failed']:
            regressions.append({
                'type': 'test_failures',
                'message': f"Test failures increased: {base['test_results']['failed']} -> {current['test_results']['failed']}",
                'severity': 'critical'
            })
        elif current['test_results']['failed'] < base['test_results']['failed']:
            improvements.append({
                'type': 'test_failures',
                'message': f"Test failures decreased: {base['test_results']['failed']} -> {current['test_results']['failed']}"
            })

        # Check test count (should not decrease)
        if current['test_results']['total'] < base['test_results']['total']:
            regressions.append({
                'type': 'test_count',
                'message': f"Total tests decreased: {base['test_results']['total']} -> {current['test_results']['total']}",
                'severity': 'warning'
            })

        # Check conflict count (should not increase without reason)
        if current['conflict_count'] > base['conflict_count']:
            regressions.append({
                'type': 'conflicts',
                'message': f"Conflict count increased: {base['conflict_count']} -> {current['conflict_count']}",
                'severity': 'warning'
            })
        elif current['conflict_count'] < base['conflict_count']:
            improvements.append({
                'type': 'conflicts',
                'message': f"Conflict count decreased: {base['conflict_count']} -> {current['conflict_count']}"
            })

        # Check for new unused rules
        known_unused = set(baseline.get('known_unused', []))
        current_unused = set(current.get('unused_rules', []))
        new_unused = current_unused - known_unused
        if new_unused:
            regressions.append({
                'type': 'unused_rules',
                'message': f"New unused rules: {', '.join(sorted(new_unused))}",
                'severity': 'warning'
            })

        # Check for new missing definitions
        known_missing = set(baseline.get('known_missing', []))
        current_missing = set(current.get('missing_definitions', []))
        new_missing = current_missing - known_missing
        if new_missing:
            regressions.append({
                'type': 'missing_definitions',
                'message': f"New missing definitions: {', '.join(sorted(new_missing))}",
                'severity': 'error'
            })

        return {
            'has_baseline': True,
            'regressions': regressions,
            'improvements': improvements,
            'baseline_date': baseline.get('created', 'unknown')
        }

    def generate_report(self, comparison, format='text'):
        """Generate health check report."""
        if format == 'json':
            return json.dumps({
                'metrics': self.metrics,
                'comparison': comparison,
                'issues': self.issues
            }, indent=2)

        lines = []
        lines.append("=" * 70)
        lines.append("GRAMMAR HEALTH CHECK REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Current metrics
        lines.append("CURRENT METRICS:")
        lines.append(f"  Rules defined:     {self.metrics['rule_count']}")
        lines.append(f"  Conflicts:         {self.metrics['conflict_count']}")
        lines.append(f"  External tokens:   {self.metrics['external_count']}")
        lines.append(f"  Scanner lines:     {self.metrics['scanner_lines']}")
        lines.append(f"  Tests passed:      {self.metrics['test_results']['passed']}")
        lines.append(f"  Tests failed:      {self.metrics['test_results']['failed']}")
        lines.append(f"  Unused rules:      {len(self.metrics['unused_rules'])}")
        lines.append("")

        # Comparison
        if comparison['has_baseline']:
            lines.append(f"COMPARISON TO BASELINE ({comparison['baseline_date'][:10]}):")
            lines.append("-" * 50)

            if comparison['regressions']:
                lines.append("")
                lines.append("REGRESSIONS:")
                for reg in comparison['regressions']:
                    severity = reg['severity'].upper()
                    lines.append(f"  [{severity}] {reg['message']}")

            if comparison['improvements']:
                lines.append("")
                lines.append("IMPROVEMENTS:")
                for imp in comparison['improvements']:
                    lines.append(f"  [+] {imp['message']}")

            if not comparison['regressions'] and not comparison['improvements']:
                lines.append("  No changes from baseline")
        else:
            lines.append("NO BASELINE FOUND")
            lines.append("Run with --save-baseline to create one")

        lines.append("")

        # Status
        has_critical = any(r['severity'] == 'critical' for r in comparison.get('regressions', []))
        has_error = any(r['severity'] == 'error' for r in comparison.get('regressions', []))

        if not comparison['has_baseline']:
            # No baseline means nothing was actually compared -- this must never
            # read as a pass. .grammar_baseline.json is tracked in git, so its
            # absence in a real checkout means a broken checkout, not a first run.
            lines.append("STATUS: FAILED - No baseline found; run --save-baseline and commit .grammar_baseline.json")
        elif has_critical or has_error:
            lines.append("STATUS: FAILED - Critical or error regressions detected")
        elif comparison.get('regressions'):
            lines.append("STATUS: WARNING - Non-critical regressions detected")
        else:
            lines.append("STATUS: PASSED")

        lines.append("")
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Check grammar health and detect regressions')
    parser.add_argument('--save-baseline', action='store_true', help='Save current state as baseline')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--ci', action='store_true', help='CI mode - exit 1 on any regression')
    args = parser.parse_args()

    checker = GrammarHealthChecker()

    if args.save_baseline:
        baseline = checker.save_baseline()
        print(f"Baseline saved to {BASELINE_FILE}")
        print(f"  Rules: {baseline['metrics']['rule_count']}")
        print(f"  Conflicts: {baseline['metrics']['conflict_count']}")
        print(f"  Tests: {baseline['metrics']['test_results']['passed']} passed, {baseline['metrics']['test_results']['failed']} failed")
        print(f"  Unused rules: {len(baseline['known_unused'])}")
        return 0

    # Collect current metrics
    checker.collect_metrics()

    # Load and compare to baseline
    baseline = checker.load_baseline()
    comparison = checker.compare_to_baseline(baseline)

    # Generate report
    format_type = 'json' if args.json else 'text'
    report = checker.generate_report(comparison, format_type)
    print(report)

    # Exit code for CI
    if args.ci:
        has_critical = any(r['severity'] == 'critical' for r in comparison.get('regressions', []))
        has_error = any(r['severity'] == 'error' for r in comparison.get('regressions', []))
        # A missing baseline means the comparison never ran -- it is not a pass.
        # See STATUS logic in generate_report() for the same reasoning.
        no_baseline = not comparison.get('has_baseline', False)
        if has_critical or has_error or no_baseline:
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
