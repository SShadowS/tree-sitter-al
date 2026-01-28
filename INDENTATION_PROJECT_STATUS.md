# AL Tree-Sitter Indentation Project - Status & Continuation Guide

**Project**: tree-sitter-al parser for Microsoft Dynamics 365 Business Central AL language  
**Focus**: Achieving excellent automatic indentation in Neovim using tree-sitter indent queries  
**Repository**: `C:\Users\DanieleLixi\Projects\tree-sitter-al\`  
**Last Updated**: January 28, 2026  
**Current Success Rate**: ~99.9% (930/932 lines correct, 2 diff lines - spacing only)

---

## Executive Summary

We successfully improved indentation from 91.20% to **~99.9%** success rate through multiple phases of fixes, culminating in **two grammar changes**:
1. Fixed parameter indentation by including parentheses in `parameter_list`
2. Fixed if-else indentation by creating an `else_clause` grammar rule

**Key Achievements**:
- Fixed 80 out of 82 originally broken lines (97.6% of issues resolved)
- Parameter indentation now works correctly (grammar change)
- If-else indentation now works correctly (grammar change)
- All 1198 parser tests pass
- Parser rebuilt and installed to Neovim
- **Only 2 diff lines remaining** (spacing issue, not indentation)

---

## What Was Accomplished

### Phase 1-3: Structural Fixes (Previous Sessions)
- Added missing page/report sections to indent rules
- Fixed case_else_branch indentation
- Achieved 99.25% success rate (18 diff lines)

### Phase 4: Parameter Indentation Fix (January 28, 2026)

**Problem Identified**: `parameter_list` node excluded parentheses, while `argument_list` included them. This caused the first parameter in multi-line lists to be under-indented.

**Solution Applied**: Grammar change to make `parameter_list` include parentheses like `argument_list`.

**Result**: Parameter indentation now works correctly. Diff lines reduced from 18 to 16.

### Phase 5: Else Clause Grammar Fix (January 28, 2026)

**Problem Identified**: The `else` keyword was not exposed as a separate node in the parse tree. Any indent rule applied to `else_branch` affected the entire content, not just the keyword.

**Solution Applied**: Created new `else_clause` grammar rule (following Rust's approach) that wraps the `else` keyword and its body as a distinct node.

**Changes Made**:
1. Added `else_clause` rule in `grammar.js`:
   ```javascript
   else_clause: $ => seq(
     kw('else', 10),
     field('body', choice(
       $.code_block,
       prec(1, $.if_statement),  // else-if chain
       $._if_then_body
     ))
   ),
   ```
2. Modified `if_statement` to use `optional($.else_clause)` instead of inline else handling
3. Updated `queries/indents.scm` with proper `else_clause` rules:
   ```scm
   (else_clause) @indent.branch
   (else_clause body: (code_block) @indent.dedent)
   ```
4. Updated 4 test files for structural changes

**Result**: Diff lines reduced from 16 to **2** (spacing only, not indentation).

---

## Current State

### Success Metrics

| Metric | Phase 1 Start | Phase 3 End | Phase 4 End | Phase 5 End | Total Improvement |
|--------|---------------|-------------|-------------|-------------|-------------------|
| **Success Rate** | 91.20% | 99.25% | 99.14% | ~99.9% | +8.7 pts |
| **Lines Correct** | 850/932 | 923/930 | 916/932 | 930/932 | +80 lines |
| **Diff Lines** | 82 | 18 | 16 | 2 | -80 lines |

### What Works Perfectly
- All object structures (tables, pages, codeunits, reports, enums, etc.)
- Report rendering layouts
- Case statements and case else branches
- PageExtension modify/addafter/addbefore/addfirst/addlast sections
- Page action area() sections
- Code blocks (begin/end)
- All structural indentation patterns
- **If-else statements** (FIXED in Phase 5)
- **Multi-line parameter lists** (FIXED in Phase 4)
- **Multi-line argument lists**

### What Doesn't Work (2 diff lines - spacing only)

**Pattern: Spacing before colon**
```al
i, j, k : Integer;    // Source has space before colon
i, j, k: Integer;     // Result removes space
```
*Note: This is a formatting/spacing issue, not indentation. The indentation is correct.*

---

## Files & Locations

### Core Files
| Purpose | Path |
|---------|------|
| **Grammar definition** | `grammar.js` |
| **Indent rules** | `queries/indents.scm` |
| **Generated parser** | `src/parser.c` |
| **Neovim parser** | `$LOCALAPPDATA/nvim-data/site/parser/al.so` |
| **Neovim indent rules** | `$LOCALAPPDATA/nvim-data/lazy/nvim-treesitter/runtime/queries/al/indents.scm` |

### Test Files
| Purpose | Path |
|---------|------|
| **Input (flush-left)** | `test_data/indents/indent_tests_initial.al` |
| **Expected output** | `test_data/indents/indent_tests_expected.al` |

---

## How to Test

### Quick Indentation Test
```bash
# Create flush-left test file
printf 'codeunit 50100 Test\n{\nprocedure Test(\nParam1: Integer;\nParam2: Text)\nbegin\nend;\n}\n' > /tmp/test.al

