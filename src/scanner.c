#include "tree_sitter/parser.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// The grammar's own identifier character classes, generated from the tables
// tree-sitter compiled grammar.js's identifier regex into. See the note on
// is_identifier_start below for why this is not <wctype.h>.
//
// <wctype.h> is deliberately NOT included: without it, a reintroduced
// iswalpha/iswalnum/towlower fails to compile rather than silently truncating.
#include "unicode_id.h"

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
  CALC_FORMULA_PROPERTY_NAME = 9,
  DIRECTIVE_EOL = 10,
  NEGATIVE_INTEGER = 11,
  NEGATIVE_DECIMAL = 12,
  MALFORMED_DIRECTIVE = 13,  // in no grammar rule: see the '#' dispatch
  SCANNER_HOOK = 14,         // an extra that is NEVER emitted: see the '#' dispatch
};

// Named so the static assertion below can test its width AND its signedness.
typedef uint32_t ScannerDepth;

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
  ScannerDepth depth;
} ScannerState;

// A reverted `depth` fails the BUILD rather than one deeply nested file, since
// the smallest input that shows the wrap needs 256 open #if directives and its
// expected parse tree is ~485 KB — far too large to keep as a corpus fixture.
//
// Both halves are load-bearing. Width alone is not enough: a SIGNED counter of
// any width reintroduces the same class at its own boundary, and the
// `state->depth > 0` guards would read a negative depth as "not nested" exactly
// as the wrapped uint8_t did.
//
// _Static_assert where the compiler has it, because it prints the MESSAGE: the
// negative-array fallback reports a bare "C2118: negative subscript" naming
// neither the constant nor the reason, which is a check that fires without
// saying what broke.
//
// The guard is __STDC_VERSION__ ALONE, deliberately. _MSC_VER is not a proxy
// for _Static_assert support, and a `_MSC_VER >= 1928` arm here was actively
// wrong: MSVC's C compiler rejects _Static_assert under DEFAULT flags at every
// version, 19.44/VS2022 included, and accepts it only under /std:c11 or
// /std:c17 — which is exactly when it defines __STDC_VERSION__ >= 201112L. That
// arm therefore enabled the assert precisely where it does not compile, and
// every default-flags MSVC build of this file failed at this line. Measured on
// 19.44.35228: default flags give "C2143: syntax error: missing ')' before '('"
// and leave __STDC_VERSION__ undefined; -std:c11 and -std:c17 both compile
// clean. Narrowing ScannerDepth still fails the build on both paths (C2338 with
// the message under c11, C2118 via the fallback under default flags), which is
// the point of keeping the fallback.
//
// No first-party build ever saw it: Makefile passes -std=c11, binding.gyp
// passes /std:c11 on Windows, and bindings/rust/build.rs calls cc .std("c11").
// It broke only third-party consumers that compile scanner.c themselves, which
// is how it survived a release — reported by one such consumer, which had
// worked around it locally with cc.std("c11").
#define SCANNER_DEPTH_IS_UNSIGNED ((ScannerDepth)-1 > (ScannerDepth)0)
#define SCANNER_DEPTH_OK (sizeof(ScannerDepth) >= 4 && SCANNER_DEPTH_IS_UNSIGNED)
#if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
_Static_assert(SCANNER_DEPTH_OK,
  "ScannerDepth must be an unsigned type of at least 32 bits: a narrower or "
  "signed depth counter wraps, and every state->depth > 0 guard then reads "
  "genuine #if nesting as not nested");
#else
typedef char scanner_depth_must_not_wrap[SCANNER_DEPTH_OK ? 1 : -1];
#endif

void *tree_sitter_al_external_scanner_create() {
  ScannerState *state = calloc(1, sizeof(ScannerState));
  return state;
}

void tree_sitter_al_external_scanner_destroy(void *payload) {
  free(payload);
}

// Serialize and deserialize BOTH derive their width from sizeof(ScannerDepth),
// and must keep doing so. Hard-coding a literal in one of them is the failure
// this pairing exists to prevent: a 1-byte serialize against a 4-byte
// deserialize guard fails the `length >=` test on every restore and silently
// resets depth to 0, which reads as "not nested" at every #if. That one is not
// caught by the static assertion above — no compile-time check can see a
// literal — but it is caught loudly by the corpus: tree-sitter serializes the
// external state after every external token, so a width mismatch breaks depth
// tracking immediately and every preproc_split_* fixture fails. Verified by
// temporarily returning 1 here.
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

