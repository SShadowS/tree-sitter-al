#include "tree_sitter/parser.h"
#include <stdlib.h>
#include <string.h>
#include <wctype.h>

enum TokenType {
  PROPERTY_NAME = 0,
  CONTINUE_AS_IDENTIFIER = 1,
  PREPROC_OPEN = 2,
  PREPROC_CLOSE = 3,
  BEGIN_KEYWORD = 4,
  END_KEYWORD = 5,
  PREPROC_SPLIT_BEGIN = 6,
  PREPROC_SPLIT_END = 7,
  VAR_ATTRIBUTE_OPEN = 8,
};

typedef struct {
  uint8_t depth;  // current #if/#endif nesting depth (max 255)
} ScannerState;

void *tree_sitter_al_external_scanner_create() {
  ScannerState *state = calloc(1, sizeof(ScannerState));
  return state;
}

void tree_sitter_al_external_scanner_destroy(void *payload) {
  free(payload);
}

unsigned tree_sitter_al_external_scanner_serialize(void *payload, char *buffer) {
  ScannerState *state = (ScannerState *)payload;
  buffer[0] = (char)state->depth;
  return 1;
}

void tree_sitter_al_external_scanner_deserialize(
  void *payload, const char *buffer, unsigned length
) {
  ScannerState *state = (ScannerState *)payload;
  state->depth = (length > 0) ? (uint8_t)buffer[0] : 0;
}

static bool is_identifier_start(int32_t c) {
  return iswalpha(c) || c == '_';
}

static bool is_identifier_char(int32_t c) {
  return iswalnum(c) || c == '_';
}

// Skip whitespace and newlines (advance without marking)
static void skip_whitespace(TSLexer *lexer) {
  while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
         lexer->lookahead == '\r' || lexer->lookahead == '\n' ||
         lexer->lookahead == '\f') {
    lexer->advance(lexer, true);
  }
}

// Read a keyword case-insensitively. Returns true if matched and lookahead is
// not an identifier character after the keyword (i.e., whole word matched).
// Advances the lexer past the keyword on success.
static bool read_keyword_ci(TSLexer *lexer, const char *keyword) {
  for (int i = 0; keyword[i] != '\0'; i++) {
    if (towlower(lexer->lookahead) != keyword[i]) return false;
    lexer->advance(lexer, false);
  }
  // Ensure it's a whole-word match (not followed by identifier chars)
  if (is_identifier_char(lexer->lookahead)) return false;
  return true;
}

// Consume a comment beginning at the current '/'. The '/' is consumed either
// way; the return value says whether it actually opened a comment, so a caller
// that cannot tolerate a bare '/' can decline. AL block comments do not nest
// (grammar.js's multiline_comment is the classic non-nesting C form).
static bool skip_comment(TSLexer *lexer) {
  lexer->advance(lexer, false);  // past the leading '/'
  if (lexer->lookahead == '/') {
    while (lexer->lookahead != 0 && lexer->lookahead != '\n') {
      lexer->advance(lexer, false);
    }
    return true;
  }
  if (lexer->lookahead == '*') {
    lexer->advance(lexer, false);
    while (lexer->lookahead != 0) {
      if (lexer->lookahead == '*') {
        lexer->advance(lexer, false);
        if (lexer->lookahead == '/') {
          lexer->advance(lexer, false);
          return true;
        }
        continue;
      }
      lexer->advance(lexer, false);
    }
    return true;  // unterminated block comment runs to EOF
  }
  return false;  // a lone '/' — not a comment
}

// Skip whitespace WITHOUT marking it skippable.
//
// advance(lexer, true) unconditionally resets the token's START position to the
// current offset. That is right for LEADING whitespace, and catastrophic
// afterwards: once the token text has been consumed (or mark_end called), a
// marking skip drags the start past the end and the node collapses to zero
// width at the later position. Every skip that runs after the token text must
// use this, never skip_whitespace.
static void skip_whitespace_nomark(TSLexer *lexer) {
  while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
         lexer->lookahead == '\r' || lexer->lookahead == '\n' ||
         lexer->lookahead == '\f') {
    lexer->advance(lexer, false);
  }
}

// Skip whitespace and comments, without marking. Returns false if a bare '/'
// was hit (already consumed), which no lookahead in this scanner can make
// sense of.
static bool skip_whitespace_and_comments(TSLexer *lexer) {
  while (true) {
    skip_whitespace_nomark(lexer);
    if (lexer->lookahead != '/') return true;
    if (!skip_comment(lexer)) return false;
  }
}

