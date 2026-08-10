#include "tree_sitter/parser.h"
#include <stdint.h>
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
  // Current #if/#endif nesting depth. uint32_t, not uint8_t: a uint8_t wrapped
  // to 0 at 256 simultaneously-open #if directives, and every `state->depth > 0`
  // guard below then read that genuine nesting as "not nested", so a split
  // construct whose own #if was the 256th open one lost its PREPROC_SPLIT_*
  // token. Verified: with 255 enclosing #if blocks the split `end;` degraded to
  // a call_statement, at 254 and at 256 it did not. The balanced-file accident
  // that the underflow guard restores 0 afterwards did not make the misparse
  // any less real. 2^32 open directives cannot be reached by a file that fits
  // in memory, so the wrap is now gone rather than moved.
  uint32_t depth;
} ScannerState;

// A reverted `depth` fails the BUILD rather than one deeply nested file, since
// the smallest input that shows the wrap needs 256 open #if directives and its
// expected parse tree is ~485 KB — far too large to keep as a corpus fixture.
typedef char scanner_depth_must_not_wrap[
  (sizeof(((ScannerState *)0)->depth) >= 4) ? 1 : -1];

void *tree_sitter_al_external_scanner_create() {
  ScannerState *state = calloc(1, sizeof(ScannerState));
  return state;
}

void tree_sitter_al_external_scanner_destroy(void *payload) {
  free(payload);
}

unsigned tree_sitter_al_external_scanner_serialize(void *payload, char *buffer) {
  ScannerState *state = (ScannerState *)payload;
  memcpy(buffer, &state->depth, sizeof(state->depth));
  return (unsigned)sizeof(state->depth);
}

void tree_sitter_al_external_scanner_deserialize(
  void *payload, const char *buffer, unsigned length
) {
  ScannerState *state = (ScannerState *)payload;
  state->depth = 0;
  if (length >= sizeof(state->depth)) {
    memcpy(&state->depth, buffer, sizeof(state->depth));
  }
}

static bool is_identifier_start(int32_t c) {
  return iswalpha(c) || c == '_';
}

static bool is_identifier_char(int32_t c) {
  return iswalnum(c) || c == '_';
}

// Fold one codepoint to a single byte for comparison against the ASCII-only
// keyword and directive spellings below.
//
// NEVER use towlower() for this. wint_t is 16 bits on Windows (MSVC warns
// C4244 on every such call), so towlower() silently truncates a
// supplementary-plane codepoint to its low 16 bits: U+10042 became 'B' and
// then 'b', and `\U00010042egin: Integer;` — a perfectly ordinary identifier
// under grammar.js's `[\p{L}_][\p{L}\p{N}_]*` — was lexed as a begin_keyword
// and swallowed the declaration. The same input parsed correctly on Linux,
// where wint_t is 32 bits, so the parser disagreed with itself across
// platforms.
//
// Non-ASCII folds to 0x01, a byte no keyword or directive contains, so no
// codepoint outside ASCII can ever be mistaken for an ASCII letter.
static char keyword_byte(int32_t c) {
  if (c >= 'A' && c <= 'Z') return (char)(c + ('a' - 'A'));
  if (c >= 0 && c < 128) return (char)c;
  return (char)0x01;
}

// Skip whitespace and newlines (advance without marking)
static void skip_whitespace(TSLexer *lexer) {
  while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
         lexer->lookahead == '\r' || lexer->lookahead == '\n' ||
         lexer->lookahead == '\f') {
    lexer->advance(lexer, true);
  }
}

