---
name: External Scanner Techniques
description: Advanced patterns for tree-sitter external scanners learned from 10+ parsers. Use when choosing scanner architecture (stateless vs stateful), implementing heredocs, indentation tracking, nested string interpolation, or debugging scanner issues. Covers decision trees, 6 major patterns (pure grammar, stateless, single-value, stack-based, heredoc, zero-width), token placement rules, and serialization best practices.
---

# External Scanner Techniques

Advanced scanner patterns. See `references/techniques.md` for detailed documentation.

## Decision Tree: Do I Need Scanner State?

```
Does the construct need lookahead?
├─ No → Use pure grammar (no scanner)
└─ Yes → Does parser track context via valid_symbols[]?
    ├─ Yes → Stateless scanner
    └─ No → Does the construct nest?
        ├─ No → Single-value state
        └─ Yes → Stack-based state
```

## Pattern Quick Reference

| Scenario | Pattern | Source |
|----------|---------|--------|
| Context-dependent constructs | Pure grammar with helper | tree-sitter-c |
| Character-level disambiguation | Stateless + valid_symbols | tree-sitter-elixir |
| Paired delimiters | Single-value state | tree-sitter-rust |
| Indentation/nesting | Stack-based state | tree-sitter-python |
| Multi-line heredocs | Stack + dynamic strings | tree-sitter-bash |
| Structural boundaries | Zero-width tokens | tree-sitter-yaml |

## Critical Token Placement Rules

**DO**: Place tokens in `choice()` at decision points:
```javascript
repeat(choice(
    $.normal_pattern,
    $.scanner_token  // Parser can choose
))
```

**DON'T**: Place tokens after structural boundaries:
```javascript
seq(
    repeat($.normal_pattern),
    optional($.scanner_token)  // Too late!
)
```

## Debug Technique

```c
if (valid_symbols[MY_TOKEN]) {
    fprintf(stderr, "SCANNER: MY_TOKEN valid at '%c'\n",
            lexer->lookahead >= 32 ? lexer->lookahead : '?');
}
```

If scanner called at unexpected positions, token placement is wrong.

## Serialization Template

```c
unsigned serialize(Scanner *s, char *buf) {
    size_t n = 0;
    buf[n++] = s->flag;
    buf[n++] = s->stack.size;
    for (uint32_t i = 0; i < s->stack.size && n < 1024; i++)
        buf[n++] = s->stack.contents[i];
    return n;
}
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Wrong call positions | Token after repeat() | Move to choice() |
| State lost | Bad serialization | Verify roundtrip |
| Infinite loop | Not advancing | Call advance() |
