// edge-census.c — corpus-wide (parent, field, child) EDGE census.
//
// WHAT IT ANSWERS, AND WHY NOTHING ELSE DOES
// ------------------------------------------
// Are the right nodes attached to the right PARENTS? An attachment change can
// preserve every node type AND every byte span, so a tree hash, an error count,
// `parse-al-parallel.sh` and a node-type census are all blind to it. That class
// fooled this project repeatedly: a clean error count never meant a correct
// tree. A node-type census tells you the right nodes exist; only an edge census
// tells you they hang off the right parents.
//
// It walks a **TSTreeCursor**, which is what `children_by_field_name()` uses, so
// it sees fields on ANONYMOUS nodes. `tree-sitter parse -c` does not print those
// at all — `additive_expression.operator`'s only members are the anonymous '+'
// and '-', and `-c` shows them with no field prefix, so punctuation always
// *looks* field-less there whether or not it carries the field. Reading that
// blind spot as evidence has produced wrong conclusions here before.
//
// FOUR DESIGN NOTES, each a reason it works rather than a detail
// --------------------------------------------------------------
//  1. Cursor, not `parse -c` — see above.
//  2. Anonymous children are recorded as the literal `(anon)`, never their
//     text. That keeps the edge-kind vocabulary BOUNDED (912 kinds on
//     BC.History); recording the text would grow it by one kind per distinct
//     token per field.
//
//     THIS IS WHY THIS TOOL AND detectors/edges.py REPORT DIFFERENT KIND
//     COUNTS ON THE SAME INPUT, and neither is wrong. edges.py keys anonymous
//     children by `child.type`, i.e. the token text, deliberately -- it wants
//     `(additive_expression, operator, "+")` and `…"-"` to be separate kinds,
//     because telling `+` from `-` in an operator field is its whole job.
//     Reconciled exactly on 2de0825 over BC.History, both at 13,339,003
//     fielded edges and 35,601,750 nodes:
//
//       907 named-child kinds -- IDENTICAL in both
//       +  5  this tool: one `(anon)` bucket per (parent, field)   = 912
//       + 13  edges.py:  one kind per distinct token               = 920
//
//     The +8 is four operator fields splitting:
//       additive_expression.operator        +1   '+' '-'
//       logical_expression.operator         +2   'and' 'or' 'xor'
//       multiplicative_expression.operator  +3   '*' '/' 'div' 'mod'
//       unary_expression.operator           +2   '+' '-' 'not'
//
//     Do NOT "reconcile" them by changing either rule. Quote 912 for this
//     tool and 920 for edges.py, and never mix the two in one comparison.
//  3. **The hash table hard-exits if it fills.** It must. Silent truncation
//     would emit a SMALLER, entirely plausible census — a green reading from a
//     broken instrument, which is the exact failure mode this tool exists to
//     catch. A detector for that class must not be capable of it.
//  4. **Every count prints through `%llu` with an explicit cast, never `%zu`.**
//     Same principle as 3, and it shipped broken for two minutes: MinGW binds
//     printf to msvcrt, whose format parser does not know `z`, so the edge-kind
//     total printed as literal garbage on an ordinary Windows toolchain. A
//     wrong headline number out of the one instrument whose whole job is to be
//     trusted about numbers. Build with `-Wall`; gcc catches it as -Wformat.
//     (Corroboration that this is real and not theoretical: tree-sitter's own
//     vendored `alloc.c` trips the same warning under MinGW.)
//
// COSTS NO LOCK — THIS IS THE PROPERTY THAT MAKES IT USABLE
// ---------------------------------------------------------
// The parser is STATICALLY LINKED here, so this binary never touches the shared
// `al.dll` that `tools/ts-lock.sh` serialises. `tree-sitter generate` needs no
// lock either (it writes only your worktree's `src/`). A full before/after
// census therefore costs **zero** lock time and can run while everyone else is
// building. Do not wrap it in ts-lock.
//
// BUILD (from repo root):
//   TS=.cache/tree-sitter-0.25.10/lib
//   gcc -O2 -o census tools/edge-census.c src/parser.c src/scanner.c
//         $TS/src/lib.c -I$TS/include -I$TS/src -Isrc
//   (one command; no trailing backslashes here because a '\' at the end of a
//    '//' line continues the COMMENT and trips -Wcomment)
//
// RUN:
//   find ./BC.History/ -name '*.al' -type f | sort > corpus.txt
//   ./census corpus.txt > edges.tsv        # ~23 s for 15,358 files
//
// stdout is `count<TAB>parent<TAB>field<TAB>child`, sorted, so two runs diff
// cleanly. stderr carries the totals (files, nodes, fielded edges, edge kinds).
//
// COMPARING ACROSS A CHANGE NEEDS **TWO BINARIES**
// -----------------------------------------------
// The parser is linked in, so the binary embeds the grammar it was built from.
// Build one binary per side and diff the TSVs:
//
//   <apply your change>  ; tree-sitter generate ; build -> census-after  ; run
//   <revert the change>  ; tree-sitter generate ; build -> census-before ; run
//   diff <(sort edges-before.tsv) <(sort edges-after.tsv)
//
// Rebuilding ONE binary and running it twice yields an identical census that
// proves nothing whatsoever. If your diff is empty, check that you really built
// two binaries before concluding the change moved no edges.
//
// Reference point, BC.History at 4.0.0: 15,358 files, ~35.6M nodes,
// **13,339,003 fielded edges**, ~912 edge kinds. Three independently written
// implementations have agreed on the edge count.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "tree_sitter/api.h"

