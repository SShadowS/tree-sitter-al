// fieldwalk.c — print the field name the TREE CURSOR reports for every node,
// including anonymous ones.
//
// WHY THIS EXISTS
// ---------------
// To answer "does field X actually contain node Y?" you must ask the tree
// cursor, because that is what the language bindings' children_by_field_name()
// uses. The obvious tools cannot answer it:
//
//   * `tree-sitter parse -c` / `--xml` do NOT print field names on ANONYMOUS
//     nodes. Proof: `additive_expression.operator` is a declared field whose
//     only members are the anonymous '+' / '-', and `-c` prints that "+" with
//     no field prefix. So punctuation always *looks* field-less under `-c`,
//     whether or not it carries the field. Reading "the ',' has no field" off
//     `-c` is reading the tool's blind spot, and it has produced wrong
//     conclusions in this repo before.
//   * `tree-sitter query` disagrees with the cursor: given
//     `(record_type reference: _ @r)` over a three-part dotted name it reports
//     only the FIRST part.
//
// A field that wraps a whole `seq` silently labels the separators inside it
// (`field('sizes', seq(int, repeat(seq(',', int))))` labels the ','), which is
// invisible in the parse tree and visible only here and in node-types.json.
// tools/check-field-types.py asserts the node-types.json side; this tool
// establishes the runtime ground truth behind those assertions.
//
// BUILD (from the repo root; the vendored runtime is fetched by
// bindings/c/build.sh, default .cache/tree-sitter-0.25.10):
//
//   TS=.cache/tree-sitter-0.25.10/lib
//   gcc -O1 -o fieldwalk tools/fieldwalk.c src/parser.c src/scanner.c \
//       $TS/src/lib.c -I$TS/include -I$TS/src -Isrc
//
// USAGE
//
//   fieldwalk <file.al>                    # whole tree, each node prefixed
//                                          # "field: " when it carries one
//   fieldwalk <file.al> <node_type> <field>
//                                          # for every <node_type>, list only
//                                          # the children carrying <field>
//
// Example — the shape a seq-spanning field produces:
//
//   $ fieldwalk probe.al record_type reference
//   parse: HAS_ERROR=no
//   == record_type [60,90)
//      FIELD reference -> identifier  text=`System`
//      FIELD reference -> . (ANON)  text=`.`      <-- the defect
//      FIELD reference -> identifier  text=`Reflection`
//
// READING THE OUTPUT — the two blank results mean different things:
//
//   "== <type> ..." with no FIELD rows under it
//        The node exists and carries NO child with that field. This is a real
//        answer: field present, no members (or the field name is misspelled).
//   "0 nodes of type <type> found"
//        The construct never reduced to that node type -- usually the probe
//        does not exercise it, or it did not parse. This is NOT evidence about
//        the field. Fix the probe and re-run.
//
// Always read the `parse: HAS_ERROR=` line first. A probe that fails to parse
// silently produces no rows, and a blank result trusted at face value is
// exactly the false negative that produced two wrong verdicts in this repo
// before this tool existed. A miss is printed loudly for that reason.
//
// To compare against an older parser, extract it first
// (`git show <rev>:src/parser.c > old/parser.c`, likewise scanner.c, and copy
// src/tree_sitter/ next to it) and build against those sources instead.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "tree_sitter/api.h"

const TSLanguage *tree_sitter_al(void);

static char *slurp(const char *path, size_t *len) {
  FILE *f = fopen(path, "rb");
  if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(2); }
  fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
  if (n < 0) { fprintf(stderr, "cannot size %s\n", path); exit(2); }
  char *b = malloc((size_t)n + 1);
  if (!b) { fprintf(stderr, "out of memory reading %s\n", path); exit(2); }
  size_t got = fread(b, 1, (size_t)n, f);
  b[got] = 0; *len = got; fclose(f); return b;
}

