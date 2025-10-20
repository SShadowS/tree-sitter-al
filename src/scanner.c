#include "tree_sitter/parser.h"
#include "tree_sitter/alloc.h"
#include "tree_sitter/array.h"
#include <wctype.h>
#include <string.h>
#include <stdio.h>
#include <stdbool.h>

// ============================================================================
// DEBUG TOGGLE - Set to 1 to enable debug output, 0 to disable
// ============================================================================
#define SCANNER_DEBUG 0

// Token types enum matching the externals array order in grammar.js
enum TokenType {
    PREPROC_ACTIVE_REGION_START,      // 0
    PREPROC_ACTIVE_REGION_END,        // 1
    PREPROC_INACTIVE_REGION_START,    // 2
    PREPROC_INACTIVE_REGION_END,      // 3
    PREPROC_SPLIT_MARKER,             // 4 - Marks start of split procedure
    PREPROC_CONTINUATION_MARKER,      // 5
    ERROR_SENTINEL,                   // 6 - Error recovery token
    PREPROC_VAR_TERMINATOR,           // 7 - Detects var section terminators in preprocessor
    ATTRIBUTE_FOR_VARIABLE,           // 8 - Distinguishes [attr] for variable
    ATTRIBUTE_FOR_PROCEDURE           // 9 - Distinguishes [attr] for procedure
};

// Keywords that can terminate a var section
static const char* VAR_TERMINATORS[] = {
    "procedure", "trigger", "onrun",
    "table", "page", "codeunit", "report", 
    "query", "xmlport", "enum", "interface",
    "fields", "keys", "fieldgroups",
    NULL  // Sentinel
};

// Split types for tracking what construct is being split
typedef enum {
    SPLIT_NONE,
    SPLIT_PROCEDURE_HEADER,
    SPLIT_OBJECT_DECLARATION,
    SPLIT_VAR_SECTION,
    SPLIT_IMPLEMENTS_CLAUSE
} SplitType;

// Scanner state structure
typedef struct {
    Array(bool) condition_stack;      // Track nested #if conditions
    bool in_split_construct;          // Detect split syntactic constructs
    SplitType current_split;          // Type of construct being split
    uint32_t split_start_line;        // Line where split began
    bool last_was_pragma;             // Track if last token was pragma
} Scanner;

// Create scanner instance
void *tree_sitter_al_external_scanner_create() {
    Scanner *scanner = ts_calloc(1, sizeof(Scanner));
    array_init(&scanner->condition_stack);
    scanner->in_split_construct = false;
    scanner->current_split = SPLIT_NONE;
    scanner->split_start_line = 0;
    scanner->last_was_pragma = false;
    return scanner;
}

// Destroy scanner instance
void tree_sitter_al_external_scanner_destroy(void *payload) {
    Scanner *scanner = (Scanner *)payload;
    array_delete(&scanner->condition_stack);
    ts_free(scanner);
}

// Serialize scanner state
unsigned tree_sitter_al_external_scanner_serialize(
    void *payload,
    char *buffer
) {
    Scanner *scanner = (Scanner *)payload;
    size_t size = 0;
    
    // Serialize condition stack size
    uint32_t stack_size = scanner->condition_stack.size;
    if (size + sizeof(stack_size) <= TREE_SITTER_SERIALIZATION_BUFFER_SIZE) {
        memcpy(buffer + size, &stack_size, sizeof(stack_size));
        size += sizeof(stack_size);
    }
    
    // Serialize condition stack values
    for (uint32_t i = 0; i < stack_size && size < TREE_SITTER_SERIALIZATION_BUFFER_SIZE; i++) {
        buffer[size++] = scanner->condition_stack.contents[i] ? 1 : 0;
    }
    
    // Serialize other state
    if (size + sizeof(bool) * 2 + sizeof(SplitType) + sizeof(uint32_t) <= TREE_SITTER_SERIALIZATION_BUFFER_SIZE) {
        buffer[size++] = scanner->in_split_construct ? 1 : 0;
        buffer[size++] = scanner->last_was_pragma ? 1 : 0;
        memcpy(buffer + size, &scanner->current_split, sizeof(SplitType));
        size += sizeof(SplitType);
        memcpy(buffer + size, &scanner->split_start_line, sizeof(uint32_t));
        size += sizeof(uint32_t);
    }
    
    return size;
}

