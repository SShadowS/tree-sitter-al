"""Configuration for keyword synchronization tools."""

import os
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
TOOLS_DIR = REPO_ROOT / "tools" / "keyword-sync"
OUTPUT_DIR = TOOLS_DIR / "output"

# VS Code extension path - try common locations
VSCODE_EXTENSION_PATHS = [
    Path(os.environ.get("USERPROFILE", "")) / ".vscode" / "extensions",
    Path(os.environ.get("HOME", "")) / ".vscode" / "extensions",
    Path("/c/Users") / os.environ.get("USERNAME", "") / ".vscode" / "extensions",
]

AL_EXTENSION_PATTERN = "ms-dynamics-smb.al-*"

# Grammar file
GRAMMAR_FILE = REPO_ROOT / "grammar.js"

# Special handling rules per CLAUDE.md
OPERATORS_USE_CHOICE = ["and", "or", "not", "xor", "div", "mod"]
CONTEXTUAL_KEYWORDS_USE_KW_WITH_EQ = ["ispreview", "helplink", "description"]
LITERAL_EXCEPTIONS = ["tabletype", "style", "styleexpr", "visible", "filters"]

# TextMate scope to category mapping
TEXTMATE_SCOPE_MAP = {
    "keyword.control.al": "control_flow",
    "keyword.operators.al": "operators",
    "keyword.other.property.al": "property_keywords",
    "keyword.other.applicationobject.al": "object_types",
    "keyword.other.builtintypes.al": "builtin_types",
    "keyword.other.metadata.al": "metadata",
}

# Priority levels for missing keywords
PRIORITY_LEVELS = {
    "control_flow": 1,  # Highest priority - core language constructs
    "operators": 1,
    "object_types": 2,
    "metadata": 2,
    "property_keywords": 3,
    "builtin_types": 4,  # Lowest - often just type names
    "snippet_enums": 5,  # From snippets, may be property values
}


def find_al_extension() -> Path | None:
    """Find the installed AL extension directory."""
    import glob

    for base_path in VSCODE_EXTENSION_PATHS:
        if not base_path.exists():
            continue

        # Find matching extension directories
        matches = list(base_path.glob(AL_EXTENSION_PATTERN))
        if matches:
            # Return the latest version (highest version number)
            matches.sort(reverse=True)
            return matches[0]

    return None


def get_special_handling(keyword: str) -> str:
    """Determine what special handling a keyword needs."""
    kw_lower = keyword.lower()

    if kw_lower in OPERATORS_USE_CHOICE:
        return "choice"  # Must use choice() not kw()
    elif kw_lower in CONTEXTUAL_KEYWORDS_USE_KW_WITH_EQ:
        return "kw_with_eq"  # Use kw_with_eq() for property=value disambiguation
    elif kw_lower in LITERAL_EXCEPTIONS:
        return "literal"  # Use literal string variations
    else:
        return "kw"  # Standard kw() function