// What may start and continue an identifier, per grammar.js's OWN rule:
//
//     identifier: $ => token(/[\p{L}_][\p{L}\p{N}_]*/u)
//
// The scanner decides where PROPERTY_NAME, VAR_ATTRIBUTE_OPEN and the
// begin/end family start and end BEFORE the generated lexer sees the text, so
// any disagreement with that regex is a disagreement about what an identifier
// is — and the external token wins, because tree-sitter does not re-lex it.
//
// These were `iswalpha(c) || c == '_'` and `iswalnum(c) || c == '_'` until
// 4.0.0, and that was wrong in BOTH directions.
//
// MEASURED on Windows 11, mingw-w64/UCRT, `sizeof(wint_t) == 2`. wint_t is 16
// bits here, so an int32_t codepoint above U+FFFF is TRUNCATED before the test:
//
//     iswalpha(U+20000) == 0   truncates to U+0000 -- a plain CJK ideograph,
//                              category Lo, REJECTED
//     iswalpha(U+E0041) == 1   truncates to 'A'    -- a TAG character,
//                              category Cf and not a letter at all, ACCEPTED
//
// and at parse level, in a table body:
//
//     <U+20000>Prop = 5;   (ERROR (identifier) (integer))    <- rejected
//     YProp = 5;           (property ...)                    <- same position
//     <U+E0041>Prop = 5;   (property ...) with NO ERROR node
//
// The false-ACCEPT is the dangerous half: the scanner manufactured an
// identifier that grammar.js's own regex rejects, emitted PROPERTY_NAME across
// it, and tree-sitter does not re-lex an external token, so nothing downstream
// could notice. A clean error count did not mean a correct tree.
//
// The false-REJECT is the cross-platform half. wint_t is 32 bits on Linux, so
// the same file does not truncate there and takes a different path through
// iswalpha entirely -- the parser disagreeing with itself per platform on
// identical input. (iswalpha is also LC_CTYPE-dependent by specification, and
// nothing here calls setlocale. On this runtime that turned out NOT to matter:
// "C", "" and "en_US.UTF-8" all answered identically for every codepoint
// tested, so locale is a hazard the standard permits rather than one measured
// here. The truncation is the part that was actually observed.)
//
// unicode_id.h is generated from the character-range tables `tree-sitter
// generate` compiled that very regex into, so agreement is by construction
// rather than by maintenance. tools/gen-unicode-id-table.py --check proves it
// has not drifted.
//
// NOTE ON SCOPE: this makes the scanner agree with GRAMMAR.JS, which is the
// stated specification -- not with alc, which is narrower still. alc 18.0
// rejects U+20000 in an identifier (AL0183) and rejects U+00B2 in a
// continuation position (AL0107), both of which grammar.js's regex accepts and
// did before this change too. Narrowing that boundary is a grammar.js decision
// about "parse structure, don't validate", and a separate one from this fix.
static bool is_identifier_start(int32_t c) {
  return al_is_identifier_start(c);
}