// Consume a complete word into `buf` and report its length. The word is folded
// through keyword_byte, so comparing it against an ASCII spelling is a
// whole-word, case-insensitive test with no truncation. Returns false when the
// word did not fit, in which case it is longer than any candidate and no
// comparison is meaningful (the characters are consumed either way).
//
// NOTHING in this scanner matches a candidate keyword against the live lexer
// any more, and nothing should. A match that walks the lexer stops on the first
// mismatching character with its prefix ALREADY CONSUMED, and a scan cannot give
// characters back — so a second candidate tried afterwards is reading from the
// wrong place. That defect has now been found three times in this file, in
// three different shapes: `read_keyword_ci("else") || read_keyword_ci("endif")`
// in PREPROC_SPLIT_END, the per-keyword begin/end/continue/property reads, and
// the `if`-then-`endif` chain in the '#' dispatch. Read the word ONCE, then
// compare.
static bool read_word_ci(TSLexer *lexer, char *buf, size_t cap, size_t *out_len) {
  size_t len = 0;
  while (is_identifier_char(lexer->lookahead)) {
    if (len < cap - 1) buf[len] = keyword_byte(lexer->lookahead);
    len++;
    lexer->advance(lexer, false);
  }
  *out_len = len;
  // Always NUL-terminated, so an over-long word is still usable for a PREFIX
  // test (every candidate is shorter than any buffer here). Only a whole-word
  // test has to check the return value.
  buf[len > cap - 1 ? cap - 1 : len] = '\0';
  return len <= cap - 1;
}

// Which scanner keyword an identifier turned out to be.
enum IdentifierWord {
  WORD_NOT_IDENTIFIER = 0,  // lookahead is not an identifier start; nothing consumed
  WORD_OTHER,               // an identifier, none of the three keywords
  WORD_BEGIN,
  WORD_END,
  WORD_CONTINUE,
};

// Consume ONE complete identifier and classify it.
//
// begin, end, continue and property_name are all identifier-initial, so they
// must share a single read (read_word_ci — see the rule stated there). Matching
// them one after another does not work: a walking match stops on the first
// mismatching character with its prefix already consumed, and tree-sitter has
// no backtracking inside a scan, so the next branch starts in the MIDDLE of an
// identifier. That is how `b1 = 5;` lost its property — the `begin` attempt ate
// the 'b', and PROPERTY_NAME's is_identifier_start check then saw the '1' and
// declined, while `x1 = 5;` in the same position (parse states 20 and 22 offer
// property_name and begin_keyword together) parsed as a property. It is also
// how a leading `b` was absorbed into a following VAR_ATTRIBUTE_OPEN, giving a
// two-column `[` token whose text was `b[`.
static enum IdentifierWord read_identifier_word(TSLexer *lexer) {
  if (!is_identifier_start(lexer->lookahead)) return WORD_NOT_IDENTIFIER;

  char buf[9];  // longest keyword tested is "continue" (8) plus the NUL
  size_t len = 0;
  if (!read_word_ci(lexer, buf, sizeof(buf), &len)) {
    return WORD_OTHER;  // too long to be any keyword
  }

