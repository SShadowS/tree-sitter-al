"""Detector registry. Each entry is a pure function of (tree, source, path)."""

from . import anchor_counts, errors, gaps, reserved

PER_FILE = (
    ("gaps", gaps.detect),
    ("errors", errors.detect),
    ("reserved", reserved.detect),
    ("anchors", anchor_counts.detect),
)