// Deserialize scanner state
void tree_sitter_al_external_scanner_deserialize(
    void *payload,
    const char *buffer,
    unsigned length
) {
    Scanner *scanner = (Scanner *)payload;
    array_clear(&scanner->condition_stack);
    
    if (length == 0) return;
    
    size_t size = 0;
    
    // Deserialize condition stack size
    uint32_t stack_size = 0;
    if (size + sizeof(stack_size) <= length) {
        memcpy(&stack_size, buffer + size, sizeof(stack_size));
        size += sizeof(stack_size);
    }
    
    // Deserialize condition stack values
    for (uint32_t i = 0; i < stack_size && size < length; i++) {
        bool value = buffer[size++] != 0;
        array_push(&scanner->condition_stack, value);
    }
    
    // Deserialize other state
    if (size < length) scanner->in_split_construct = buffer[size++] != 0;
    if (size < length) scanner->last_was_pragma = buffer[size++] != 0;
    if (size + sizeof(SplitType) <= length) {
        memcpy(&scanner->current_split, buffer + size, sizeof(SplitType));
        size += sizeof(SplitType);
    }
    if (size + sizeof(uint32_t) <= length) {
        memcpy(&scanner->split_start_line, buffer + size, sizeof(uint32_t));
    }
}


// Helper: Check if character is valid identifier start
static bool is_id_start(int32_t c) {
    return iswalpha(c) || c == '_';
}

// Helper: Check if character is valid identifier continuation
static bool is_id_continue(int32_t c) {
    return iswalnum(c) || c == '_';
}

// Helper: Skip whitespace but not newlines
static void skip_whitespace(TSLexer *lexer) {
    while (lexer->lookahead == ' ' || lexer->lookahead == '\t') {
        lexer->advance(lexer, true);
    }
}

// Helper: Skip whitespace including newlines and comments
static void skip_whitespace_and_comments(TSLexer *lexer) {
    for (;;) {
        if (iswspace(lexer->lookahead)) {
            lexer->advance(lexer, true);
        } else if (lexer->lookahead == '/') {
            // Store current position
            lexer->mark_end(lexer);
            lexer->advance(lexer, false);
            
            if (lexer->lookahead == '/') {
                // Line comment - consume it
                lexer->advance(lexer, true);
                while (lexer->lookahead != '\n' && lexer->lookahead != '\r' && !lexer->eof(lexer)) {
                    lexer->advance(lexer, true);
                }
            } else if (lexer->lookahead == '*') {
                // Block comment - consume it
                lexer->advance(lexer, true);
                bool found_end = false;
                while (!lexer->eof(lexer) && !found_end) {
                    if (lexer->lookahead == '*') {
                        lexer->advance(lexer, true);
                        if (lexer->lookahead == '/') {
                            lexer->advance(lexer, true);
                            found_end = true;
                        }
                    } else {
                        lexer->advance(lexer, true);
                    }
                }
            } else {
                // Not a comment, backtrack
                break;
            }
        } else {
            break;
        }
    }
}

// Helper: Check if we're looking at a specific string
static bool looking_at(TSLexer *lexer, const char *word) {
    skip_whitespace(lexer);
    
    for (int i = 0; word[i] != '\0'; i++) {
        if (lexer->lookahead != word[i]) {
            return false;
        }
        lexer->advance(lexer, false);
    }
    return true;
}

// Helper: Check if we're looking at a specific string (case-insensitive)
static bool looking_at_ci(TSLexer *lexer, const char *word) {
    skip_whitespace(lexer);
    
    for (int i = 0; word[i] != '\0'; i++) {
        if (towlower(lexer->lookahead) != towlower(word[i])) {
            return false;
        }
        lexer->advance(lexer, false);
    }
    return true;
}