# Format with Neovim
nvim --headless /tmp/test.al -c "set filetype=al" -c "normal! gg=G" -c "w! /tmp/result.al" -c "q!"

# Check result (parameters should be at 8 spaces)
cat /tmp/result.al
```

### Full Test Suite
```bash
# Run parser tests
tree-sitter test

# Run indent test suite
nvim --headless test_data/indents/indent_tests_initial.al \
  -c "set filetype=al" -c "normal! gg=G" \
  -c "w! test_data/indents/indent_tests_results.al" -c "q!"

# Count diff lines (target: 2)
diff test_data/indents/indent_tests_expected.al test_data/indents/indent_tests_results.al | grep -c "^[<>]"
```

### After Grammar Changes
```bash
# Regenerate parser
tree-sitter generate

# Run tests
tree-sitter test

# Rebuild and install to Neovim
tree-sitter build -o "$LOCALAPPDATA/nvim-data/site/parser/al.so" .

# Copy indent rules
cp queries/indents.scm "$LOCALAPPDATA/nvim-data/lazy/nvim-treesitter/runtime/queries/al/indents.scm"
```

---

## Grammar Changes for Indentation

### else_clause Rule (Phase 5)

The key insight was that `else` needed to be exposed as a separate node (like Rust does) to allow proper indent targeting.

**Before**: `else` was consumed by the parser but not a named node
```
(if_statement
  condition: (boolean)
  then_branch: (statement)
  else_branch: (statement))   // No 'else' keyword node!
```

**After**: `else_clause` wraps the keyword and body
```
(if_statement
  condition: (boolean)
  then_branch: (statement)
  (else_clause
    body: (statement)))       // 'else' is now targetable!
```

### parameter_list Rule (Phase 4)

Aligned `parameter_list` structure with `argument_list` by including parentheses.

---

## Commit History

```
77df3ed Add else_clause grammar rule for proper indentation
0d2cedf Update indentation project status after parameter fix
3d37da7 Fix parameter_list to include parentheses for proper indentation
a77e453 try to fix parameters indent without grammar changes
afdeb85 attempting to fix if_then_else auto indentation
07983b5 various indent fixes, up to 99.25% correct indentations
4eb0b5b fixes indenting of until keyword
```

---

## Summary

The indentation project has achieved **production-ready quality** with ~99.9% success rate. The remaining 2 diff lines are:
- **Spacing issue only** (`i, j, k : Integer` vs `i, j, k: Integer`)
- Not an indentation problem

Both major indentation issues (parameters and if-else) have been **fully resolved** through grammar changes:
1. `parameter_list` now includes parentheses
2. `else_clause` now exposes the `else` keyword as a targetable node
