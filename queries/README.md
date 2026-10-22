# Queries

Tree-sitter query files for the AL grammar. `tree-sitter.json` registers `highlights`, `tags` and `locals`;
editors that use the other three load them by name.

| file | captures | used for |
|---|---|---|
| `highlights.scm` | `@keyword`, `@type`, `@function`, `@variable`, `@property`, `@constant`, `@operator`, ... | syntax highlighting |
| `locals.scm` | `@local.scope`, `@local.definition`, `@local.reference` | scope-aware highlighting of variables and parameters |
| `tags.scm` | `@definition.*`, `@reference.*`, `@name` | symbol lists, go to definition (`tree-sitter tags`) |
| `indents.scm` | `@indent.begin`, `@indent.end`, `@indent.branch` | auto-indentation |
| `folds.scm` | `@fold` | code folding |
| `textobjects.scm` | `@function.inside` / `.around`, `@class.inside`, `@block.inside`, `@comment.inside`, ... | structural selection and motion |

Read a keyword's text from the keyword node itself (`(if_keyword) @keyword`), never from its anonymous child: the
two external keywords `begin_keyword` and `end_keyword` have no child (CLAUDE.md, "Keyword Architecture").

## `#if` inside expressions

An `#if` group may stand inside an expression, as a tail (`preproc_conditional_expression_tail`), an operand prefix
(`preproc_operand_prefix`) or a whole operand (`preproc_conditional_operand`). In an expression region that contains
such a group, the nesting of the binary and unary nodes is **not** a grouping claim: a query that reads the operands
of an `additive_expression` there sees the tree as written, not the meaning of any one configuration. To get the
meaning, splice the active arm, flatten and regroup by the operator ladder, as
[`docs/expression-regions.md`](../docs/expression-regions.md) states (which edges are region edges, which region
each group belongs to, the ladder, worked trees). Patterns that only capture a node (a name, a literal, an operator
token) are unaffected.