// Walk with an explicit cursor, printing the field name of each child.
// ts_tree_cursor_current_field_name() is the call that matters: it is what the
// bindings use, and unlike the CLI's printers it reports fields on anonymous
// nodes too.
static void walk(TSTreeCursor *c, int depth) {
  TSNode node = ts_tree_cursor_current_node(c);
  const char *field = ts_tree_cursor_current_field_name(c);
  for (int i = 0; i < depth; i++) fputs("  ", stdout);
  printf("%s%s%s%s  [%u,%u)\n",
         field ? field : "",
         field ? ": " : "",
         ts_node_type(node),
         ts_node_is_named(node) ? "" : "  (ANON)",
         ts_node_start_byte(node), ts_node_end_byte(node));
  if (ts_tree_cursor_goto_first_child(c)) {
    do { walk(c, depth + 1); } while (ts_tree_cursor_goto_next_sibling(c));
    ts_tree_cursor_goto_parent(c);
  }
}

int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: fieldwalk <file.al> [node_type field]\n");
    return 2;
  }
  size_t len; char *src = slurp(argv[1], &len);
  TSParser *p = ts_parser_new();
  if (!ts_parser_set_language(p, tree_sitter_al())) {
    fprintf(stderr, "ABI MISMATCH: could not set language "
                    "(runtime too old for this parser?)\n");
    return 3;
  }
  TSTree *t = ts_parser_parse_string(p, NULL, src, (uint32_t)len);
  TSNode root = ts_tree_root_node(t);

  // Report parse health unconditionally. A probe that failed to parse produces
  // no rows in targeted mode, which is indistinguishable from "the field has no
  // members" unless the failure is stated out loud.
  int had_error = ts_node_has_error(root);
  printf("parse: HAS_ERROR=%s\n", had_error ? "YES -- results below are unreliable" : "no");

  if (argc >= 4) {
    // Targeted mode: for every node of type argv[2], list the children that
    // carry field argv[3]. This is exactly children_by_field_name(argv[3]).
    const char *want_type = argv[2], *want_field = argv[3];
    TSTreeCursor c = ts_tree_cursor_new(root);
    int done = 0, matched = 0;
    while (!done) {
      TSNode n = ts_tree_cursor_current_node(&c);
      if (strcmp(ts_node_type(n), want_type) == 0) {
        matched++;
        printf("== %s [%u,%u)\n", want_type,
               ts_node_start_byte(n), ts_node_end_byte(n));
        TSTreeCursor ic = ts_tree_cursor_new(n);
        if (ts_tree_cursor_goto_first_child(&ic)) {
          do {
            const char *f = ts_tree_cursor_current_field_name(&ic);
            if (f && strcmp(f, want_field) == 0) {
              TSNode cn = ts_tree_cursor_current_node(&ic);
              uint32_t s = ts_node_start_byte(cn), e = ts_node_end_byte(cn);
              printf("   FIELD %s -> %s%s  text=`%.*s`\n", f, ts_node_type(cn),
                     ts_node_is_named(cn) ? "" : " (ANON)",
                     (int)(e - s), src + s);
            }
          } while (ts_tree_cursor_goto_next_sibling(&ic));
        }
        ts_tree_cursor_delete(&ic);
      }
      if (ts_tree_cursor_goto_first_child(&c)) continue;
      while (!ts_tree_cursor_goto_next_sibling(&c)) {
        if (!ts_tree_cursor_goto_parent(&c)) { done = 1; break; }
      }
    }
    ts_tree_cursor_delete(&c);
    if (matched == 0) {
      // Loud, and distinct from "found the node, it has no such field child" --
      // conflating the two is how a blank result gets mistaken for evidence.
      printf("0 nodes of type %s found -- this says NOTHING about field '%s'; "
             "the probe does not exercise that construct%s\n",
             want_type, want_field,
             had_error ? " (and the file did not parse cleanly)" : "");
      return 1;
    }
  } else {
    TSTreeCursor c = ts_tree_cursor_new(root);
    walk(&c, 0);
    ts_tree_cursor_delete(&c);
  }
  return 0;
}
