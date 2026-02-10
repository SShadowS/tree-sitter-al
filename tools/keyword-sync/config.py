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

# =============================================================================
# False Positives - items flagged as "missing" but handled by generic mechanisms
# =============================================================================
# Each entry maps lowercase item name -> reason string explaining why it's a
# false positive. Verified against BC.History production files (15,000+ files).

FALSE_POSITIVE_KEYWORDS = {
    # External scanner tokens
    "to": "Handled by external scanner token `for_to_keyword` (grammar.js externals)",
    "downto": "Handled by external scanner token `for_downto_keyword` (grammar.js externals)",
    # Attributes handled by generic attribute_item rule
    "runonclient": "Attribute handled by generic `attribute_item` rule: [RunOnClient]",
    "securityfiltering": "Attribute handled by generic `attribute_item` rule: [SecurityFiltering(...)]",
    "withevents": "Attribute handled by generic `attribute_item` rule: [WithEvents]",
    "suppressdispose": "Attribute handled by generic `attribute_item` rule: [SuppressDispose] (not used in production)",
    # Legacy keywords
    "program": "Legacy C/AL keyword not used in modern AL (Business Central)",
}

FALSE_POSITIVE_PROPERTIES = {
    # Already explicitly defined in grammar.js
    "extensible": "Already defined in grammar.js as `extensible_property`",
    "profiledescription": "Already defined in grammar.js as `profile_description_property2`",
    # ControlAddIn properties handled by generic controladdin_property rule
    "horizontalshrink": "Handled by generic `controladdin_property` rule (any identifier = boolean)",
    "horizontalstretch": "Handled by generic `controladdin_property` rule (any identifier = boolean)",
    "verticalshrink": "Handled by generic `controladdin_property` rule (any identifier = boolean)",
    "verticalstretch": "Handled by generic `controladdin_property` rule (any identifier = boolean)",
    "maximumheight": "Handled by generic `controladdin_property` rule (any identifier = integer)",
    "maximumwidth": "Handled by generic `controladdin_property` rule (any identifier = integer)",
    "minimumheight": "Handled by generic `controladdin_property` rule (any identifier = integer)",
    "minimumwidth": "Handled by generic `controladdin_property` rule (any identifier = integer)",
    "requestedheight": "Handled by generic `controladdin_property` rule (any identifier = integer)",
    "requestedwidth": "Handled by generic `controladdin_property` rule (any identifier = integer)",
    "recreatescript": "Handled by generic `controladdin_property` rule (any identifier = string)",
    "refreshscript": "Handled by generic `controladdin_property` rule (any identifier = string)",
    "startupscript": "Handled by generic `controladdin_property` rule (any identifier = string)",
    "stylesheets": "Handled by generic `controladdin_property` rule (any identifier = string)",
    # Not used as a property in production
    "definitionfile": "Not used as a property in any production file (only as variable name)",
}

FALSE_POSITIVE_TRIGGERS = {
    "onbeforeopen": "Handled by generic `trigger_declaration` rule (accepts any identifier as trigger name)",
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
