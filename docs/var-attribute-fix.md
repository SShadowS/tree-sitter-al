# Fix: var_section greedily consuming procedure-level attributes

## Bug

`var_section` swallows `[Test]` and other attributes that belong to procedures:

```al
var
    Assert: Codeunit Assert;

[Test]                    // <-- gets consumed by var_section (WRONG)
procedure TestMethod()
begin end;
```

## Root Cause

`var_section` has `repeat(choice(..., $.attribute_item, ...))`. In LR parsing, `[` is an unambiguous shift into the repeat — not a conflict. No `prec`/conflict declaration can fix this.

## Why attribute_item is in var_section

Variable-level attributes are valid AL:
```al
var
    [NonDebuggable]
    Secret: Text;
```

## Fix: External Scanner Token `VAR_ATTRIBUTE_OPEN`

### Scanner Logic

When `VAR_ATTRIBUTE_OPEN` is in `valid_symbols`:
1. Check lookahead is `[`
2. Advance past entire `[...]` (track bracket/paren depth for arguments)
3. Skip whitespace after `]`
4. If next is `identifier :` or `"quoted" :` or `[` (another attribute) → emit token
5. Otherwise → decline (body-level attribute)

### Grammar Changes

```javascript
// externals: add $.var_attribute_open

// New rule:
var_attribute_item: $ => seq(
  $.var_attribute_open,  // scanner token replaces '['
  field('attribute', $.attribute_content),
  ']'
),

// var_section: replace $.attribute_item with $.var_attribute_item
var_section: $ => prec.right(seq(
  optional(choice($.protected_keyword, $.local_keyword)),
  $.var_keyword,
  repeat(choice(
    $.variable_declaration,
    $.var_attribute_item,       // was: $.attribute_item
    $.preproc_conditional_var,
    $.preproc_split_procedure,
  )),
)),
```

### Scanner Implementation (src/scanner.c)

Add to TokenType enum:
```c
VAR_ATTRIBUTE_OPEN = 8,
```

Add scan logic after PREPROC_SPLIT_END, before CONTINUE_AS_IDENTIFIER:
```c
if (valid_symbols[VAR_ATTRIBUTE_OPEN]) {
  skip_whitespace(lexer);
  if (lexer->lookahead == '[') {
    // Save position, scan past [...], check what follows
    // If followed by identifier: or "quoted": or [ → emit
    // Otherwise → decline
  }
}
```

### Key Lookahead Details

After `]`, skip whitespace, then check:
- `[` → another attribute → emit (variable can have multiple attrs)
- Letter or `_` → could be identifier → scan identifier, skip ws, check for `:` (not `:=`)
- `"` → quoted identifier → scan to closing `"`, skip ws, check for `:`
- Anything else → NOT a variable declaration → decline

### Files to Modify

1. `src/scanner.c` — Add VAR_ATTRIBUTE_OPEN token + scan logic
2. `grammar.js` — Add to externals, add var_attribute_item rule, update var_section

### Test Cases

```al
// Must work: variable attribute stays in var_section
var [NonDebuggable] Secret: Text;

// Must work: [Test] NOT consumed by var_section
var X: Integer;
[Test] procedure P() begin end;

// Must work: multiple attrs on variable
var [InDataSet] [NonDebuggable] Y: Boolean;

// Must work: [Test] after var inside #if block
#if CLEAN26
var X: Integer;
[Test] procedure P() begin end;
#endif
```