// Helper: Consume rest of line
static void consume_line(TSLexer *lexer) {
    while (lexer->lookahead != '\n' && lexer->lookahead != '\r' && !lexer->eof(lexer)) {
        lexer->advance(lexer, false);
    }
}

// Helper: Check for pragma directive
static bool scan_pragma(Scanner *scanner, TSLexer *lexer) {
    if (lexer->lookahead != '#') return false;
    
    lexer->advance(lexer, false);
    
    if (looking_at_ci(lexer, "pragma")) {
        consume_line(lexer);
        scanner->last_was_pragma = true;
        return true;
    }
    
    return false;
}

// Helper: Look ahead for specific character
static bool peek_for_char(TSLexer *lexer, char target) {
    if (lexer->lookahead == target) {
        return true;
    }
    return false;
}

// Helper: Scan until we find a character or reach end of line
static bool scan_until_char(TSLexer *lexer, char target) {
    while (lexer->lookahead != target && lexer->lookahead != '\n' && 
           lexer->lookahead != '\r' && !lexer->eof(lexer)) {
        lexer->advance(lexer, false);
    }
    return lexer->lookahead == target;
}

// Helper: Detect if we're starting a split construct
static bool detect_split_construct(Scanner *scanner, TSLexer *lexer) {
    // Check if we're in a procedure declaration context
    // Look for ) followed by whitespace/newline then #if
    if (scanner->last_was_pragma == false) {
        // Skip any whitespace
        skip_whitespace(lexer);
        
        // If we see #, this might be a split construct
        if (lexer->lookahead == '#') {
            scanner->current_split = SPLIT_PROCEDURE_HEADER;
            scanner->in_split_construct = true;
            return true;
        }
    }
    
    return false;
}

// Helper: Skip to end of line
static void skip_to_eol(TSLexer *lexer) {
    while (lexer->lookahead != '\n' && 
           lexer->lookahead != '\r' && 
           !lexer->eof(lexer)) {
        lexer->advance(lexer, false);
    }
}

// Helper: Skip string literal
static void skip_string(TSLexer *lexer) {
    char quote = lexer->lookahead;
    if (quote != '\'' && quote != '"') return;
    
    lexer->advance(lexer, false);
    while (!lexer->eof(lexer)) {
        if (lexer->lookahead == quote) {
            lexer->advance(lexer, false);
            // Check for doubled quote (escape sequence)
            if (lexer->lookahead == quote) {
                lexer->advance(lexer, false);
                continue;
            }
            break;
        }
        lexer->advance(lexer, false);
    }
}

// Helper: Skip block comment
static void skip_block_comment(TSLexer *lexer) {
    lexer->advance(lexer, false); // Skip '/'
    lexer->advance(lexer, false); // Skip '*'
    
    while (!lexer->eof(lexer)) {
        if (lexer->lookahead == '*') {
            lexer->advance(lexer, false);
            if (lexer->lookahead == '/') {
                lexer->advance(lexer, false);
                break;
            }
        } else {
            lexer->advance(lexer, false);
        }
    }
}

// Helper: Peek at next character without advancing
static int32_t peek_next_char(TSLexer *lexer) {
    // Note: This is a simplified implementation
    // Tree-sitter doesn't provide direct peek ahead
    // In practice, we'd need to use mark/restore
    return 0;  // Placeholder
}

// Helper: Skip whitespace and comments
static void skip_non_code(TSLexer *lexer) {
    while (!lexer->eof(lexer)) {
        skip_whitespace(lexer);
        
        if (lexer->lookahead == '/' && peek_next_char(lexer) == '/') {
            // Line comment
            skip_to_eol(lexer);
        } else if (lexer->lookahead == '/' && peek_next_char(lexer) == '*') {
            // Block comment
            skip_block_comment(lexer);
        } else if (lexer->lookahead == '\'' || lexer->lookahead == '"') {
            // String literal
            skip_string(lexer);
        } else {
            break;
        }
    }
}

