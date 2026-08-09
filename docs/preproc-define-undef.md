# `#define` and `#undef` support

AL has two symbol-definition preprocessor directives that the grammar did not
recognise until now: `#define` and `#undef`. Microsoft documents both in the
[conditional directives table][ms-docs], and Microsoft's own Highlight.js
grammar (`highlightjs_al/src/al.js` in [microsoft/AL][ms-al]) lists them
alongside `if`/`else`/`elif`/`endif`/`region`/`endregion`/`pragma`.

The gap went unnoticed because BC.History contains zero occurrences of either
directive — the base application declares its symbols through the
`preprocessorSymbols` setting in `app.json` instead of in source. The production
corpus therefore gives no regression signal here, and the fixtures in
`test/corpus/preproc_define_undef_test.txt` are synthetic.

## What the AL compiler actually accepts

The rules below were established by compiling probe files with `alc 18.0.37`,
not inferred from the documentation. Each case was a standalone project
compiled with `al compile /project:. /out:out.app /packagecachepath:.alpackages`;
"accepted" means exit 0 with an `.app` written.

Accepted:

| Case | Example |
|------|---------|
| At the top of the file | `#define DEBUG` before any object |
| `#undef` | `#define DEBUG` then `#undef DEBUG` |
| `#undef` of a symbol never defined | `#undef NEVERDEFINED` |
| Whitespace after `#` | `# define DEBUG`, `#\tundef DEBUG` |
| Any casing | `#DEFINE`, `#UNDEF`, `#Define`, `#UnDef` |
| Leading indentation | `   #define DEBUG` |
| After leading comments | line comments and block comments both |
| After a leading `#pragma` or `#region` | |
| Inside a leading `#if`/`#else`/`#endif` | including in the `#else` branch |
| Before `namespace` | `#define DEBUG` then `namespace Probe.Test;` |
| Trailing line comment | `#define DEBUG // enable` |
| Symbol used in a later `#if` | `#define DEBUG` … `#if DEBUG` |
| Underscores and digits in the symbol | `#define _DEBUG_1` |

Rejected:

| Case | Compiler error |
|------|----------------|
| After the first real token of the file | `AL0625: Cannot define/undefine preprocessor symbols after first token in file` |
| Inside an object body, a trigger body, a `var` section, a table `fields` section | `AL0625` |
| After a `namespace` or `using` declaration | `AL0625` |
| Between two object declarations | `AL0625` |
| No symbol name | `AL0107: Syntax error, identifier expected` |
| Quoted symbol name (`#define "My Symbol"`) | `AL0107` |
| A second token after the symbol (`#define DEBUG EXTRA`) | `AL0631: Single-line comment or end-of-line expected` |
| A trailing block comment (`#define DEBUG /* nope */`) | `AL0631` |
| `#` and the directive on different lines | `AL0621: Preprocessor directive expected` |

So the window is narrow: before the first real token, though comments and any
number of `#pragma`, `#region`/`#endregion` and `#if`/`#endif` blocks may
precede or wrap the directive.

## How the grammar models it

`preproc_define` and `preproc_undef` are single-line regex tokens registered in
`extras`, exactly like `pragma`, `preproc_region` and `preproc_endregion`:

```javascript
preproc_define: $ => new RustRegex('(?i)#[ \\t]*define[^\\n\\r]*'),
preproc_undef:  $ => new RustRegex('(?i)#[ \\t]*undef[^\\n\\r]*'),
```

The `[ \t]*` (never `\s*`) between `#` and the keyword is the same guard the
other directive tokens carry — the regex crate's `\s` matches `\n`, which would
let the token span a newline and swallow real source on the next line.

The `extras` placement is deliberately more permissive than the compiler. Per
the project's "parse structure, don't validate" principle, `AL0625` is a
positional semantic check that belongs in a linter or LSP server, not in the
parser. Registering the directives as extras also buys reachability for free:
file-leading position, inside a leading pragma-only `#if` block, and after
leading comments and pragmas are all the same rule, with no new parser states
and no GLR conflicts. Modelling them on `preproc_if` instead would have needed
new conditional-body rules to cover the wrapped-in-`#if` case.

Neither directive touches the scanner's `#if`/`#endif` depth counter — they are
line-level and open nothing.

## Scanner lookahead

`src/scanner.c` scans ahead past `#`-led lines in `peek_directive_ci_skip_extras`
(formerly `peek_keyword_ci_skip_pragma`), used by `PREPROC_SPLIT_BEGIN` to check
whether `begin` is immediately followed by `#endif`, and by `PREPROC_SPLIT_END`
for `#else`/`#endif`. Extras are transparent to the parse tree, so that lookahead
has to step over all of them, not just `#pragma`.

The helper reads the directive word after `#` once into a buffer and then
classifies it, instead of trying candidate keywords one after another.
Consuming `#` is irreversible within a single scan, and so is consuming the
shared `end` prefix of `endif` and `endregion` — a sequential match on
`endregion` would have destroyed the ability to then match `endif`. The
transparent set is `pragma`, `region`, `endregion`, `define`, `undef`
(`TRANSPARENT_DIRECTIVES`), and must be kept in sync with the `extras` array in
`grammar.js`. Comments are extras too and are handled by
`skip_whitespace_and_comments` rather than by that list.

Adding `region`/`endregion` to that set is a behaviour change beyond
`#define`/`#undef`: previously a `#region` line between a split `begin` and its
`#endif` blocked `PREPROC_SPLIT_BEGIN`. It is covered by a fixture, and
`tools/tree-harness.sh` confirmed all 15,358 BC.History parse trees are
byte-identical before and after, so no production file relied on the old
behaviour.

The other two places the scanner consumes `#` need no change:

- `PREPROC_OPEN`/`PREPROC_CLOSE` dispatch — on `#define` it consumes `#`, fails
  both `if` and `endif`, and returns false. Tree-sitter discards the advances
  and the internal lexer then matches the extras regex. This is the same path
  `#pragma` and `#region` already take.
- `PREPROC_SPLIT_END`'s check for `;` followed by `#else`/`#endif` — a
  `#define` can never legally sit there, and it did not skip `#pragma` there
  either.

## Related grammars with the same gap

- `U:\Git\sublime-al` — the preprocessor context in `AL.sublime-syntax` listed
  only `if`, `elif`, `else`, `endif`, `pragma`, `region`, `endregion`.
- The [Pygments AL lexer][pygments] already recognises both directives and is a
  usable cross-check.

[ms-docs]: https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/directives/devenv-directives-in-al
[ms-al]: https://github.com/microsoft/AL
[pygments]: https://github.com/pygments/pygments/pull/3246
