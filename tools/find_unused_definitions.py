#!/usr/bin/env python3
"""
Tree-sitter Grammar Definition Analyzer

Consolidated tool for finding unused, low-usage, and orphan definitions in tree-sitter grammars.
Combines functionality of find_orphans.py and find_unused_simple.py with improvements:
- Built-in exclusion list for known special-purpose rules
- Optimized output for use as input to other tasks
- Comprehensive analysis including test file coverage
- Machine-readable and human-readable output formats

Run from the repository root — grammar.js and test/corpus/ are read relative to
the working directory.

KNOWN LIMITATION: the scan is only partly comment-aware. A trailing `// …`
comment is stripped from a rule's own definition line, but nowhere else: a
`$.rule` mentioned inside a `/* … */` block comment, or in a trailing `//`
comment on a continuation line, still counts as a reference and can therefore
hide a genuine orphan. Both holes pre-date the definition-line scan and neither
is currently triggered by grammar.js.

Usage:
    python tools/find_unused_definitions.py [--json] [--verbose] [--threshold N]
"""

import re
import sys
import json
import argparse
from collections import defaultdict
from pathlib import Path


# A quoted string, or a `//` that is therefore outside one. Alternating them in a
# single pattern means a `//` inside a literal is consumed as part of the string
# and can never be mistaken for a comment — grammar.js really does contain
# `comment: $ => token(seq('//', /[^\n]*/))`, which a naive `//.*$` strip would
# truncate.
_LINE_COMMENT_SCAN = re.compile(r"""('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")|//""")


def _strip_line_comment(line):
    """Return `line` with any trailing `//` comment removed."""
    for match in _LINE_COMMENT_SCAN.finditer(line):
        if match.group(1) is None:      # matched `//`, not a quoted string
            return line[:match.start()]
    return line