// Helper: Skip attribute block [...]
static void skip_attribute_block(TSLexer *lexer) {
    if (lexer->lookahead != '[') return;
    lexer->advance(lexer, false);
    
    int bracket_depth = 1;
    while (bracket_depth > 0 && !lexer->eof(lexer)) {
        if (lexer->lookahead == '[') {
            bracket_depth++;
        } else if (lexer->lookahead == ']') {
            bracket_depth--;
        } else if (lexer->lookahead == '\'' || lexer->lookahead == '"') {
            skip_string(lexer);
            continue;
        }
        lexer->advance(lexer, false);
    }
}

// Helper: Match keyword (case-insensitive)
static bool match_keyword_ci(TSLexer *lexer, const char *keyword) {
    const char *p = keyword;
    uint32_t start = lexer->get_column(lexer);
    
    while (*p) {
        if (lexer->eof(lexer)) return false;
        
        char c = lexer->lookahead;
        if (c >= 'A' && c <= 'Z') c = c - 'A' + 'a';
        
        if (c != (*p >= 'A' && *p <= 'Z' ? *p - 'A' + 'a' : *p)) {
            // Rewind - this is approximate, actual implementation needs proper mark/restore
            return false;
        }
        
        lexer->advance(lexer, false);
        p++;
    }
    
    return true;
}

// Helper: Check if character is a symbol
static bool is_symbol(char c) {
    return c == '(' || c == ')' || c == '{' || c == '}' || 
           c == '[' || c == ']' || c == ';' || c == ':' ||
           c == ',' || c == '.' || c == '=' || c == '+' ||
           c == '-' || c == '*' || c == '/' || c == '<' ||
           c == '>' || c == '&' || c == '|' || c == '^' ||
           c == '!' || c == '~' || c == '?' || c == '#';
}

// Helper: Check if character is whitespace
static bool is_whitespace(char c) {
    return c == ' ' || c == '\t' || c == '\n' || c == '\r';
}

// Helper: Match keyword with whole-word boundary check
static bool match_keyword_ci_whole_word(TSLexer *lexer, const char *keyword) {
    // Mark current position
    uint32_t start_col = lexer->get_column(lexer);

    // Try to match keyword
    if (!match_keyword_ci(lexer, keyword)) {
        return false;
    }

    // Check next character is a delimiter
    if (lexer->eof(lexer) ||
        is_whitespace(lexer->lookahead) ||
        is_symbol(lexer->lookahead)) {
        // Rewind to start - this needs proper implementation
        // For now, we'll assume the caller will handle positioning
        return true;
    }

    return false;
}

// Helper: Peek ahead to check if current position starts with keyword (doesn't advance lexer)
static bool peek_keyword_ci(int32_t lookahead, TSLexer *lexer, const char *keyword) {
    // Save start state - we'll manually track position
    const char *p = keyword;

    // First character is the current lookahead (not yet advanced)
    char c = lookahead;
    if (c >= 'A' && c <= 'Z') c = c - 'A' + 'a';
    char kc = (*p >= 'A' && *p <= 'Z' ? *p - 'A' + 'a' : *p);

    if (c != kc) {
        return false;
    }

    // For the rest, we need to peek ahead without consuming
    // We'll advance temporarily but remember we need to restore
    int matched_chars = 1;
    p++;

    while (*p) {
        lexer->advance(lexer, false);
        matched_chars++;

        if (lexer->eof(lexer)) {
            // Need to rewind
            goto rewind_and_fail;
        }

        c = lexer->lookahead;
        if (c >= 'A' && c <= 'Z') c = c - 'A' + 'a';
        kc = (*p >= 'A' && *p <= 'Z' ? *p - 'A' + 'a' : *p);

        if (c != kc) {
            goto rewind_and_fail;
        }

        p++;
    }

    // Matched all characters, now check word boundary
    lexer->advance(lexer, false);
    matched_chars++;

    bool is_word_boundary = (lexer->eof(lexer) ||
                             is_whitespace(lexer->lookahead) ||
                             is_symbol(lexer->lookahead) ||
                             !is_id_continue(lexer->lookahead));

    // Rewind back to start
    for (int i = 1; i < matched_chars; i++) {
        // Tree-sitter doesn't have rewind, so we can't truly restore
        // The caller must handle this differently
    }

    return is_word_boundary;

rewind_and_fail:
    // Can't rewind in tree-sitter - this approach won't work
    return false;
}