const TSLanguage *tree_sitter_al(void);

// ---- open-addressing string->count map -------------------------------------
#define CAP (1u << 21)
typedef struct { char *key; uint64_t n; } Slot;
static Slot *tab;
static size_t used;

static uint64_t fnv(const char *s) {
  uint64_t h = 1469598103934665603ULL;
  for (; *s; s++) { h ^= (unsigned char)*s; h *= 1099511628211ULL; }
  return h;
}

static void bump(const char *key) {
  size_t i = fnv(key) & (CAP - 1);
  while (tab[i].key) {
    if (strcmp(tab[i].key, key) == 0) { tab[i].n++; return; }
    i = (i + 1) & (CAP - 1);
  }
  tab[i].key = strdup(key);
  tab[i].n = 1;
  if (++used > CAP / 2) { fprintf(stderr, "census: table full\n"); exit(2); }
}

static int cmp(const void *a, const void *b) {
  const Slot *x = a, *y = b;
  return strcmp(x->key, y->key);
}

// ---- walk ------------------------------------------------------------------
static uint64_t edges_total, nodes_total;

static void walk(TSNode node, TSTreeCursor *c) {
  if (!ts_tree_cursor_goto_first_child(c)) return;
  const char *parent = ts_node_type(node);
  do {
    TSNode child = ts_tree_cursor_current_node(c);
    nodes_total++;
    const char *field = ts_tree_cursor_current_field_name(c);
    if (field) {
      char key[512];
      snprintf(key, sizeof(key), "%s\t%s\t%s", parent, field,
               ts_node_is_named(child) ? ts_node_type(child) : "(anon)");
      bump(key);
      edges_total++;
    }
    walk(child, c);
  } while (ts_tree_cursor_goto_next_sibling(c));
  ts_tree_cursor_goto_parent(c);
}

int main(int argc, char **argv) {
  if (argc < 2) { fprintf(stderr, "usage: census <filelist>\n"); return 2; }
  tab = calloc(CAP, sizeof(Slot));
  if (!tab) return 2;

  FILE *lf = fopen(argv[1], "rb");
  if (!lf) { perror("filelist"); return 2; }

  TSParser *parser = ts_parser_new();
  ts_parser_set_language(parser, tree_sitter_al());

  char path[4096];
  uint64_t files = 0, failed = 0;
  while (fgets(path, sizeof(path), lf)) {
    size_t L = strlen(path);
    while (L && (path[L-1] == '\n' || path[L-1] == '\r')) path[--L] = 0;
    if (!L) continue;

    FILE *f = fopen(path, "rb");
    if (!f) { failed++; continue; }
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    char *buf = malloc((size_t)sz + 1);
    if (!buf) { fclose(f); failed++; continue; }
    size_t got = fread(buf, 1, (size_t)sz, f);
    buf[got] = 0;
    fclose(f);

    TSTree *tree = ts_parser_parse_string(parser, NULL, buf, (uint32_t)got);
    TSNode root = ts_tree_root_node(tree);
    TSTreeCursor cur = ts_tree_cursor_new(root);
    nodes_total++;
    walk(root, &cur);
    ts_tree_cursor_delete(&cur);
    ts_tree_delete(tree);
    free(buf);
    files++;
  }
  fclose(lf);
  ts_parser_delete(parser);

  // stable, sorted output so two runs diff cleanly
  Slot *out = malloc(used * sizeof(Slot));
  size_t k = 0;
  for (size_t i = 0; i < CAP; i++) if (tab[i].key) out[k++] = tab[i];
  qsort(out, k, sizeof(Slot), cmp);
  for (size_t i = 0; i < k; i++) printf("%llu\t%s\n", (unsigned long long)out[i].n, out[i].key);

  // Every count goes through %llu with an explicit cast. NOT %zu: MinGW binds
  // printf to msvcrt, whose format parser does not know 'z', so the edge-kind
  // count would print as literal garbage on a perfectly ordinary Windows
  // toolchain -- a wrong headline number from a tool whose whole job is to be
  // trusted about numbers. gcc catches it as -Wformat, so build with -Wall.
  fprintf(stderr, "census: %llu files (%llu unreadable), %llu nodes, "
                  "%llu fielded edges, %llu edge kinds\n",
          (unsigned long long)files, (unsigned long long)failed,
          (unsigned long long)nodes_total, (unsigned long long)edges_total,
          (unsigned long long)k);
  return 0;
}
