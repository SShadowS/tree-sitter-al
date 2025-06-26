# AL Parser Preprocessor Remodeling Plan

This document outlines a comprehensive plan to eliminate the known preprocessor limitations in the tree-sitter-al parser. The goal is to enable parsing of AL code where preprocessor directives (#if, #else, #endif) split syntactic constructs.

## Current Limitations

The parser currently fails to handle these 6 preprocessor-related patterns:

1. **Conditional Object Declarations**: Objects declared within preprocessor conditionals
   ```al
   #if not CLEAN24
   codeunit 139754 "Test" implements "Interface1", "Interface2"
   #else  
   codeunit 139754 "Test" implements "Interface2"
   #endif
   ```

2. **Pragmas Before Namespace**: Pragma directives appearing before namespace declarations
   ```al
   #pragma warning disable AS0035
   namespace Microsoft.EServices.EDocumentConnector.Avalara;
   ```

3. **Mixed Var/Procedure Sections**: Var sections and procedures within same preprocessor block
   ```al
   #if not CLEAN25  
   protected var
       Item: Record Item;
   
   procedure CalcPrice()
   begin
   end;
   #endif
   ```

4. **Split Procedure Headers**: Return type syntax split by preprocessor
   ```al
   #if not CLEAN26
   local procedure GetPageID(RecRef: RecordRef) Result: Integer
   #else  
   local procedure GetPageID(RecRef: RecordRef): Integer
   #endif
   ```

5. **Complex Trigger Preprocessor**: Var declarations inside triggers with preprocessor
   ```al
   trigger OnInsert()
   #if not CLEAN24
   var
       NoSeriesManagement: Codeunit NoSeriesManagement;
   #endif
   begin
   ```

6. **Split Implements Clause**: Similar to pattern 1, preprocessor splitting implements list

## Architectural Solution

### Phase 1: External Scanner Implementation

Create an external scanner to handle preprocessor directives with full context awareness:

#### 1.1 Scanner Architecture
- **File**: Create `src/scanner.c`
- **Purpose**: Track preprocessor state and inject synthetic tokens
- **Key Features**:
  - Maintain preprocessor condition stack
  - Track active/inactive code regions
  - Generate synthetic tokens for split constructs

#### 1.2 Token Types
```c
enum TokenType {
  PREPROC_ACTIVE_REGION_START,
  PREPROC_ACTIVE_REGION_END,
  PREPROC_INACTIVE_REGION_START,
  PREPROC_INACTIVE_REGION_END,
  PREPROC_SPLIT_MARKER,
  PREPROC_CONTINUATION_MARKER,
  ERROR_SENTINEL
};
```

#### 1.3 Scanner State
```c
typedef struct {
  Array(bool) condition_stack;      // Track nested #if conditions
  bool in_split_construct;          // Detect split syntactic constructs
  enum SplitType current_split;     // Type of construct being split
  uint32_t split_start_line;        // Line where split began
} Scanner;
```

### Phase 2: Grammar Modifications

#### 2.1 Add External Tokens
```javascript
externals: $ => [
  $.preproc_active_region_start,
  $.preproc_active_region_end,
  $.preproc_inactive_region_start,
  $.preproc_inactive_region_end,
  $.preproc_split_marker,
  $.preproc_continuation_marker,
  $.error_sentinel
],
```

#### 2.2 Create Alternative Parse Paths

For each construct that can be split by preprocessor:

```javascript
// Example: Procedure declaration with optional split
procedure_declaration: $ => choice(
  // Normal procedure
  seq(
    optional($.attribute_list),
    optional($._visibility_modifier),
    choice('procedure', 'trigger'),
    field('name', $.identifier),
    '(',
    optional($.parameter_list),
    ')',
    choice(
      seq(':', field('return_type', $._type)),          // Modern syntax
      seq('Result', ':', field('return_type', $._type)) // Legacy syntax
    )
  ),
  
  // Preprocessor-split procedure
  seq(
    optional($.attribute_list),
    optional($._visibility_modifier),
    choice('procedure', 'trigger'),
    field('name', $.identifier),
    '(',
    optional($.parameter_list),
    ')',
    $.preproc_split_marker,
    choice(
      seq($.preproc_continuation_marker, ':', field('return_type', $._type)),
      seq($.preproc_continuation_marker, 'Result', ':', field('return_type', $._type))
    )
  )
),
```

#### 2.3 Conditional Parse Rules

Create conditional versions of major constructs:

```javascript
// Object declaration that can be inside preprocessor
_conditional_object: $ => seq(
  $.preproc_active_region_start,
  $._object,
  $.preproc_active_region_end
),

// Source file that can start with pragmas
source_file: $ => choice(
  // Standard structure
  seq(
    optional($.namespace_declaration),
    repeat(choice($.using_statement, $.preproc_conditional_using)),
    repeat(choice($._object, $.pragma))
  ),
  
  // Pragma-first structure
  seq(
    repeat1($.pragma),
    optional($.namespace_declaration),
    repeat(choice($.using_statement, $.preproc_conditional_using)),
    repeat(choice($._object, $.pragma))
  ),
  
  // Preprocessor-wrapped source
  $.preproc_conditional_source
),
```

### Phase 3: Scanner Logic Implementation

#### 3.1 Preprocessor Tracking
```c
bool scan_preprocessor_directive(Scanner *scanner, TSLexer *lexer) {
  // Detect #if, #else, #endif
  // Update condition stack
  // Determine if we're in active or inactive region
  // Check for split constructs
}
```

#### 3.2 Split Detection Heuristics
```c
bool detect_split_construct(Scanner *scanner, TSLexer *lexer) {
  // Look ahead for patterns that indicate a split:
  // - "procedure" followed by #if
  // - ")" followed by #if before ":" or "Result"
  // - "implements" followed by #if
  // - "var" inside trigger followed by #if
}
```

#### 3.3 Token Generation
```c
bool tree_sitter_al_external_scanner_scan(
  void *payload,
  TSLexer *lexer,
  const bool *valid_symbols
) {
  Scanner *scanner = (Scanner *)payload;
  
  // Handle error recovery
  if (valid_symbols[ERROR_SENTINEL]) {
    return false;
  }
  
  // Check for preprocessor directives
  if (lexer->lookahead == '#') {
    return scan_preprocessor_directive(scanner, lexer);
  }
  
  // Generate appropriate tokens based on state
  if (scanner->in_split_construct) {
    return generate_split_tokens(scanner, lexer, valid_symbols);
  }
  
  return false;
}
```

### Phase 4: Alternative Approaches

#### 4.1 GLR (Generalized LR) Parser Mode
- Enable GLR parsing to handle ambiguities
- Allow multiple parse paths for preprocessor-split constructs
- Merge paths post-parsing based on active preprocessor conditions

#### 4.2 Two-Pass Parsing
- First pass: Identify preprocessor structure and active regions
- Second pass: Parse with preprocessor-aware grammar

#### 4.3 Preprocessing Transform
- Add optional preprocessing step before parsing
- Transform split constructs into parseable forms
- Maintain source mapping for accurate positions

### Phase 5: Implementation Strategy

#### 5.1 Incremental Development
1. **Stage 1**: Implement external scanner infrastructure
2. **Stage 2**: Handle pragmas before namespace (simplest case)
3. **Stage 3**: Handle split procedure headers
4. **Stage 4**: Handle conditional object declarations
5. **Stage 5**: Handle complex nested cases

#### 5.2 Testing Strategy
- Create comprehensive test suite for each pattern
- Test nested preprocessor conditions
- Test error recovery with malformed preprocessor
- Benchmark performance impact

#### 5.3 Backwards Compatibility
- Ensure existing code continues to parse correctly
- Make preprocessor handling optional via feature flag
- Provide migration guide for grammar consumers

## Risk Mitigation

### Technical Risks
1. **Performance Impact**: External scanner overhead
   - Mitigation: Optimize scanner with caching and early exits
   
2. **Complexity**: Grammar becomes more complex
   - Mitigation: Clear documentation and examples
   
3. **Incremental Parsing**: May break with synthetic tokens
   - Mitigation: Careful token boundary management

### Implementation Risks
1. **Breaking Changes**: Existing parsers may fail
   - Mitigation: Version the changes, provide compatibility mode
   
2. **Maintenance Burden**: More code to maintain
   - Mitigation: Comprehensive tests and documentation

## Success Criteria

1. All 6 known limitation tests pass without ERROR nodes
2. No regression in existing tests
3. Performance degradation < 10%
4. Clean integration with tree-sitter ecosystem
5. Clear documentation for maintainers

## Timeline Estimate

- **Phase 1**: 2-3 weeks (External scanner setup)
- **Phase 2**: 1-2 weeks (Grammar modifications)
- **Phase 3**: 3-4 weeks (Scanner logic)
- **Phase 4**: 2-3 weeks (Testing and optimization)
- **Total**: 8-12 weeks for full implementation

## Conclusion

This remodeling plan provides a path to eliminate the preprocessor limitations through a combination of external scanner technology and grammar enhancements. The approach balances completeness with maintainability, ensuring the parser can handle real-world AL code while remaining performant and understandable.

The key insight is that preprocessor directives create a parallel structure to the main syntax tree, and by tracking this structure explicitly through an external scanner, we can guide the parser to handle split constructs gracefully.