// Helper: Match directive (case-insensitive)
static bool match_directive_ci(TSLexer *lexer, const char *directive) {
    skip_whitespace(lexer);
    return match_keyword_ci(lexer, directive);
}

// Forward declarations
static bool scan_var_terminator_in_preproc(Scanner *scanner, TSLexer *lexer);
static bool scan_split_procedure_marker(Scanner *scanner, TSLexer *lexer);
static bool scan_attribute_for_procedure(Scanner *scanner, TSLexer *lexer);

// Main scan function
bool tree_sitter_al_external_scanner_scan(
    void *payload,
    TSLexer *lexer,
    const bool *valid_symbols
) {
    Scanner *scanner = (Scanner*)payload;

    if (SCANNER_DEBUG) {
        static bool first_call = true;
        if (first_call) {
            fprintf(stderr, "SCANNER: First call - scanner is active!\n");
            fflush(stderr);
            first_call = false;
        }

        // Debug: print scanner state when at '#'
        if (lexer->lookahead == '#') {
            fprintf(stderr, "SCANNER at '#': valid: VAR_TERM=%d SPLIT=%d ATTR_PROC=%d\n",
                    valid_symbols[PREPROC_VAR_TERMINATOR],
                    valid_symbols[PREPROC_SPLIT_MARKER],
                    valid_symbols[ATTRIBUTE_FOR_PROCEDURE]);
            fflush(stderr);
        }
    }

    // Check for split procedure marker (can be called from any position)
    if (valid_symbols[PREPROC_SPLIT_MARKER]) {
        // fprintf(stderr, "  -> Checking for SPLIT_MARKER...\n");
        if (scan_split_procedure_marker(scanner, lexer)) {
            // fprintf(stderr, "  -> FOUND SPLIT_MARKER!\n");
            lexer->result_symbol = PREPROC_SPLIT_MARKER;
            return true;
        }
        // fprintf(stderr, "  -> Not a split marker\n");
    }

    // Check for attribute for procedure when we see [
    if (lexer->lookahead == '[' && valid_symbols[ATTRIBUTE_FOR_PROCEDURE]) {
        // fprintf(stderr, "  -> Checking for ATTRIBUTE_FOR_PROCEDURE...\n");
        if (scan_attribute_for_procedure(scanner, lexer)) {
            // fprintf(stderr, "  -> FOUND ATTRIBUTE_FOR_PROCEDURE!\n");
            lexer->result_symbol = ATTRIBUTE_FOR_PROCEDURE;
            return true;
        }
        // fprintf(stderr, "  -> Not an attribute for procedure\n");
    }

    // Check for var terminator in preprocessor blocks
    // CRITICAL: Only check if lookahead is already '#' - don't advance to look for it!
    // The internal lexer will position us at '#' if that's the next token.
    if (valid_symbols[PREPROC_VAR_TERMINATOR] && lexer->lookahead == '#') {
        // Mark current position as token end (zero-width token)
        lexer->mark_end(lexer);

        if (SCANNER_DEBUG) fprintf(stderr, "SCANNER: Checking for PREPROC_VAR_TERMINATOR at #...\n");
        if (scan_var_terminator_in_preproc(scanner, lexer)) {
            if (SCANNER_DEBUG) fprintf(stderr, "SCANNER: ✓ Emitting PREPROC_VAR_TERMINATOR!\n");
            // Emit zero-width terminator BEFORE the #if
            lexer->result_symbol = PREPROC_VAR_TERMINATOR;
            return true;
        }
        if (SCANNER_DEBUG) fprintf(stderr, "SCANNER: ✗ No terminator (contains vars)\n");
    }

    return false;
}

