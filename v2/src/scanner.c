#include "tree_sitter/parser.h"
#include <string.h>
#include <wctype.h>

enum TokenType {
  PROPERTY_NAME,
  CONTINUE_AS_IDENTIFIER,
};

void *tree_sitter_al_external_scanner_create() { return NULL; }
void tree_sitter_al_external_scanner_destroy(void *payload) {}
unsigned tree_sitter_al_external_scanner_serialize(void *payload, char *buffer) { return 0; }
void tree_sitter_al_external_scanner_deserialize(void *payload, const char *buffer, unsigned length) {}

static bool is_identifier_start(int32_t c) {
  return iswalpha(c) || c == '_';
}

static bool is_identifier_char(int32_t c) {
  return iswalnum(c) || c == '_';
}

bool tree_sitter_al_external_scanner_scan(
  void *payload,
  TSLexer *lexer,
  const bool *valid_symbols
) {
  // CONTINUE_AS_IDENTIFIER: match 'continue' followed by ':='
  if (valid_symbols[CONTINUE_AS_IDENTIFIER]) {
    // Skip leading whitespace
    while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
           lexer->lookahead == '\r' || lexer->lookahead == '\n' ||
           lexer->lookahead == '\f') {
      lexer->advance(lexer, true);
    }

    // Check for 'continue' (case-insensitive, exactly 8 chars)
    const char *keyword = "continue";
    int pos = 0;
    bool match = true;

    if (!is_identifier_start(lexer->lookahead)) {
      // Not an identifier — can't be continue_as_identifier or property_name
      return false;
    }

    // Try to match 'continue'
    while (is_identifier_char(lexer->lookahead)) {
      if (pos < 8) {
        if (towlower(lexer->lookahead) != keyword[pos]) {
          match = false;
        }
        pos++;
      } else {
        match = false;
        pos++;
      }
      lexer->advance(lexer, false);
    }

    // Check if exactly 'continue' (8 chars)
    if (match && pos == 8) {
      lexer->mark_end(lexer);

      // Skip whitespace
      while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
             lexer->lookahead == '\r' || lexer->lookahead == '\n' ||
             lexer->lookahead == '\f') {
        lexer->advance(lexer, false);
      }

      // Check for ':='
      if (lexer->lookahead == ':') {
        lexer->advance(lexer, false);
        if (lexer->lookahead == '=') {
          lexer->result_symbol = CONTINUE_AS_IDENTIFIER;
          return true;
        }
      }
    }

    // Did not match continue_as_identifier
    // Note: we can't fall through to PROPERTY_NAME here because we've
    // already consumed characters. The scanner will be called again
    // for the same position if we return false.
    return false;
  }

  // PROPERTY_NAME: match identifier followed by = (not :=)
  if (valid_symbols[PROPERTY_NAME]) {
    // Skip leading whitespace (extras are not skipped before external scanner)
    while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
           lexer->lookahead == '\r' || lexer->lookahead == '\n' ||
           lexer->lookahead == '\f') {
      lexer->advance(lexer, true);  // true = skip (whitespace)
    }

    // Must start with identifier character
    if (!is_identifier_start(lexer->lookahead)) return false;

    // Mark start
    lexer->mark_end(lexer);

    // Consume identifier
    while (is_identifier_char(lexer->lookahead)) {
      lexer->advance(lexer, false);
    }

    // Mark end of identifier (before whitespace/equals)
    lexer->mark_end(lexer);

    // Skip whitespace
    while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
           lexer->lookahead == '\r' || lexer->lookahead == '\f') {
      lexer->advance(lexer, false);
    }

    // Check for = but not :=
    if (lexer->lookahead == '=') {
      lexer->result_symbol = PROPERTY_NAME;
      return true;
    }

    return false;
  }

  return false;
}
