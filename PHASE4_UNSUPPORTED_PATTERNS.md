# Phase 4: Unsupported Patterns After Rust-Style Refactor

After Phase 4, the following patterns are **no longer supported**:

## 1. Attributes Inside Preprocessor Branches

**Old pattern (no longer supported):**
```al
#if CONDITION
[Attribute1]
procedure Proc()
#else
[Attribute2]  
procedure Proc()
#endif
begin
end;
```

**New pattern (required):**
```al
[Attribute]
#if CONDITION
procedure Proc()
#endif
begin
end;
```

## Affected Tests (5)

These tests document the old patterns and will remain failing:

1. **Multiple attributes in preprocessor branch** - Tests `preproc_attributed_split_procedure` with multiple attributes in different branches
2. **Preprocessor conditional splitting procedure header** - Tests preprocessor splitting procedure with attributes
3. **Preprocessor directives wrapping attributes for procedures** - Tests attributes wrapped in preprocessor
4. **Preprocessor split between procedure header and body** - Tests split with attributes
5. **Preprocessor conditional with split procedure header** - Tests conditional split headers with attributes

## Rationale

The Rust-style refactor treats attributes as **statements** (peers with declarations), not embedded within them. This means attributes must appear at the statement level, not inside preprocessor conditional branches that split declaration headers.

**Benefits:**
- ✅ Simpler grammar (no `attributed_*` wrappers)
- ✅ Consistent with Rust/C# patterns
- ✅ Fixes core limitation: `[Attr] #if CONDITION procedure Proc() #endif` now works
- ✅ Clearer parse trees

**Migration:**
Move all attributes outside and before preprocessor blocks.
