#include "tree_sitter/parser.h"
#include "tree_sitter/alloc.h"
#include "tree_sitter/array.h"
#include <wctype.h>
#include <string.h>
#include <stdio.h>
#include <stdbool.h>

// Token types enum matching the externals array order
enum TokenType {
    // Token for detecting var section terminators in preprocessor blocks
    PREPROC_VAR_TERMINATOR,
    // Error recovery token
    ERROR_SENTINEL
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

// Helper: Match directive (case-insensitive)
static bool match_directive_ci(TSLexer *lexer, const char *directive) {
    skip_whitespace(lexer);
    return match_keyword_ci(lexer, directive);
}

// Forward declaration
static bool scan_var_terminator_in_preproc(Scanner *scanner, TSLexer *lexer);

// Main scan function
bool tree_sitter_al_external_scanner_scan(
    void *payload,
    TSLexer *lexer,
    const bool *valid_symbols
) {
    Scanner *scanner = (Scanner*)payload;
    
    // Debug: print valid symbols when we see #
    if (lexer->lookahead == '#') {
        fprintf(stderr, "DEBUG: At #, valid_symbols: VAR_TERM=%d, ERROR=%d\n", 
                valid_symbols[PREPROC_VAR_TERMINATOR], 
                valid_symbols[ERROR_SENTINEL]);
        
        if (valid_symbols[PREPROC_VAR_TERMINATOR]) {
            bool result = scan_var_terminator_in_preproc(scanner, lexer);
            if (result) {
                lexer->result_symbol = PREPROC_VAR_TERMINATOR;
                return true;
            }
        }
    }
    
    return false;
}

// Scan for var section terminators inside preprocessor blocks
static bool scan_var_terminator_in_preproc(Scanner *scanner, TSLexer *lexer) {
    // Save start position for byte counting
    uint32_t start_column = lexer->get_column(lexer);
    
    // Mark start of token
    lexer->mark_end(lexer);
    
    // Consume '#'
    lexer->advance(lexer, false);
    
    // Must be followed by 'if', 'ifdef', or 'ifndef'
    if (!match_keyword_ci(lexer, "if") && 
        !match_keyword_ci(lexer, "ifdef") && 
        !match_keyword_ci(lexer, "ifndef")) {
        return false;
    }
    
    // Skip to end of directive line
    skip_to_eol(lexer);
    lexer->mark_end(lexer);  // Token ends at EOL
    
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
            // Check for 'local', 'protected', 'internal' modifiers
            const char* modifiers[] = {"local", "protected", "internal", NULL};
            for (int i = 0; modifiers[i]; i++) {
                if (match_keyword_ci_whole_word(lexer, modifiers[i])) {
                    // Skip the modifier and continue checking
                    int len = strlen(modifiers[i]);
                    for (int j = 0; j < len; j++) {
                        lexer->advance(lexer, false);
                    }
                    skip_whitespace(lexer);
                    break;
                }
            }
            
            // Check for any var terminator
            for (int i = 0; VAR_TERMINATORS[i]; i++) {
                if (match_keyword_ci_whole_word(lexer, VAR_TERMINATORS[i])) {
                    lexer->result_symbol = PREPROC_VAR_TERMINATOR;
                    return true;
                }
            }
            
            // Also check for closing brace (ends the object)
            if (lexer->lookahead == '}') {
                lexer->result_symbol = PREPROC_VAR_TERMINATOR;
                return true;
            }
            
            lexer->advance(lexer, false);
        } else {
            lexer->advance(lexer, false);
        }
        
        // Correct byte counting
        uint32_t pos_after = lexer->get_column(lexer);
        bytes_scanned += (pos_after > pos_before) ? (pos_after - pos_before) : 1;
    }
    
    return false;  // No terminator found
}