  if (len == 5 && strcmp(buf, "begin") == 0) return WORD_BEGIN;
  if (len == 3 && strcmp(buf, "end") == 0) return WORD_END;
  if (len == 8 && strcmp(buf, "continue") == 0) return WORD_CONTINUE;
  return WORD_OTHER;
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

// A directive name plus HOW grammar.js matches it. The two modes are not
// interchangeable, and getting one wrong makes the scanner disagree with the
// parser about what a directive even is:
//
//   whole_word = true   The grammar reaches this directive ONLY through the
//                       scanner's own '#' dispatch, which compares the whole
//                       word. `#endif` is the only one: `#endifX` is not a
//                       preproc_close for the parser either, so the lookahead
//                       must not treat it as one.
//
//   whole_word = false  The grammar matches it with a regex carrying no
//                       trailing boundary. `#[ \t]*region[^\n\r]*` accepts
//                       `#regionX foo` as a preproc_region extra, and
//                       `#[ \t]*else` matches the first five bytes of
//                       `#elseX`. A whole-word scanner test rejected all of
//                       these while the parser accepted them, and the split
//                       token then declined: `#regionX` sitting between an
//                       `end;` and its `#else` degraded the `end;` to a
//                       call_statement and shredded the #else branch into loose
//                       identifiers. Prefix matching is what keeps the two in
//                       agreement.
typedef struct {
  const char *name;
  bool whole_word;
} DirectiveMatch;

// Directives that grammar.js declares as `extras`. Comments are extras too, but
// they are handled by skip_whitespace_and_comments rather than listed here.
// Everything transparent to the parse tree must be stepped over by a lookahead
// scanning for a structural directive. Keep in sync with the `extras` array —
// including the match mode, which mirrors each one's regex.
static const DirectiveMatch TRANSPARENT_DIRECTIVES[] = {
  { "pragma", false }, { "endregion", false }, { "region", false },
  { "define", false }, { "undef", false }, { NULL, false },
};

// Target sets for peek_directive_ci_skip_extras. Bare words, no '#'.
static const DirectiveMatch DIRECTIVE_ENDIF[] = { { "endif", true }, { NULL, false } };
// PREPROC_SPLIT_END's continuation set. "elif" belongs here for the same reason
// "else" does: `#if … end; #elif …` is a branch alternative, and alc accepts it
// (verified — both the #elif and #else forms compile). Omitting it made the
// token decline and the run reparse as a call_statement plus loose identifiers.
// Adding a target here is free: every target is tested against ONE buffered
// read of the directive word (see peek_directive_ci_skip_extras), so a third
// entry cannot resurrect the consume-the-prefix trap described there.
static const DirectiveMatch DIRECTIVE_BRANCH_OR_ENDIF[] = {
  { "elif", false }, { "else", false }, { "endif", true }, { NULL, false },
};

// Test one buffered directive word against one candidate. `truncated` says the
// word was longer than the buffer; every candidate is at most 9 bytes, so a
// prefix test is still decisive, but a whole-word test can only fail.
static bool directive_matches(const DirectiveMatch *d, const char *word, bool truncated) {
  size_t n = strlen(d->name);
  if (strncmp(word, d->name, n) != 0) return false;
  if (!d->whole_word) return true;
  return !truncated && word[n] == '\0';
}

// Skip whitespace, comments and transparent-directive lines, then test whether
// what follows is a '#' directive named by one of `targets`.
//
// Used when scanning ahead for split-construct patterns (PREPROC_SPLIT_BEGIN
// looking for #endif, PREPROC_SPLIT_END looking for #else/#endif).
//
// EVERY target is tested against a SINGLE buffered read of the directive word
// (read_word_ci). Never match candidates one after another here: consuming '#'
// is irreversible within one scan, and so is consuming the 'end' prefix shared
// by "endif" and "endregion", so a failed first attempt silently destroys the
// later ones. An earlier walking `read_keyword_ci("else") ||
// read_keyword_ci("endif")` in PREPROC_SPLIT_END made the "endif" arm
// permanently unreachable exactly this way.
static bool peek_directive_ci_skip_extras(TSLexer *lexer, const DirectiveMatch *targets) {
  while (true) {
    if (!skip_whitespace_and_comments(lexer)) return false;
    if (lexer->lookahead != '#') return false;

    lexer->advance(lexer, false);
    // Horizontal whitespace only: '# pragma' is one directive, but '#' and a
    // word on the NEXT line are not (matching the extras regexes' `[ \t]*`).
    while (lexer->lookahead == ' ' || lexer->lookahead == '\t') {
      lexer->advance(lexer, false);
    }

    // Read the directive word ONCE. Longest AL directive is "endregion" (9), so
    // 15 stored bytes always decide a prefix test; an over-long word is kept
    // rather than rejected, because `#regionAAAAAAAAAAAAAA` is still a
    // preproc_region to the parser.
    char word[16];
    size_t len = 0;
    bool truncated = !read_word_ci(lexer, word, sizeof(word), &len);

    for (int i = 0; targets[i].name != NULL; i++) {
      if (directive_matches(&targets[i], word, truncated)) return true;
    }

    bool transparent = false;
    for (int i = 0; TRANSPARENT_DIRECTIVES[i].name != NULL; i++) {
      if (directive_matches(&TRANSPARENT_DIRECTIVES[i], word, truncated)) {
        transparent = true;
        break;
      }
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
      // Read the directive word ONCE and compare it against both candidates.
      //
      // This used to chain `read_keyword_ci("if")` and then, on failure,
      // `read_keyword_ci("endif")`, defended by the argument that the two words
      // differ at their first character so a failed "if" consumes nothing. That
      // argument is about the two CANDIDATES and says nothing about the INPUT,
      // which is not restricted to them:
      //
      //   `#elif`   — "if" declines at char 0, then "endif" matches the 'e' and
      //               declines at 'l', leaving the 'e' consumed. Harmless only
      //               because the next statement is `return false` and
      //               tree-sitter discards a failed scan's advances.
      //   `#iendif` — "if" matches the 'i', declines at 'e', and leaves the 'i'
      //               consumed. "endif" then reads the REMAINING `endif` and
      //               RETURNS TRUE: a preproc_close spanning all seven bytes of
      //               `#iendif`, the depth counter decremented, exit code 0 and
      //               no ERROR node, for a directive the grammar accepts
      //               nowhere. `#ifendif` did the same via the "if" whole-word
      //               check. `#xendif` errored correctly — the discriminator is
      //               whether the input starts with a prefix of "if".
      //
      // One buffered read cannot do that: the word is compared whole, so a
      // partial candidate match can neither leak into the next comparison nor
      // return true. "endif" (5) is the longest candidate.
      char word[8];
      size_t len = 0;
      if (!read_word_ci(lexer, word, sizeof(word), &len)) return false;
      if (valid_symbols[PREPROC_OPEN] && len == 2 && strcmp(word, "if") == 0) {
        state->depth++;
        lexer->result_symbol = PREPROC_OPEN;
        return true;
      }
      if (valid_symbols[PREPROC_CLOSE] && len == 5 && strcmp(word, "endif") == 0) {
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

  // VAR_ATTRIBUTE_OPEN: match '[' when the attribute is followed by a variable
  // declaration pattern (identifier ':' or quoted_identifier ':' or another '[').
  // This prevents var_section from greedily consuming procedure-level attributes.
  // The scanner scans past the entire [...] attribute, then checks what follows.
  //
  // This runs BEFORE the identifier dispatch, and must stay there. It is the
  // only '['-initial token, so no identifier can precede it in a well-formed
  // token — but when it ran second, a failed `begin` match had already eaten a
  // leading 'b' and the '[' token silently grew to cover `b[`, losing the
  // identifier byte from the tree entirely. Ordering a '['-initial token ahead
  // of the identifier-initial ones costs nothing and removes that whole class.
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

      // Now skip whitespace and comments after ']' and check what follows
      if (!skip_whitespace_and_comments(lexer)) return false;

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
          // Skip whitespace and comments between chained attributes
          if (!skip_whitespace_and_comments(lexer)) return false;
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

          // Skip whitespace and comments
          if (!skip_whitespace_and_comments(lexer)) return false;
          if (lexer->lookahead == ':') {
            lexer->result_symbol = VAR_ATTRIBUTE_OPEN;
            return true;
          }
          if (lexer->lookahead != ',') return false;

          lexer->advance(lexer, false);  // past the ','
          if (!skip_whitespace_and_comments(lexer)) return false;
        }
      }

      // Not followed by variable declaration pattern — decline
      return false;
    }
  }