class GrammarAnalyzer:
    def __init__(self, grammar_content):
        self.content = grammar_content
        self.lines = grammar_content.split('\n')
        self.defined_rules = {}
        self.referenced_rules = defaultdict(list)
        self.test_references = defaultdict(int)
        
        # Known special-purpose rules that are intentionally exclusive
        self.exclusion_list = {
            # Tree-sitter special top-level properties
            'word', 'conflicts', 'extras', 'externals', 'inline', 
            'supertypes', 'precedences',
            
            # Entry points
            'source_file', 'program', 'module',
            
            # Tree-sitter built-ins
            'MISSING', 'ERROR', 'IMMEDIATE_TOKEN', 'PREC_DYNAMIC',
            '_start', '_end', '_newline', '_indent', '_dedent',
            
            # AL-specific entry points and special rules
            'application_object_declaration',  # Root for all AL objects
            
            # Template patterns that might be used via aliases or indirection
            '_string_value_template',  # Template for string value patterns
            '_layout_modification_template',  # Template for layout modifications
            '_identifier_choice_list',  # Template for identifier lists
            
            # Add more known exclusive rules based on your grammar
            # These are rules that are meant to be used in specific contexts only
        }
        
    def find_rule_definitions(self):
        """Find all rule definitions in the grammar."""
        # Pattern for rule definitions: rule_name: $ => ...
        definition_pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*\$\s*=>'
        
        for line_num, line in enumerate(self.lines, 1):
            # Skip comments
            if line.strip().startswith('//'):
                continue
                
            match = re.match(definition_pattern, line)
            if match:
                rule_name = match.group(1)
                self.defined_rules[rule_name] = {
                    'line': line_num,
                    'content': line.strip(),
                    'usage_count': 0,
                    'test_count': 0,
                    'references': []
                }
        
    def find_rule_references(self):
        """Find all rule references in the grammar."""
        for line_num, line in enumerate(self.lines, 1):
            # Skip comments
            if line.strip().startswith('//'):
                continue

            # Pattern 3: a rule definition line carries references on its own
            # right-hand side whenever the whole body fits on one line:
            #     alias_rule:      $ => $._other_rule,
            #     break_statement: $ => prec(13, $.break_keyword),
            # Scanning starts just past the `$ =>` so the rule's own name on the
            # left is never counted as a reference to itself. Only the explicit
            # `$.name` form is collected here; the bare-identifier sweep
            # (Pattern 2 below) is meaningful only inside argument lists.
            #
            # Previously only the bare `$ => $.other` shape was recognised and
            # every other definition line was skipped wholesale, so any rule
            # whose sole use was inside a wrapper such as prec() — break_keyword
            # is the real case — was reported as an orphan.
            definition_match = re.match(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*\$\s*=>', line)
            if definition_match:
                # A trailing `// …` comment is not code. Without this, a rule
                # mentioned only in a note such as
                #     stub: $ => 'a',  // TODO: wire up like $.ghost
                # counts as a reference and a real orphan stays hidden — the
                # false-negative direction, which is worse than the false
                # positive this pattern was added to fix.
                rhs = _strip_line_comment(line)[definition_match.end():]
                is_alias = re.match(r'^\s*\$\.([a-zA-Z_][a-zA-Z0-9_]*)\s*,?\s*$', rhs) is not None
                for match in re.finditer(r'\$\.([a-zA-Z_][a-zA-Z0-9_]*)', rhs):
                    rule_name = match.group(1)
                    self.referenced_rules[rule_name].append({
                        'line': line_num,
                        'context': line.strip(),
                        'type': 'alias_reference' if is_alias else 'direct_reference'
                    })
                    if rule_name in self.defined_rules:
                        self.defined_rules[rule_name]['usage_count'] += 1
                continue

            # Pattern 1: $.rule_name
            for match in re.finditer(r'\$\.([a-zA-Z_][a-zA-Z0-9_]*)', line):
                rule_name = match.group(1)
                self.referenced_rules[rule_name].append({
                    'line': line_num,
                    'context': line.strip(),
                    'type': 'direct_reference'
                })
                if rule_name in self.defined_rules:
                    self.defined_rules[rule_name]['usage_count'] += 1
                    
            # Pattern 2: rule in arrays/choices (not preceded by $ or .)
            # This catches patterns like choice('rule1', $.rule2, rule3)
            for match in re.finditer(r'(?<![a-zA-Z_$.])\b([a-zA-Z_][a-zA-Z0-9_]*)\b(?![a-zA-Z_:])', line):
                rule_name = match.group(1)
                # Check if this looks like a rule reference in a choice/array
                if rule_name in self.defined_rules:
                    # Look for context clues that this is a rule reference
                    before = line[:match.start()].rstrip()
                    after = line[match.end():].lstrip()
                    if (before.endswith(('(', ',', '[')) or 
                        after.startswith((')', ',', ']')) or
                        'choice' in before or 'seq' in before or 'repeat' in before):
                        self.referenced_rules[rule_name].append({
                            'line': line_num,
                            'context': line.strip(),
                            'type': 'implicit_reference'
                        })
                        self.defined_rules[rule_name]['usage_count'] += 1
            
    
    def analyze_test_files(self, test_dir='test/corpus'):
        """Analyze test files for rule usage."""
        test_path = Path(test_dir)
        if not test_path.exists():
            return
            
        for test_file in test_path.glob('*.txt'):
            try:
                content = test_file.read_text(encoding='utf-8')
                
                # Find rule references in parse trees
                for rule in self.defined_rules:
                    # Pattern for rules in parse trees: (rule_name
                    pattern = rf'\({rule}\b'
                    count = len(re.findall(pattern, content))
                    if count > 0:
                        self.test_references[rule] += count
                        self.defined_rules[rule]['test_count'] = count
                        
            except Exception as e:
                print(f"Warning: Could not read {test_file}: {e}", file=sys.stderr)
    
    def get_unused_rules(self, include_excluded=False):
        """Get rules with zero usage."""
        unused = []
        for rule_name, info in self.defined_rules.items():
            if not include_excluded and rule_name in self.exclusion_list:
                continue
            if info['usage_count'] == 0 and info['test_count'] == 0:
                unused.append({
                    'name': rule_name,
                    'line': info['line'],
                    'grammar_refs': 0,
                    'test_refs': 0
                })
        return sorted(unused, key=lambda x: x['line'])
    
    def get_low_usage_rules(self, threshold=2, include_excluded=False):
        """Get rules with usage below threshold."""
        low_usage = []
        for rule_name, info in self.defined_rules.items():
            if not include_excluded and rule_name in self.exclusion_list:
                continue
            total_usage = info['usage_count'] + info['test_count']
            if 0 < total_usage <= threshold:
                low_usage.append({
                    'name': rule_name,
                    'line': info['line'],
                    'grammar_refs': info['usage_count'],
                    'test_refs': info['test_count'],
                    'total_refs': total_usage
                })
        return sorted(low_usage, key=lambda x: (x['total_refs'], x['line']))
    
    def get_missing_definitions(self):
        """Find rules that are referenced but not defined."""
        missing = []
        for rule_name, references in self.referenced_rules.items():
            if rule_name not in self.defined_rules and rule_name not in self.exclusion_list:
                missing.append({
                    'name': rule_name,
                    'reference_count': len(references),
                    'first_reference': references[0] if references else None
                })
        return sorted(missing, key=lambda x: x['name'])
    
    def generate_report(self, format='text', verbose=False, threshold=2):
        """Generate analysis report in specified format."""
        unused = self.get_unused_rules()
        low_usage = self.get_low_usage_rules(threshold)
        missing = self.get_missing_definitions()
        
        if format == 'json':
            return self._generate_json_report(unused, low_usage, missing)
        else:
            return self._generate_text_report(unused, low_usage, missing, verbose, threshold)
    
    def _generate_json_report(self, unused, low_usage, missing):
        """Generate machine-readable JSON report."""
        report = {
            'summary': {
                'total_definitions': len(self.defined_rules),
                'total_references': len(self.referenced_rules),
                'unused_count': len(unused),
                'low_usage_count': len(low_usage),
                'missing_count': len(missing),
                'excluded_rules': sorted(list(self.exclusion_list))
            },
            'unused_rules': unused,
            'low_usage_rules': low_usage,
            'missing_definitions': missing
        }
        return json.dumps(report, indent=2)
    
    def _generate_text_report(self, unused, low_usage, missing, verbose, threshold):
        """Generate human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("TREE-SITTER GRAMMAR DEFINITION ANALYSIS")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        lines.append("SUMMARY:")
        lines.append(f"  Total rule definitions: {len(self.defined_rules)}")
        lines.append(f"  Unused rules: {len(unused)}")
        lines.append(f"  Low usage rules (<={threshold} refs): {len(low_usage)}")
        lines.append(f"  Missing definitions: {len(missing)}")
        lines.append(f"  Excluded from analysis: {len(self.exclusion_list)} special rules")
        lines.append("")
        
        # Unused rules
        if unused:
            lines.append("UNUSED RULES (0 references):")
            lines.append("-" * 50)
            for rule in unused[:30]:  # Limit output
                lines.append(f"  {rule['name']} (line {rule['line']})")
            if len(unused) > 30:
                lines.append(f"  ... and {len(unused) - 30} more")
            lines.append("")
        
        # Low usage rules
        if low_usage:
            lines.append(f"LOW USAGE RULES (1-{threshold} references):")
            lines.append("-" * 50)
            for rule in low_usage[:20]:  # Limit output
                refs = f"grammar: {rule['grammar_refs']}, tests: {rule['test_refs']}"
                lines.append(f"  {rule['name']} ({refs}) - line {rule['line']}")
            if len(low_usage) > 20:
                lines.append(f"  ... and {len(low_usage) - 20} more")
            lines.append("")
        
        # Missing definitions
        if missing:
            lines.append("MISSING DEFINITIONS:")
            lines.append("-" * 50)
            for miss in missing[:10]:
                lines.append(f"  {miss['name']} ({miss['reference_count']} references)")
                if verbose and miss['first_reference']:
                    ref = miss['first_reference']
                    lines.append(f"    First ref at line {ref['line']}: {ref['context'][:60]}...")
            if len(missing) > 10:
                lines.append(f"  ... and {len(missing) - 10} more")
            lines.append("")
        
        # Actionable items for task input
        if unused or low_usage:
            lines.append("ACTIONABLE ITEMS FOR CLEANUP:")
            lines.append("-" * 50)
            lines.append("Consider reviewing these definitions:")
            
            # Combine unused and low usage for actionable list
            actionable = []
            for rule in unused:
                actionable.append(f"{rule['name']}:unused")
            for rule in low_usage:
                actionable.append(f"{rule['name']}:low-usage-{rule['total_refs']}")
            
            # Output in a format easy to parse
            for item in actionable[:50]:
                lines.append(f"  - {item}")
            if len(actionable) > 50:
                lines.append(f"  ... and {len(actionable) - 50} more")
            lines.append("")
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze tree-sitter grammar for unused and low-usage definitions'
    )
    parser.add_argument(
        'grammar_file', nargs='?', default='grammar.js',
        help='Path to grammar.js file (default: grammar.js)'
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Output report in JSON format'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Include detailed information in report'
    )
    parser.add_argument(
        '--threshold', '-t', type=int, default=2,
        help='Usage threshold for low-usage detection (default: 2)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Write report to file'
    )
    parser.add_argument(
        '--include-excluded', action='store_true',
        help='Include normally excluded rules in analysis'
    )
    
    args = parser.parse_args()
    
    # Read grammar file
    grammar_path = Path(args.grammar_file)
    if not grammar_path.exists():
        print(f"Error: Grammar file '{grammar_path}' not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        grammar_content = grammar_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading grammar file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Analyze
    analyzer = GrammarAnalyzer(grammar_content)
    analyzer.find_rule_definitions()
    analyzer.find_rule_references()
    analyzer.analyze_test_files()
    
    # Generate report
    format_type = 'json' if args.json else 'text'
    report = analyzer.generate_report(
        format=format_type,
        verbose=args.verbose,
        threshold=args.threshold
    )
    
    # Output
    if args.output:
        try:
            Path(args.output).write_text(report, encoding='utf-8')
            print(f"Report written to {args.output}")
        except Exception as e:
            print(f"Error writing report: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(report)
    
    # Always save a detailed JSON report for programmatic use
    if not args.json:
        json_report = analyzer.generate_report(format='json', threshold=args.threshold)
        json_path = grammar_path.parent / 'grammar_analysis.json'
        try:
            json_path.write_text(json_report, encoding='utf-8')
            print(f"\nDetailed JSON report saved to {json_path}")
        except Exception:
            pass  # Silent fail for JSON backup


if __name__ == '__main__':
    main()
