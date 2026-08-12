# Python Package Modernization for code-graph-rag Compatibility

This tree-sitter-al grammar needs its Python bindings updated to match the modern tree-sitter ecosystem conventions (as used by tree-sitter-python v0.25.0) before it can be integrated into [code-graph-rag](https://github.com/vitali87/code-graph-rag).

**Target compatibility:** `tree-sitter==0.25.2` (used by code-graph-rag)

## What needs to change

### 1. `binding.c` — Switch from `PyLong_FromVoidPtr` to `PyCapsule`

The current binding returns a raw pointer. Modern tree-sitter (0.24+) expects a `PyCapsule`.

**Current** (`bindings/python/tree_sitter_al/binding.c`):
```c
static PyObject* _binding_language(PyObject *self, PyObject *args) {
    return PyLong_FromVoidPtr(tree_sitter_al());
}
// ... uses PyModule_Create with m_size = -1
```

**Should become:**
```c
static PyObject* _binding_language(PyObject *Py_UNUSED(self), PyObject *Py_UNUSED(args)) {
    return PyCapsule_New(tree_sitter_al(), "tree_sitter.Language", NULL);
}

static struct PyModuleDef_Slot slots[] = {
#ifdef Py_GIL_DISABLED
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, NULL}
};

// ... module def uses .m_size = 0, .m_slots = slots
// PyInit__binding returns PyModuleDef_Init(&module) instead of PyModule_Create(&module)
```

Reference: `other-languages/tree-sitter-python/bindings/python/tree_sitter_python/binding.c`

### 2. `__init__.py` — Add query file loading

**Current** (`bindings/python/tree_sitter_al/__init__.py`):
```python
"Al grammar for tree-sitter"
from ._binding import language
__all__ = ["language"]
```

**Should become** something like:
```python
"""AL grammar for tree-sitter"""

from importlib.resources import files as _files
from ._binding import language


def _get_query(name, file):
    query = _files(f"{__package__}.queries") / file
    globals()[name] = query.read_text()
    return globals()[name]


def __getattr__(name):
    if name == "HIGHLIGHTS_QUERY":
        return _get_query("HIGHLIGHTS_QUERY", "highlights.scm")
    if name == "TAGS_QUERY":
        return _get_query("TAGS_QUERY", "tags.scm")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "language",
    "HIGHLIGHTS_QUERY",
    "TAGS_QUERY",
]
```

Reference: `other-languages/tree-sitter-python/bindings/python/tree_sitter_python/__init__.py`

### 3. `__init__.pyi` — Update return type and add query stubs

**Current:**
```python
def language() -> int: ...
```

**Should become:**
```python
from typing import Final

HIGHLIGHTS_QUERY: Final[str]
TAGS_QUERY: Final[str]

def language() -> object: ...
```

### 4. `pyproject.toml` — Update Python and tree-sitter requirements

**Changes needed:**
- `requires-python` from `">=3.9"` to `">=3.12"` (code-graph-rag requires 3.12+)
- `core` dependency from `"tree-sitter~=0.22"` to `"tree-sitter~=0.24"` (for PyCapsule support)
- `setuptools` minimum from `">=42"` to `">=62.4.0"`

### 5. `setup.py` — Add `scanner.c` to extension sources

The `src/scanner.c` file exists but is not listed in the extension sources. The comment says to add it if present.

**Current:**
```python
sources=[
    "bindings/python/tree_sitter_al/binding.c",
    "src/parser.c",
    # NOTE: if your language uses an external scanner, add it here.
],
```

**Should become:**
```python
sources=[
    "bindings/python/tree_sitter_al/binding.c",
    "src/parser.c",
    "src/scanner.c",
],
```

Also update the `cibuildwheel` build target from `cp39-*` to `cp312-*` and the `Py_LIMITED_API` macro from `0x03090000` to `0x030C0000`.

### 6. `setup.py` — Update wheel tag

Update `BdistWheel.get_tag()` to use `cp312` instead of `cp39`.

## Verification

After making these changes, verify by building locally:

```bash
pip install -e .
python -c "import tree_sitter_al; print(tree_sitter_al.language())"
```

The `language()` call should return a `PyCapsule` object (not an integer). Then verify it works with tree-sitter 0.25:

```bash
pip install tree-sitter==0.25.2
python -c "
import tree_sitter
import tree_sitter_al
lang = tree_sitter.Language(tree_sitter_al.language())
parser = tree_sitter.Parser(lang)
tree = parser.parse(b'codeunit 50100 MyCodeunit { }')
print(tree.root_node.sexp())
"
```

## Files to modify

| File | Change |
|------|--------|
| `bindings/python/tree_sitter_al/binding.c` | PyCapsule pattern, module slots |
| `bindings/python/tree_sitter_al/__init__.py` | Query loading via `__getattr__` |
| `bindings/python/tree_sitter_al/__init__.pyi` | Return type + query stubs |
| `pyproject.toml` | Python/tree-sitter version bumps |
| `setup.py` | Add scanner.c, update cp version, update Py_LIMITED_API |