  // Identifier-initial dispatch — BEGIN_KEYWORD, END_KEYWORD, their two
  // PREPROC_SPLIT_* competitors, CONTINUE_AS_IDENTIFIER and PROPERTY_NAME in
  // ONE scan over ONE read of the identifier.
  //
  // These cannot be sequential blocks each doing its own read. A scan that
  // returns false discards every advance it made and the scanner is NOT
  // re-entered at the same position, so a block that reads text, fails and
  // declines destroys the later blocks' only chance to fire; and a block that
  // reads a partial match and falls through leaves the later blocks starting
  // mid-identifier. Read the word once (read_identifier_word), fix the token
  // end with mark_end, then let the classification and the lookaheads choose
  // the symbol.
  //
  // The split tokens get first refusal at depth > 0; BEGIN_KEYWORD and
  // END_KEYWORD are the fallback at EVERY depth. BEGIN_KEYWORD used to be
  // guarded by `state->depth == 0`, which left a complete begin…end inside #if
  // claimed by no visible node at all: the grammar's anonymous kw('begin') is
  // token(PATTERN), and tree-sitter renders anonymous PATTERN tokens as hidden
  // auxiliary symbols (unlike anonymous STRING tokens such as ";", which are
  // visible). The keyword was lexed and then vanished from the tree.
  //
  // '#' handling: peek_directive_ci_skip_extras takes BARE directive words and
  // consumes the '#' itself. The PREPROC_OPEN/CLOSE dispatch advances past '#'
  // manually before reading its word. These are DIFFERENT conventions — do not
  // mix.
  //
  // Comments, #pragma, #region, #define and friends are all extras, hence all
  // transparent here (see skip_whitespace_and_comments/TRANSPARENT_DIRECTIVES).
  if (valid_symbols[BEGIN_KEYWORD] || valid_symbols[PREPROC_SPLIT_BEGIN] ||
      valid_symbols[END_KEYWORD] || valid_symbols[PREPROC_SPLIT_END] ||
      valid_symbols[CONTINUE_AS_IDENTIFIER] || valid_symbols[PROPERTY_NAME]) {
    skip_whitespace(lexer);
    enum IdentifierWord word = read_identifier_word(lexer);
    if (word == WORD_NOT_IDENTIFIER) return false;  // nothing consumed
    lexer->mark_end(lexer);  // token covers exactly the identifier just read

    if (word == WORD_BEGIN &&
        (valid_symbols[BEGIN_KEYWORD] || valid_symbols[PREPROC_SPLIT_BEGIN])) {
      // A failed lookahead is not a failed scan — `begin` is still a `begin`.
      // mark_end above is what makes that fallback safe, since the lookahead
      // advances well past the keyword.
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

    if (word == WORD_END &&
        (valid_symbols[END_KEYWORD] || valid_symbols[PREPROC_SPLIT_END])) {
      // PREPROC_SPLIT_END wants 'end' followed by ';' then a branch
      // continuation — #elif, #else or #endif. Comments and transparent
      // directive lines may sit at either gap and must not stop the lookahead:
      // before this skipped nothing, a single trailing `// note` after the
      // `end;` silently dropped the token and the run reparsed as a
      // call_statement with NO error nodes.
      if (state->depth > 0 && valid_symbols[PREPROC_SPLIT_END] &&
          skip_whitespace_and_comments(lexer) && lexer->lookahead == ';') {
        lexer->advance(lexer, false);
        if (peek_directive_ci_skip_extras(lexer, DIRECTIVE_BRANCH_OR_ENDIF)) {
          lexer->result_symbol = PREPROC_SPLIT_END;
          return true;
        }
      }
      if (valid_symbols[END_KEYWORD]) {
        lexer->result_symbol = END_KEYWORD;
        return true;
      }
      return false;
    }

    // PROPERTY_NAME is tested before CONTINUE_AS_IDENTIFIER on purpose: the
    // continue test consumes the ':' of ':=' and would leave a bare '=' for the
    // property test to misread, whereas testing for '=' first consumes nothing
    // the continue test needs. (No parse state offers both — see the
    // ts_external_scanner_states table — but the order should not depend on
    // that holding.)
    if (valid_symbols[PROPERTY_NAME]) {
      // Skip whitespace and comments. '\n' belongs here just as much as '\r' —
      // the leading skip above already accepts it, and alc accepts a property
      // whose '=' sits on the next line (verified). Omitting it made
      // `Caption\n    = 'Test';` an ERROR that the compiler compiles fine.
      // A bare '/' is not a comment and is not '=', so declining on it loses
      // nothing.
      if (!skip_whitespace_and_comments(lexer)) return false;
      if (lexer->lookahead == '=') {
        lexer->result_symbol = PROPERTY_NAME;
        return true;
      }
    }

    if (word == WORD_CONTINUE && valid_symbols[CONTINUE_AS_IDENTIFIER]) {
      skip_whitespace_nomark(lexer);
      if (lexer->lookahead == ':') {
        lexer->advance(lexer, false);
        if (lexer->lookahead == '=') {
          lexer->result_symbol = CONTINUE_AS_IDENTIFIER;
          return true;
        }
      }
    }

    return false;
  }

  return false;
}