// Scan for split procedure marker
// Detects when #if starts a split procedure (attributes and/or procedure header in branches)
// Note: May be called AFTER #if is consumed, so we look ahead from current position
static bool scan_split_procedure_marker(Scanner *scanner, TSLexer *lexer) {
    // Debug: starting scan
    // fprintf(stderr, "    scan_split_procedure_marker: starting scan at lookahead='%c'(0x%x)\n",
    //         lexer->lookahead > 31 && lexer->lookahead < 127 ? lexer->lookahead : '?',
    //         lexer->lookahead);

    // Mark the token start - don't consume anything
    lexer->mark_end(lexer);

    // If we're at #, skip past the directive
    if (lexer->lookahead == '#') {
        lexer->advance(lexer, false);

        // Must be followed by 'if', 'ifdef', or 'ifndef'
        if (!match_keyword_ci(lexer, "if") &&
            !match_keyword_ci(lexer, "ifdef") &&
            !match_keyword_ci(lexer, "ifndef")) {
            // fprintf(stderr, "    scan_split_procedure_marker: not if/ifdef/ifndef, returning false\n");
            return false;
        }

        // fprintf(stderr, "    scan_split_procedure_marker: found #if, skipping to EOL\n");
        skip_to_eol(lexer);
    }

    // Otherwise, we're already past #if, so just look ahead from here
    // fprintf(stderr, "    scan_split_procedure_marker: looking ahead for procedure...\n");

    // Now look ahead to see what's in the branch
    const uint32_t MAX_LOOKAHEAD = 5000;
    uint32_t bytes_scanned = 0;

    while (!lexer->eof(lexer) && bytes_scanned < MAX_LOOKAHEAD) {
        skip_whitespace_and_comments(lexer);

        // Skip any attributes
        while (lexer->lookahead == '[') {
            skip_attribute_block(lexer);
            skip_whitespace_and_comments(lexer);
            bytes_scanned += 100; // Approximate
        }

        // Skip pragmas (#pragma)
        if (lexer->lookahead == '#') {
            lexer->advance(lexer, false);
            if (match_keyword_ci(lexer, "pragma")) {
                skip_to_eol(lexer);
                continue;
            }
            // If it's another preprocessor directive, stop looking
            return false;
        }

        // Check for 'procedure' keyword (case-insensitive)
        if (is_id_start(lexer->lookahead)) {
            // Try to match 'procedure'
            int32_t saved_lookahead = lexer->lookahead;
            bool found_procedure = false;

            // Match 'procedure' case-insensitively
            if (towlower(lexer->lookahead) == 'p') {
                lexer->advance(lexer, false);
                if (towlower(lexer->lookahead) == 'r') {
                    lexer->advance(lexer, false);
                    if (towlower(lexer->lookahead) == 'o') {
                        lexer->advance(lexer, false);
                        if (towlower(lexer->lookahead) == 'c') {
                            lexer->advance(lexer, false);
                            if (towlower(lexer->lookahead) == 'e') {
                                lexer->advance(lexer, false);
                                if (towlower(lexer->lookahead) == 'd') {
                                    lexer->advance(lexer, false);
                                    if (towlower(lexer->lookahead) == 'u') {
                                        lexer->advance(lexer, false);
                                        if (towlower(lexer->lookahead) == 'r') {
                                            lexer->advance(lexer, false);
                                            if (towlower(lexer->lookahead) == 'e') {
                                                lexer->advance(lexer, false);
                                                // Check word boundary
                                                if (!is_id_continue(lexer->lookahead)) {
                                                    found_procedure = true;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            if (found_procedure) {
                // We found a procedure inside the #if block
                // This is a split procedure marker
                // fprintf(stderr, "    scan_split_procedure_marker: FOUND procedure keyword! Returning true\n");
                return true;
            }

            // Not 'procedure', bail out
            // fprintf(stderr, "    scan_split_procedure_marker: found identifier but not 'procedure'\n");
            return false;
        }

        // If we hit something else, this isn't a split procedure
        // fprintf(stderr, "    scan_split_procedure_marker: hit non-identifier, returning false\n");
        return false;
    }

    // fprintf(stderr, "    scan_split_procedure_marker: exceeded lookahead, returning false\n");
    return false;
}

// Scan for attribute for procedure
// Detects when [ starts an attribute list that precedes a procedure (not a variable)
static bool scan_attribute_for_procedure(Scanner *scanner, TSLexer *lexer) {
    // Must start with [
    if (lexer->lookahead != '[') return false;

    // Mark the token start
    lexer->mark_end(lexer);

    // Skip the attribute block
    skip_attribute_block(lexer);

    // Look ahead to see what follows
    const uint32_t MAX_LOOKAHEAD = 2000;
    uint32_t bytes_scanned = 0;

    while (!lexer->eof(lexer) && bytes_scanned < MAX_LOOKAHEAD) {
        skip_whitespace_and_comments(lexer);

        // Skip more attributes if present
        if (lexer->lookahead == '[') {
            skip_attribute_block(lexer);
            continue;
        }

        // Skip pragmas
        if (lexer->lookahead == '#') {
            int32_t saved = lexer->lookahead;
            lexer->advance(lexer, false);
            if (match_keyword_ci(lexer, "pragma")) {
                skip_to_eol(lexer);
                continue;
            } else if (match_keyword_ci(lexer, "if") ||
                      match_keyword_ci(lexer, "ifdef") ||
                      match_keyword_ci(lexer, "ifndef")) {
                // Attribute followed by #if - could be attributed split procedure
                // Look ahead past the #if to see if there's a procedure
                skip_to_eol(lexer);
                skip_whitespace_and_comments(lexer);

                // Skip any more attributes inside the #if
                while (lexer->lookahead == '[') {
                    skip_attribute_block(lexer);
                    skip_whitespace_and_comments(lexer);
                }

                // Now check for 'procedure'
                // Fall through to the procedure check below
            } else {
                // Some other preprocessor directive
                return false;
            }
        }

        // Check for 'procedure' keyword
        if (is_id_start(lexer->lookahead)) {
            // Try to match 'procedure' case-insensitively
            bool found = (towlower(lexer->lookahead) == 'p');
            if (found) {
                lexer->advance(lexer, false);
                found = (towlower(lexer->lookahead) == 'r');
            }
            if (found) {
                lexer->advance(lexer, false);
                found = (towlower(lexer->lookahead) == 'o');
            }
            if (found) {
                lexer->advance(lexer, false);
                found = (towlower(lexer->lookahead) == 'c');
            }
            if (found) {
                lexer->advance(lexer, false);
                found = (towlower(lexer->lookahead) == 'e');
            }
            if (found) {
                lexer->advance(lexer, false);
                found = (towlower(lexer->lookahead) == 'd');
            }
            if (found) {
                lexer->advance(lexer, false);
                found = (towlower(lexer->lookahead) == 'u');
            }
            if (found) {
                lexer->advance(lexer, false);
                found = (towlower(lexer->lookahead) == 'r');
            }
            if (found) {
                lexer->advance(lexer, false);
                found = (towlower(lexer->lookahead) == 'e');
            }
            if (found) {
                lexer->advance(lexer, false);
                // Check word boundary
                if (!is_id_continue(lexer->lookahead)) {
                    // This attribute is for a procedure!
                    return true;
                }
            }

            // Not 'procedure', so this might be for a variable
            return false;
        }

        // If we hit something else, assume it's not for a procedure
        return false;
    }

    return false;
}

// Scan for var section terminators inside preprocessor blocks
// NOTE: Caller must call lexer->mark_end() before calling this function
// to establish the zero-width token position.
static bool scan_var_terminator_in_preproc(Scanner *scanner, TSLexer *lexer) {
    if (SCANNER_DEBUG) {
        fprintf(stderr, "  -> scan_var_terminator_in_preproc: Starting scan\n");
        fflush(stderr);
    }

    // Save start position for byte counting
    uint32_t start_column = lexer->get_column(lexer);

    // Lookahead only - caller already marked token position
    // Check if this is #if
    if (lexer->lookahead != '#') {
        fprintf(stderr, "    -> Not #, returning false\n");
        return false;
    }

    // Peek ahead without consuming
    lexer->advance(lexer, false);

    // Must be followed by 'if', 'ifdef', or 'ifndef'
    bool is_if = match_keyword_ci(lexer, "if");
    bool is_ifdef = match_keyword_ci(lexer, "ifdef");
    bool is_ifndef = match_keyword_ci(lexer, "ifndef");

    if (!is_if && !is_ifdef && !is_ifndef) {
        return false;
    }

    // Skip to end of directive line (for lookahead)
    skip_to_eol(lexer);
    // Note: Don't call mark_end again - token stays zero-width

    // Begin lookahead
    int depth = 1;
    uint32_t bytes_scanned = 0;
    const uint32_t MAX_LOOKAHEAD = 10000;
    
    while (depth > 0 && !lexer->eof(lexer) && bytes_scanned < MAX_LOOKAHEAD) {
        uint32_t pos_before = lexer->get_column(lexer);
        
        // Skip whitespace, comments, and strings
        skip_non_code(lexer);
        
        // Check for attributes and skip them
        if (lexer->lookahead == '[') {
            skip_attribute_block(lexer);
            continue;
        }
        
        // Check for preprocessor directives
        if (lexer->lookahead == '#') {
            lexer->advance(lexer, false);
            if (match_directive_ci(lexer, "if") || 
                match_directive_ci(lexer, "ifdef") ||
                match_directive_ci(lexer, "ifndef")) {
                depth++;
            } else if (match_directive_ci(lexer, "endif")) {
                depth--;
            }
            // Note: #else and #elif don't change depth
            skip_to_eol(lexer);
        } 
        // At depth 1, check for any var terminator
        else if (depth == 1) {
            // Check for closing brace (ends the object)
            if (lexer->lookahead == '}') {
                lexer->result_symbol = PREPROC_VAR_TERMINATOR;
                return true;
            }

            // Only check for keywords at the start of identifiers
            if (is_id_start(lexer->lookahead)) {
                // Read the entire identifier into a buffer
                char identifier[256];
                int id_len = 0;

                while (is_id_continue(lexer->lookahead) && !lexer->eof(lexer) && id_len < 255) {
                    identifier[id_len++] = lexer->lookahead;
                    lexer->advance(lexer, false);
                }
                identifier[id_len] = '\0';

                // Check if this identifier matches any var terminator (case-insensitive)
                for (int i = 0; VAR_TERMINATORS[i]; i++) {
                    // Case-insensitive comparison
                    bool matches = true;
                    const char *term = VAR_TERMINATORS[i];
                    if (strlen(term) != id_len) {
                        matches = false;
                    } else {
                        for (int j = 0; j < id_len; j++) {
                            char c1 = identifier[j];
                            char c2 = term[j];
                            // Convert to lowercase for comparison
                            if (c1 >= 'A' && c1 <= 'Z') c1 = c1 - 'A' + 'a';
                            if (c2 >= 'A' && c2 <= 'Z') c2 = c2 - 'A' + 'a';
                            if (c1 != c2) {
                                matches = false;
                                break;
                            }
                        }
                    }

                    if (matches) {
                        if (SCANNER_DEBUG) {
                            fprintf(stderr, "  -> Found terminator keyword: %s\n", term);
                            fflush(stderr);
                        }
                        lexer->result_symbol = PREPROC_VAR_TERMINATOR;
                        return true;
                    }
                }
            } else {
                // Not an identifier start, just advance one character
                lexer->advance(lexer, false);
            }
        } else {
            lexer->advance(lexer, false);
        }
        
        // Correct byte counting
        uint32_t pos_after = lexer->get_column(lexer);
        bytes_scanned += (pos_after > pos_before) ? (pos_after - pos_before) : 1;
    }

    if (SCANNER_DEBUG) {
        fprintf(stderr, "  -> scan_var_terminator_in_preproc: No terminators found\n");
        fflush(stderr);
    }
    return false;  // No terminator found
}