// Directives that grammar.js declares as `extras`. Comments are extras too, but
// they are handled by skip_whitespace_and_comments rather than listed here.
// Everything transparent to the parse tree must be stepped over by a lookahead
// scanning for a structural directive. Keep in sync with the `extras` array.
static const char *const TRANSPARENT_DIRECTIVES[] = {
  "pragma", "endregion", "region", "define", "undef", NULL,
};

// Target sets for peek_directive_ci_skip_extras. Bare words, no '#'.
static const char *const DIRECTIVE_ENDIF[] = { "endif", NULL };
static const char *const DIRECTIVE_ELSE_ENDIF[] = { "else", "endif", NULL };

// Skip whitespace, comments and transparent-directive lines, then test whether
// what follows is a '#' directive named by one of `targets`.
//
// Used when scanning ahead for split-construct patterns (PREPROC_SPLIT_BEGIN
// looking for #endif, PREPROC_SPLIT_END looking for #else/#endif).
//
// EVERY target is tested against a SINGLE buffered read of the directive word.
// Never match candidates one after another here: consuming '#' is irreversible
// within one scan, and so is consuming the 'end' prefix shared by "endif" and
// "endregion", so a failed first attempt silently destroys the later ones. An
// earlier `read_keyword_ci(lexer, "else") || read_keyword_ci(lexer, "endif")`
// in PREPROC_SPLIT_END made the "endif" arm permanently unreachable exactly
// this way.
static bool peek_directive_ci_skip_extras(TSLexer *lexer, const char *const *targets) {
  while (true) {
    if (!skip_whitespace_and_comments(lexer)) return false;
    if (lexer->lookahead != '#') return false;

    lexer->advance(lexer, false);
    // Horizontal whitespace only: '# pragma' is one directive, but '#' and a
    // word on the NEXT line are not (matching the extras regexes' `[ \t]*`).
    while (lexer->lookahead == ' ' || lexer->lookahead == '\t') {
      lexer->advance(lexer, false);
    }

    // Read the directive word. Longest AL directive is "endregion" (9).
    char word[16];
    size_t len = 0;
    while (is_identifier_char(lexer->lookahead)) {
      if (len < sizeof(word) - 1) word[len] = (char)towlower(lexer->lookahead);
      len++;
      lexer->advance(lexer, false);
    }
    if (len >= sizeof(word)) return false;  // too long to be any directive
    word[len] = '\0';

    for (int i = 0; targets[i] != NULL; i++) {
      if (strcmp(word, targets[i]) == 0) return true;
    }

    bool transparent = false;
    for (int i = 0; TRANSPARENT_DIRECTIVES[i] != NULL; i++) {
      if (strcmp(word, TRANSPARENT_DIRECTIVES[i]) == 0) { transparent = true; break; }
    }
    if (!transparent) return false;

    // Skip the rest of this directive's line, then look again.
    while (lexer->lookahead != '\0' && lexer->lookahead != '\n') {
      lexer->advance(lexer, false);
    }
  }
}