static bool is_identifier_char(int32_t c) {
  return al_is_identifier_char(c);
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

// Every single-character member of grammar.js's `extras` array, enumerated so a
// reader can check the list against `extras` by eye. There are exactly SEVEN:
//
//     ' '   \t   \n   \r   \f   \v      -- the six that `/\s/` matches
//     U+FEFF                            -- the BOM, its own extras entry
//
// An adjective is not a specification: this comment previously said "the
// single-character members" and the list under it was missing `\v`, which read
// as complete and was not. Count the entries against `extras` rather than
// trusting the sentence.
//
// Comments and the five directive extras are not single characters and are
// handled by skip_whitespace_and_comments and TRANSPARENT_DIRECTIVES.
//
// Anything the PARSER skips as an extra and a scanner lookahead does not is a
// disagreement about where the next token starts, and it is silent. Both
// omissions had the same signature — a `\v` or a BOM between a split `end;` and
// its `#else` dropped PREPROC_SPLIT_END, while the byte-identical file without
// it emitted preproc_split_end.
//
// The bound is exactly these seven: U+0085, U+00A0, U+1680, U+2000, U+2028,
// U+2029, U+202F, U+205F and U+3000 are all rejected by the PARSER too, because
// tree-sitter's `\s` is not Unicode-aware here. Those produce a different
// failure signature (the parser errors on the character as well) and are
// correctly out of scope.
static bool is_extra_space(int32_t c) {
  return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f' ||
         c == '\v' || c == 0xFEFF;
}

// Skip whitespace and newlines (advance without marking)
static void skip_whitespace(TSLexer *lexer) {
  while (is_extra_space(lexer->lookahead)) {
    lexer->advance(lexer, true);
  }
}

// Consume a complete word into `buf` (capacity `cap`, which must be at least 2)
// and report its length. The word is folded through keyword_byte, so comparing
// it against an ASCII spelling is a whole-word, case-insensitive test with no
// truncation. The characters are consumed either way.
//
// Returns false when the word did not fit. An over-long word cannot equal any
// candidate, so every test here treats it as a miss. `buf` is NUL-terminated
// either way. (Until B2 a PREFIX test also ran on this buffer and had to accept
// an over-long word; nothing tests a prefix any more — see word_in.)
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
  // Always NUL-terminated. An over-long word is truncated here, and the return
  // value says so: every caller treats it as a miss (see word_in).
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
  WORD_CALCFORMULA,  // the one property name the scanner keys on (issue #21)
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

  char buf[12];  // longest keyword tested is "calcformula" (11) plus the NUL
  size_t len = 0;
  if (!read_word_ci(lexer, buf, sizeof(buf), &len)) {
    return WORD_OTHER;  // too long to be any keyword
  }

  if (len == 5 && strcmp(buf, "begin") == 0) return WORD_BEGIN;
  if (len == 3 && strcmp(buf, "end") == 0) return WORD_END;
  if (len == 8 && strcmp(buf, "continue") == 0) return WORD_CONTINUE;
  if (len == 11 && strcmp(buf, "calcformula") == 0) return WORD_CALCFORMULA;
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
  while (is_extra_space(lexer->lookahead)) {
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

// Every directive word is compared WHOLE, everywhere: in the '#' dispatch and
// in the lookaheads below. Until B2 the lookaheads also had a prefix mode,
// because `#else`/`#elif` were grammar regexes with no trailing boundary (the
// lexer compiler rejects `\b` and lookahead), so `#elseX` WAS `#else` to the
// parser and the lookahead had to agree. They are still grammar regexes, but
// the '#' dispatch below now claims every prefix form as MALFORMED_DIRECTIVE
// before their regexes see it, and alc rejects every prefix form (AL0621,
// tools/config_oracle/probe_alc.py prefix_*). A prefix test here would only
// make the scanner disagree with the parser about what a directive is.
//
// Directives that grammar.js declares as `extras`. Comments are extras too, but
// they are handled by skip_whitespace_and_comments rather than listed here.
// Everything transparent to the parse tree must be stepped over by a lookahead
// scanning for a structural directive. Keep in sync with the `extras` array.
static const char *const TRANSPARENT_DIRECTIVES[] = {
  "pragma", "endregion", "region", "define", "undef", NULL,
};

// Target sets for peek_directive_ci_skip_extras. Bare words, no '#'.
static const char *const DIRECTIVE_ENDIF[] = { "endif", NULL };
// PREPROC_SPLIT_END's continuation set. "elif" belongs here for the same reason
// "else" does: `#if … end; #elif …` is a branch alternative, and alc accepts it
// (verified — both the #elif and #else forms compile). Omitting it made the
// token decline and the run reparse as a call_statement plus loose identifiers.
// Adding a target here is free: every target is tested against ONE buffered
// read of the directive word (see peek_directive_ci_skip_extras), so a third
// entry cannot resurrect the consume-the-prefix trap described there.
static const char *const DIRECTIVE_BRANCH_OR_ENDIF[] = { "elif", "else", "endif", NULL };

// Is the buffered word one of `words`? `truncated` (the word did not fit its
// buffer) can only be a miss: every candidate fits.
static bool word_in(const char *const *words, const char *word, bool truncated) {
  if (truncated) return false;
  for (int i = 0; words[i] != NULL; i++) {
    if (strcmp(word, words[i]) == 0) return true;
  }
  return false;
}

// After `#endif`/`#else`: is the rest of the line blank but for an optional
// `//` comment? alc rejects anything else, a `/* */` comment included (AL0631).
// Reads past the token; the caller has already called mark_end.
static bool line_rest_is_blank(TSLexer *lexer) {
  while (lexer->lookahead != '\n' && is_extra_space(lexer->lookahead)) {
    lexer->advance(lexer, false);
  }
  if (lexer->lookahead == '\n' || lexer->eof(lexer)) return true;
  if (lexer->lookahead != '/') return false;
  lexer->advance(lexer, false);
  if (lexer->lookahead == '/') return true;
  // A lone '/' (`#endif /`) is part of the malformed line. Mark it here:
  // consume_line only marks characters it advances over itself, and at a
  // newline it advances over none.
  lexer->mark_end(lexer);
  return false;
}

// After `#if`/`#elif`: does a block comment open, or a second directive
// start, anywhere on the rest of the line? alc rejects both (AL0631:
// `#if A /* c */`, `#if A #region R`) where it accepts a trailing `//` comment.
// A `#` cannot occur in a condition, so any `#` before a `//` is a directive.
// Without this the second directive lexed as an extra (#region, #pragma) and
// the line parsed clean. DIRECTIVE_EOL, asked after the condition, returns
// before the '#' dispatch, so this check at the opener is where it is seen.
//
// B3: the condition must also be COMPLETE on its line. A line whose last
// condition word is `and`, `or` or `not`, or whose parentheses do not balance,
// is AL0629 (probe_alc.py dangling_*): the operand on the next line is not
// read. Without this the grammar's condition simply continued across the
// newline (DIRECTIVE_EOL cannot fire mid-expression) and absorbed it. Words
// are compared whole, so `band` and `andx` are symbols. Every check here
// works off ONE pass over the line; when the verdict is only known at its
// end, the end is marked so the MALFORMED_DIRECTIVE token still covers the
// line (consume_line only marks what it advances over).
static bool opener_line_is_malformed(TSLexer *lexer) {
  int depth = 0;           // '(' minus ')'; negative is unbalanced for good
  bool dangling = false;   // the last word read was and/or/not
  while (lexer->lookahead != '\n' && !lexer->eof(lexer)) {
    int32_t c = lexer->lookahead;
    if (c == '#') return true;
    if (c == '/') {
      lexer->advance(lexer, false);
      if (lexer->lookahead == '*') return true;
      if (lexer->lookahead == '/') break;
      dangling = false;
    } else if (is_identifier_char(c)) {
      char word[4];
      size_t len = 0;
      bool fits = read_word_ci(lexer, word, sizeof(word), &len);
      dangling = fits && (strcmp(word, "and") == 0 || strcmp(word, "or") == 0 ||
                          strcmp(word, "not") == 0);
    } else {
      if (c == '(') depth++;
      if (c == ')' && --depth < 0) return true;
      if (!is_extra_space(c)) dangling = false;
      lexer->advance(lexer, false);
    }
  }
  if (depth != 0 || dangling) {
    lexer->mark_end(lexer);
    return true;
  }
  return false;
}

// Extend the token to the last non-space character before the newline.
static void consume_line(TSLexer *lexer) {
  while (lexer->lookahead != '\n' && !lexer->eof(lexer)) {
    bool space = is_extra_space(lexer->lookahead);
    lexer->advance(lexer, false);
    if (!space) lexer->mark_end(lexer);
  }
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

    // Read the directive word ONCE. Longest AL directive is "endregion" (9).
    char word[16];
    size_t len = 0;
    bool truncated = !read_word_ci(lexer, word, sizeof(word), &len);

    if (word_in(targets, word, truncated)) return true;
    if (!word_in(TRANSPARENT_DIRECTIVES, word, truncated)) return false;

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
      valid_symbols[VAR_ATTRIBUTE_OPEN] &&
      valid_symbols[CALC_FORMULA_PROPERTY_NAME] &&
      valid_symbols[DIRECTIVE_EOL] &&
      valid_symbols[NEGATIVE_INTEGER] && valid_symbols[NEGATIVE_DECIMAL] &&
      valid_symbols[MALFORMED_DIRECTIVE] && valid_symbols[SCANNER_HOOK]) {
    return false;
  }

  // DIRECTIVE_EOL: the newline that ends an #if/#elif line. Every extra-space
  // character except `\n` before it is skipped (`is_extra_space`: `\r`, `\f`,
  // `\v` and U+FEFF as well as space and tab; skipping only space and tab left
  // `\f\n`, `\r\r\n` and the rest a hidden MISSING token that only `has_error`
  // shows). Then exactly ONE `\n` is the token, and anything
  // else declines so the grammar lexes it (`and`, `or`, `)`, or a `// comment`
  // extra, after which this is asked again at the newline). It exists because
  // a lexical `/\r?\n/` is also a whitespace separator, and the lexer's longest
  // match skipped a run of blank lines and took the LAST newline, stretching the
  // preproc_if over them. Only a condition's end offers it, and no other
  // external token is valid there outside error recovery (checked against
  // ts_external_scanner_states), so declining costs no other token its turn.
  if (valid_symbols[DIRECTIVE_EOL]) {
    while (lexer->lookahead != '\n' && is_extra_space(lexer->lookahead)) {
      lexer->advance(lexer, true);
    }
    if (lexer->lookahead != '\n') {
      return false;
    }
    lexer->advance(lexer, false);
    lexer->mark_end(lexer);
    lexer->result_symbol = DIRECTIVE_EOL;
    return true;
  }

  // NEGATIVE_INTEGER / NEGATIVE_DECIMAL: `-1` / `-1.5` as ONE signed literal
  // (issue #23), but only where it ends the value: before `;`, `,`, `#` or end
  // of input, after whitespace and comments. As a lexical token it won by
  // longest match wherever it was valid, so `Visible = -1 < Rec.O;` lexed `-1`
  // and ERRORed at `<` (grammar finding G7). Declining here lets the grammar
  // lex `-` as unary minus, giving the tree `- 1 < Rec.O` gets.
  //
  // Only a `-` commits this block: no other external token starts with one, so
  // returning false after reading it costs no later block its turn. Anything
  // else falls through with only leading whitespace skipped, which every later
  // block skips too.
  if (valid_symbols[NEGATIVE_INTEGER] || valid_symbols[NEGATIVE_DECIMAL]) {
    skip_whitespace(lexer);
    if (lexer->lookahead == '-') {
      lexer->advance(lexer, false);
      if (lexer->lookahead < '0' || lexer->lookahead > '9') {
        return false;
      }
      while (lexer->lookahead >= '0' && lexer->lookahead <= '9') {
        lexer->advance(lexer, false);
      }
      enum TokenType symbol = NEGATIVE_INTEGER;
      lexer->mark_end(lexer);
      if (lexer->lookahead == '.') {
        lexer->advance(lexer, false);
        if (lexer->lookahead < '0' || lexer->lookahead > '9') {
          return false;  // `-1.` is no literal the grammar has either
        }
        while (lexer->lookahead >= '0' && lexer->lookahead <= '9') {
          lexer->advance(lexer, false);
        }
        symbol = NEGATIVE_DECIMAL;
        lexer->mark_end(lexer);
      }
      if (!valid_symbols[symbol]) {
        return false;
      }
      if (!skip_whitespace_and_comments(lexer)) {
        return false;  // a bare '/' follows: a division, not the value's end
      }
      int32_t c = lexer->lookahead;
      if (c == ';' || c == ',' || c == '#' || lexer->eof(lexer)) {
        lexer->result_symbol = symbol;
        return true;
      }
      return false;
    }
  }

  // The '#' dispatch: PREPROC_OPEN (#if), PREPROC_CLOSE (#endif) and
  // MALFORMED_DIRECTIVE, in one block because consuming '#' is irreversible
  // within a single scanner call. It is also the gatekeeper for the directives
  // the GRAMMAR lexes (#elif, #else and the five extras): their regexes cannot
  // refuse a prefix or a trailing token, so a malformed line is claimed here
  // as MALFORMED_DIRECTIVE before the internal lexer sees it, and a well-formed
  // one is declined and lexed by its regex as before.
  //
  // It runs whatever is valid, not only when #if/#endif is: the gatekeeper has
  // to see `#elsewhere` and `#regionX` in every state. The scanner is called in
  // every state because of SCANNER_HOOK: an external token listed in grammar.js
  // `extras`, so valid everywhere, and NEVER returned by this function. Before
  // it, 3,937 of 15,870 parse states had no valid external token, so tree-sitter
  // never called the scanner there and a malformed line in those states (77 of
  // the states where #else is valid, 71 for #elif, and most mid-expression
  // positions for the extras) still lexed through the grammar's regexes. The
  // hook cannot change a tree: tree-sitter only ever receives a token this
  // function returns, the internal lexer has no definition for an external
  // token, and every token this function does return is guarded by
  // valid_symbols except MALFORMED_DIRECTIVE, which is only returned for a
  // line alc rejects. A hook-only state therefore lexes exactly as it did
  // before, except for such lines.
  //
  // No other block's token starts with '#', so declining here costs nothing
  // (the whitespace skip is the same marking skip every later block starts
  // with).
  {
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
      // return true. "endregion" (9) is the longest directive word.
      char word[12];
      size_t len = 0;
      bool truncated = !read_word_ci(lexer, word, sizeof(word), &len);
      // The token is the '#' and the word. Every check below reads past it.
      lexer->mark_end(lexer);

      static const char *const OTHERS[] = {
        "pragma", "region", "endregion", "define", "undef", NULL,
      };
      bool is_if = !truncated && strcmp(word, "if") == 0;
      bool is_elif = !truncated && strcmp(word, "elif") == 0;
      bool is_else = !truncated && strcmp(word, "else") == 0;
      bool is_endif = !truncated && strcmp(word, "endif") == 0;

      if (len == 0 || word_in(OTHERS, word, truncated)) {
        // A bare '#', or an extras directive: the grammar's regexes own those.
        return false;
      }
      enum TokenType symbol = is_if ? PREPROC_OPEN : PREPROC_CLOSE;
      if ((is_if || is_endif) && !valid_symbols[symbol]) {
        // A real directive the parser cannot take here. Declining leaves it
        // to the internal lexer, which has no token for it: an ERROR, as
        // before B2.
        return false;
      }
      // What alc lets follow the word on its line (AL0631 otherwise,
      // tools/config_oracle/probe_alc.py): after #endif/#else, only spaces
      // and an optional `//` comment; after #if/#elif, a condition with no
      // block comment and no second directive on the line. Any other word is
      // AL0621.
      bool malformed = (is_else || is_endif) ? !line_rest_is_blank(lexer)
                     : (is_if || is_elif)    ? opener_line_is_malformed(lexer)
                     : true;
      if (malformed) {
        // `#elsewhere`, `#regionX` (the extras regex matches its `#region`
        // and leaves `X` an identifier, clean in a statement list), `#endif;`.
        // No rule takes this token, so the parser wraps the whole line in an
        // ERROR. It is never valid outside error recovery, which returned
        // above, so it is emitted unasked.
        consume_line(lexer);
        lexer->result_symbol = MALFORMED_DIRECTIVE;
        return true;
      }
      if (is_elif || is_else) {
        return false;  // well-formed: the grammar's regex lexes it
      }
      if (symbol == PREPROC_OPEN) state->depth++;
      if (symbol == PREPROC_CLOSE && state->depth > 0) state->depth--;
      lexer->result_symbol = symbol;
      return true;
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
      valid_symbols[CONTINUE_AS_IDENTIFIER] || valid_symbols[PROPERTY_NAME] ||
      valid_symbols[CALC_FORMULA_PROPERTY_NAME]) {
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
      // Unreachable today, and the reason is worth stating exactly, because the
      // obvious claim — "property_name is never co-valid with begin_keyword" —
      // is FALSE: rows 28, 30, 39 and 40 offer both, which is the whole basis of the
      // `b1 = 1;` defect fixed in 4.0.0.
      //
      // Reaching this line requires !BEGIN_KEYWORD && PREPROC_SPLIT_BEGIN. In
      // ts_external_scanner_states, preproc_split_begin appears in rows 1, 13 and
      // 52 only, and rows 13 and 52 BOTH also carry begin_keyword — so the arm
      // above returns first, and row 1 is the all-thirteen recovery row the guard at
      // the top of scan() already rejects. Re-check that if a new row carries
      // preproc_split_begin without begin_keyword.
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
      // Skips the PROPERTY_NAME test below, and unlike the `begin` arm this one
      // has NO safety margin from the keyword itself. It is safe only because
      // ts_external_scanner_states pairs property_name with neither end_keyword
      // nor preproc_split_end in any row outside the all-thirteen recovery row, so
      // reaching here means property_name was not wanted anyway. That is a real
      // dependency on the generated table — a property named `end` in a state
      // that also wanted END_KEYWORD would be dropped. Re-check after any change
      // that adds an external or moves a rule between object and statement
      // bodies.
      return false;
    }

    // PROPERTY_NAME is tested before CONTINUE_AS_IDENTIFIER on purpose: the
    // continue test consumes the ':' of ':=' and would leave a bare '=' for the
    // property test to misread, whereas testing for '=' first consumes nothing
    // the continue test needs. (No parse state offers both — see the
    // ts_external_scanner_states table — but unlike the two arms above, this
    // ORDER does not depend on that holding.)
    if (valid_symbols[PROPERTY_NAME] || valid_symbols[CALC_FORMULA_PROPERTY_NAME]) {
      // Skip whitespace and comments. '\n' belongs here just as much as '\r' —
      // the leading skip above already accepts it, and alc accepts a property
      // whose '=' sits on the next line (verified). Omitting it made
      // `Caption\n    = 'Test';` an ERROR that the compiler compiles fine.
      // A bare '/' is not a comment and is not '=', so declining on it loses
      // nothing.
      if (!skip_whitespace_and_comments(lexer)) return false;
      if (lexer->lookahead == '=') {
        // CalcFormula is the one property keyed by NAME: its value has a
        // grammar of its own (sum/count/exist/min/max/average/lookup over a
        // field reference), and `sum("T".N)` is also a complete call
        // expression, so the generic property rule could only ever reach it
        // by a GLR tiebreak -- which went the wrong way for every aggregate
        // without a where(): 22 of BC.History's 2,553 CalcFormula sites, in
        // 12 files (issue #21). Only the property NAME separates
        // `CalcFormula = Count(X)` from `DataCaptionExpression = Caption(Rec)`,
        // so the name is what this reads. Falls back to PROPERTY_NAME where
        // the grammar does not offer the keyed token, so a state that only
        // knows the generic property keeps working.
        lexer->result_symbol =
            (word == WORD_CALCFORMULA && valid_symbols[CALC_FORMULA_PROPERTY_NAME])
                ? CALC_FORMULA_PROPERTY_NAME
                : PROPERTY_NAME;
        if (lexer->result_symbol == PROPERTY_NAME && !valid_symbols[PROPERTY_NAME]) {
          return false;
        }
        return true;
      }
    }

    if (word == WORD_CONTINUE && valid_symbols[CONTINUE_AS_IDENTIFIER]) {
      // `continue` is a NAME, not the statement, when what follows is
      // something no continue statement can be followed by: a call `(`, a
      // member `.`, a subscript `[`, an enum qualifier `::`, or an assignment
      // operator := += -= *= /=. Until 4.1.0 only `:=` was tested, so
      // `Continue(X);` parsed as continue_statement plus a stranded
      // parenthesized_expression with no ERROR, and `Continue.Field := 1;`
      // was an ERROR (issue #22). A statement is followed by ; end else
      // until or a directive, none of which appear here, so nothing that IS a
      // continue statement is affected -- BC.History's 7 bare `continue;`
      // included. Advancing past the first char of a two-char operator and
      // finding no '=' returns false, which discards the advance and lets the
      // grammar lex the keyword; that is the pre-existing `:` behaviour.
      skip_whitespace_nomark(lexer);
      int32_t c = lexer->lookahead;
      if (c == '(' || c == '.' || c == '[') {
        lexer->result_symbol = CONTINUE_AS_IDENTIFIER;
        return true;
      }
      if (c == ':') {
        lexer->advance(lexer, false);
        if (lexer->lookahead == '=' || lexer->lookahead == ':') {
          lexer->result_symbol = CONTINUE_AS_IDENTIFIER;
          return true;
        }
      } else if (c == '+' || c == '-' || c == '*' || c == '/') {
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