bool tree_sitter_al_external_scanner_scan(
  void *payload,
  TSLexer *lexer,
  const bool *valid_symbols
) {
  ScannerState *state = (ScannerState *)payload;

  // Error recovery guard: when all externals are valid, the parser is in
  // error recovery mode. Don't match anything — let the parser handle it.
  if (valid_symbols[PROPERTY_NAME] && valid_symbols[CONTINUE_AS_IDENTIFIER] &&
      valid_symbols[PREPROC_OPEN] && valid_symbols[PREPROC_CLOSE] &&
      valid_symbols[BEGIN_KEYWORD] && valid_symbols[END_KEYWORD] &&
      valid_symbols[PREPROC_SPLIT_BEGIN] &&
      valid_symbols[PREPROC_SPLIT_END] &&
      valid_symbols[VAR_ATTRIBUTE_OPEN]) {
    return false;
  }

  // PREPROC_OPEN (#if) and PREPROC_CLOSE (#endif) — combined dispatch
  // We must handle both in one block because consuming '#' is irreversible
  // within a single scanner call.
  if (valid_symbols[PREPROC_OPEN] || valid_symbols[PREPROC_CLOSE]) {
    skip_whitespace(lexer);
    if (lexer->lookahead == '#') {
      lexer->advance(lexer, false);
      // Consume horizontal whitespace between '#' and the keyword as PART OF
      // THE TOKEN (advance(lexer, false) — never advance(lexer, true), which
      // would mark it as a skippable extra instead). Space/tab ONLY — never
      // '\r'/'\n': a directive split across lines must NOT match (that stays
      // an honest ERROR; see the cross-line negatives in
      // preproc_if_elif_whitespace_tolerance_test.txt). This makes '#if' and
      // '#endif' (spaced or not) scanner-exclusive: the only route either
      // token can be produced is here, so there is no scanner/literal split
      // for GLR to fork on (see grammar.js's preproc_if/preproc_endif, which
      // now carry ONLY $.preproc_open/$.preproc_close — no literal fallback).
      while (lexer->lookahead == ' ' || lexer->lookahead == '\t') {
        lexer->advance(lexer, false);
      }
      if (valid_symbols[PREPROC_OPEN] && read_keyword_ci(lexer, "if")) {
        state->depth++;
        lexer->result_symbol = PREPROC_OPEN;
        return true;
      }
      // Note: if "if" didn't match, we consumed '#' + optional whitespace +
      // partial chars. read_keyword_ci only advances while chars match, so
      // if it returned false on the first char, no further chars beyond the
      // whitespace were consumed. For "#endif"/"# endif", after failing the
      // "if" match (first char 'e' != 'i'), the lexer is right after the
      // whitespace. We can still try "endif" from there.
      if (valid_symbols[PREPROC_CLOSE] && read_keyword_ci(lexer, "endif")) {
        if (state->depth > 0) state->depth--;
        lexer->result_symbol = PREPROC_CLOSE;
        return true;
      }
      // '#' (+ optional whitespace) was consumed but neither matched —
      // return false. Per the external-scanner contract, ALL advances made
      // during this (failed) scan are discarded by tree-sitter; the lexer
      // resets to the original '#' position for the next lex attempt (e.g.
      // the parser's generic error-recovery machinery). This is the existing
      // invariant the pre-whitespace code already relied on (see the note
      // above) — untouched by this change.
      return false;
    }
  }

  // 'begin' dispatch — BEGIN_KEYWORD and PREPROC_SPLIT_BEGIN in ONE scan.
  //
  // These cannot be two sequential blocks. A scan that returns false discards
  // every advance it made and the scanner is NOT re-entered at the same
  // position, so a PREPROC_SPLIT_BEGIN block that reads 'begin', fails its
  // lookahead and declines destroys BEGIN_KEYWORD's only chance to fire. Read
  // the keyword once, fix the token end with mark_end, then let the lookahead
  // choose the symbol.
  //
  // The split token gets first refusal at depth > 0; BEGIN_KEYWORD is the
  // fallback at EVERY depth. It used to be guarded by `state->depth == 0`,
  // which left a complete begin…end inside #if claimed by no visible node at
  // all: the grammar's anonymous kw('begin') is token(PATTERN), and tree-sitter
  // renders anonymous PATTERN tokens as hidden auxiliary symbols (unlike
  // anonymous STRING tokens such as ";", which are visible). The keyword was
  // lexed and then vanished from the tree.
  //
  // '#' handling: peek_directive_ci_skip_extras takes BARE directive words and
  // consumes the '#' itself. PREPROC_OPEN/CLOSE manually advance past '#'
  // before calling read_keyword_ci("if"/"endif"). These are DIFFERENT
  // conventions — do not mix.
  //
  // Comments, #pragma, #region, #define and friends are all extras, hence all
  // transparent here (see skip_whitespace_and_comments/TRANSPARENT_DIRECTIVES).
  if (valid_symbols[BEGIN_KEYWORD] || valid_symbols[PREPROC_SPLIT_BEGIN]) {
    skip_whitespace(lexer);
    if (read_keyword_ci(lexer, "begin")) {
      lexer->mark_end(lexer);  // token covers only 'begin'
      if (state->depth > 0 && valid_symbols[PREPROC_SPLIT_BEGIN] &&
          peek_directive_ci_skip_extras(lexer, DIRECTIVE_ENDIF)) {
        lexer->result_symbol = PREPROC_SPLIT_BEGIN;
        return true;
      }
      if (valid_symbols[BEGIN_KEYWORD]) {
        lexer->result_symbol = BEGIN_KEYWORD;
        return true;
      }
      return false;
    }
    // Not 'begin'. When the split token is live this scan is committed to the
    // begin decision and declines outright (pre-existing behaviour); otherwise
    // fall through so the 'end' dispatch and the identifier tokens still run.
    //
    // CONSTRAINT this early return depends on: no parse state may offer
    // PREPROC_SPLIT_BEGIN and END_KEYWORD at the same position. If one did,
    // this line would swallow a legitimate 'end'. It holds today because all
    // three $.preproc_split_begin sites in grammar.js are immediately followed
    // by $.preproc_endif, so #endif is the only continuation the parser will
    // accept there. Before 4.0.0 the constraint was free — END_KEYWORD was
    // dead at depth > 0, so this guard could not shadow it. It is no longer
    // free. Re-check it if you add a fourth $.preproc_split_begin site, and
    // narrow the guard to the 'begin'-only case if the new site admits 'end'.
    if (state->depth > 0 && valid_symbols[PREPROC_SPLIT_BEGIN]) return false;
  }

  // 'end' dispatch — END_KEYWORD and PREPROC_SPLIT_END in ONE scan, for the
  // same reason as 'begin' above. PREPROC_SPLIT_END wants 'end' followed by
  // ';' then #else or #endif.
  if (valid_symbols[END_KEYWORD] || valid_symbols[PREPROC_SPLIT_END]) {
    skip_whitespace(lexer);
    if (read_keyword_ci(lexer, "end")) {
      lexer->mark_end(lexer);  // token covers only 'end'
      if (state->depth > 0 && valid_symbols[PREPROC_SPLIT_END]) {
        // Comments and transparent directive lines may sit at either gap and
        // must not stop the lookahead — before this skipped nothing, a single
        // trailing `// note` after the `end;` silently dropped the token and
        // the run reparsed as a call_statement with NO error nodes.
        //
        // A failed lookahead (including the bare-'/' decline) is not a failed
        // scan: 'end' is still an 'end', so fall through to END_KEYWORD rather
        // than returning false. mark_end already pinned the token to 'end'.
        if (skip_whitespace_and_comments(lexer) && lexer->lookahead == ';') {
          lexer->advance(lexer, false);
          if (peek_directive_ci_skip_extras(lexer, DIRECTIVE_ELSE_ENDIF)) {
            lexer->result_symbol = PREPROC_SPLIT_END;
            return true;
          }
        }
      }
      if (valid_symbols[END_KEYWORD]) {
        lexer->result_symbol = END_KEYWORD;
        return true;
      }
      return false;
    }
    if (state->depth > 0 && valid_symbols[PREPROC_SPLIT_END]) return false;
  }

  // VAR_ATTRIBUTE_OPEN: match '[' when the attribute is followed by a variable
  // declaration pattern (identifier ':' or quoted_identifier ':' or another '[').
  // This prevents var_section from greedily consuming procedure-level attributes.
  // The scanner scans past the entire [...] attribute, then checks what follows.
  if (valid_symbols[VAR_ATTRIBUTE_OPEN]) {
    skip_whitespace(lexer);
    if (lexer->lookahead == '[') {
      // Mark the '[' as the token (single character)
      lexer->advance(lexer, false);
      lexer->mark_end(lexer);

      // Scan past the attribute content to find the closing ']'.
      // Bracket depth handles nesting; strings and comments are skipped whole so
      // a ']' inside either cannot close the scan early.
      int bracket_depth = 1;
      bool in_string = false;

      while (bracket_depth > 0 && lexer->lookahead != 0) {
        if (in_string) {
          if (lexer->lookahead == '\'') {
            lexer->advance(lexer, false);
            // Check for escaped quote ('')
            if (lexer->lookahead == '\'') {
              lexer->advance(lexer, false);
              continue;
            }
            in_string = false;
            continue;
          }
        } else {
          if (lexer->lookahead == '/') {
            // Consumes the '/' whether or not a comment opened, so the loop
            // always makes progress.
            skip_comment(lexer);
            continue;
          }
          if (lexer->lookahead == '\'') {
            in_string = true;
          } else if (lexer->lookahead == '[') {
            bracket_depth++;
          } else if (lexer->lookahead == ']') {
            bracket_depth--;
            if (bracket_depth == 0) {
              lexer->advance(lexer, false);  // consume the ']'
              break;
            }
          }
        }
        lexer->advance(lexer, false);
      }

      if (bracket_depth != 0) return false;  // unterminated attribute

      // Now skip whitespace after ']' and check what follows
      while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
             lexer->lookahead == '\r' || lexer->lookahead == '\n' ||
             lexer->lookahead == '\f') {
        lexer->advance(lexer, false);
      }

      // Check what follows:
      // - '[' → another attribute (chain) → this is a var attribute
      // - identifier followed by ':' → variable declaration → var attribute
      // - '"' quoted identifier followed by ':' → variable declaration → var attribute
      // - anything else → NOT a variable → decline

      if (lexer->lookahead == '[') {
        // Another attribute follows — scan past all chained attributes to check
        // if the final one is followed by a variable declaration pattern.
        // We need to scan past [attr1][attr2]...[attrN] identifier: to confirm.
        while (lexer->lookahead == '[') {
          int inner_bracket_depth = 1;
          bool inner_in_string = false;
          lexer->advance(lexer, false);  // consume '['
          while (inner_bracket_depth > 0 && lexer->lookahead != 0) {
            if (inner_in_string) {
              if (lexer->lookahead == '\'') {
                lexer->advance(lexer, false);
                if (lexer->lookahead == '\'') {
                  lexer->advance(lexer, false);
                  continue;
                }
                inner_in_string = false;
                continue;
              }
            } else {
              if (lexer->lookahead == '/') {
                skip_comment(lexer);
                continue;
              }
              if (lexer->lookahead == '\'') {
                inner_in_string = true;
              } else if (lexer->lookahead == '[') {
                inner_bracket_depth++;
              } else if (lexer->lookahead == ']') {
                inner_bracket_depth--;
                if (inner_bracket_depth == 0) {
                  lexer->advance(lexer, false);  // consume ']'
                  break;
                }
              }
            }
            lexer->advance(lexer, false);
          }
          if (inner_bracket_depth != 0) return false;
          // Skip whitespace between chained attributes
          while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
                 lexer->lookahead == '\r' || lexer->lookahead == '\n' ||
                 lexer->lookahead == '\f') {
            lexer->advance(lexer, false);
          }
        }
        // After all chained attributes, check for variable declaration pattern
        // (fall through to the identifier/quoted-identifier checks below)
      }

      // Variable declaration pattern: name (',' name)* ':'  — where each name
      // is a bare identifier or a quoted identifier, in ANY position. Handling
      // quoted and bare names in one loop is what lets a quoted name lead a
      // multi-name declaration; the previous split branches accepted a quoted
      // name only when it was solo or in a later position.
      if (lexer->lookahead == '"' || is_identifier_start(lexer->lookahead)) {
        while (true) {
          if (lexer->lookahead == '"') {
            lexer->advance(lexer, false);
            while (lexer->lookahead != 0 && lexer->lookahead != '"') {
              lexer->advance(lexer, false);
            }
            if (lexer->lookahead != '"') return false;  // unterminated
            lexer->advance(lexer, false);
          } else if (is_identifier_start(lexer->lookahead)) {
            while (is_identifier_char(lexer->lookahead)) {
              lexer->advance(lexer, false);
            }
          } else {
            return false;
          }

          // Skip whitespace
          while (lexer->lookahead == ' ' || lexer->lookahead == '\t') {
            lexer->advance(lexer, false);
          }
          if (lexer->lookahead == ':') {
            lexer->result_symbol = VAR_ATTRIBUTE_OPEN;
            return true;
          }
          if (lexer->lookahead != ',') return false;

          lexer->advance(lexer, false);  // past the ','
          while (lexer->lookahead == ' ' || lexer->lookahead == '\t') {
            lexer->advance(lexer, false);
          }
        }
      }

      // Not followed by variable declaration pattern — decline
      return false;
    }
  }

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

    // Did not match continue_as_identifier. We can't fall through to
    // PROPERTY_NAME because characters are already consumed and the external
    // scanner is NOT re-entered for the same position after a false return —
    // tree-sitter discards the advances and runs the internal lexer instead.
    // This is only safe because the grammar never makes CONTINUE_AS_IDENTIFIER
    // and PROPERTY_NAME valid in the same state (properties live in object and
    // section bodies, `continue :=` in statement bodies).
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

    // Skip whitespace and comments. '\n' belongs here just as much as '\r' —
    // the leading skip above already accepts it, and alc accepts a property
    // whose '=' sits on the next line (verified). Omitting it made
    // `Caption\n    = 'Test';` an ERROR that the compiler compiles fine.
    // A bare '/' is not a comment and is not '=', so declining on it loses
    // nothing.
    if (!skip_whitespace_and_comments(lexer)) return false;

    // Check for = but not :=
    if (lexer->lookahead == '=') {
      lexer->result_symbol = PROPERTY_NAME;
      return true;
    }

    return false;
  }

  return false;
}
