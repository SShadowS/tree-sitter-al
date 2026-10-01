"""Classified traversal over the all-branches AL tree (roadmap F0, spec 5.1 and 6).

Stdlib only, no relative imports: tests load this file by path, and the
installed package imports it as ``tree_sitter_al.traversal``. Works on any
py-tree-sitter >= 0.25 ``Tree``; nothing here imports ``tree_sitter``.

Every position is a canonical UTF-8 byte offset. Node classes come from the
hand-maintained policy (``traversal/policy.json``), never from a type name.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

SCHEMA = 1
CLASSES = ("ordinary", "branch-container", "assembler", "fragment", "token-alias", "directive", "trivia")
# Only these get a SplitInfo on their visit. An ordinary node that holds directives
# (an ERROR node, say) is walked normally; its arms still reach every visit's `arms`.
SPLIT_CLASSES = ("branch-container", "assembler", "fragment")


class PolicyError(ValueError):
    """The policy file is not one this module can read."""


class WrongDocument(ValueError):
    """An ArmDescriptor from another source revision was handed to bind_arm."""


@dataclass(frozen=True)
class Policy:
    types: dict

    def cls(self, type_: str) -> str:
        entry = self.types.get(type_)
        return entry["class"] if entry else "ordinary"

    def role(self, type_: str):
        entry = self.types.get(type_)
        return entry.get("role") if entry else None

    def host_policy(self, container: str, parent: str, field):
        hosts = (self.types.get(container) or {}).get("hosts") or {}
        return hosts.get(f"{parent}:{field or '<children>'}")


def load_policy(path=None) -> Policy:
    if path is None:
        text = (resources.files("tree_sitter_al") / "traversal_policy.json").read_text(encoding="utf-8")
    else:
        text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    if data.get("schema") != SCHEMA:
        raise PolicyError(f"policy schema {data.get('schema')!r}, expected {SCHEMA}")
    for type_, entry in data["types"].items():
        if entry.get("class") not in CLASSES:
            raise PolicyError(f"{type_}: unknown class {entry.get('class')!r}")
    return Policy(data["types"])


def fnv1a64(data: bytes) -> str:
    h = 0xCBF29CE484222325
    for b in data:
        h = ((h ^ b) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{h:016x}"


@dataclass(frozen=True)
class Directive:
    role: str
    start: int   # the '#' offset
    end: int
    node: object


@dataclass(frozen=True)
class ArmDescriptor:
    group_id: tuple          # (revision, '#if' byte offset)
    arm_id: int
    directive_offsets: tuple  # '#' of the arm's opening directive, then of its closing one if any
    raw_range: tuple         # (start, end) of the arm body, before masking


@dataclass(frozen=True)
class Group:
    if_offset: int
    directives: tuple        # Directive, in source order: if, elif*, else?, endif?
    arms: tuple              # ArmDescriptor


@dataclass(frozen=True)
class Fragment:
    field: object            # str | None
    node: object             # a named node or an anonymous token

    @property
    def type(self):
        return self.node.type


@dataclass(frozen=True)
class ArmFragments:
    descriptor: ArmDescriptor
    fragments: tuple         # Fragment, in source order


@dataclass(frozen=True)
class GroupArms:
    group_id: tuple
    arms: tuple              # ArmFragments, one per arm, every arm present


@dataclass(frozen=True)
class SplitInfo:
    groups: tuple            # GroupArms, in source order
    shared: tuple            # Fragment: the node's own children outside every arm, directives excluded


@dataclass(frozen=True)
class Visit:
    node: object
    cls: str
    type: str
    field: object
    start: int
    end: int
    arms: tuple              # ((if_offset, arm_id), ...), outermost first
    host: object             # host policy, for a branch container in a known slot
    split: object            # SplitInfo | None


class Document:
    """A P1 tree paired with its source bytes and revision; owns the group index."""

    def __init__(self, tree, source: bytes, policy: Policy):
        self.tree = tree
        self.source = source
        self.revision = fnv1a64(source)
        self.groups, self.unpaired, self._by_parent = _pair(tree.root_node, policy, self.revision, len(source))

    def descriptors(self):
        return [a for g in self.groups for a in g.arms]


def _pair(root, policy, revision, eof):
    open_, done, unpaired, by_parent = [], [], [], {}
    stack = [(root, None)]
    while stack:
        node, parent_id = stack.pop()
        role = policy.role(node.type) if node.is_named else None
        if role is None:
            stack.extend((c, node.id) for c in reversed(node.children))
            continue
        d = Directive(role, node.start_byte, node.end_byte, node)
        if role == "if":
            open_.append([d])
        elif not open_:
            unpaired.append(d)
            continue
        else:
            open_[-1].append(d)
        group = open_[-1]
        by_parent.setdefault(parent_id, {})[group[0].start] = None   # dict: ordered set
        if role == "endif":
            done.append(open_.pop())
    done.extend(open_)                    # unclosed at EOF
    groups = {}
    for ds in sorted(done, key=lambda g: g[0].start):
        arms = []
        for idx, d in enumerate(ds):
            if d.role == "endif":
                continue
            closer = ds[idx + 1] if idx + 1 < len(ds) else None
            offsets = (d.start, closer.start) if closer else (d.start,)
            arms.append(ArmDescriptor((revision, ds[0].start), len(arms), offsets,
                                      (d.end, closer.start if closer else eof)))
        groups[ds[0].start] = Group(ds[0].start, tuple(ds), tuple(arms))
    return tuple(groups.values()), tuple(unpaired), {k: [groups[o] for o in v] for k, v in by_parent.items()}


def _kids(node):
    """(child, field name) pairs, the children list read once."""
    return [(c, node.field_name_for_child(i)) for i, c in enumerate(node.children)]


def walk(document: Document, policy: Policy, *, root=None, include_directives=False, include_trivia=False):
    arms = sorted(document.descriptors(), key=lambda a: (a.raw_range[0], -a.raw_range[1]))
    active, k, out = [], 0, []
    start_node = root if root is not None else document.tree.root_node
    parent0, field0 = start_node.parent, None
    if parent0 is not None:              # a subtree root keeps its real parent and field
        field0 = next((parent0.field_name_for_child(i) for i, c in enumerate(parent0.children) if c == start_node), None)
    stack = [(start_node, field0, parent0)]
    while stack:
        node, field, parent = stack.pop()
        if not node.is_named:
            continue
        cls = policy.cls(node.type)
        if (cls == "directive" and not include_directives) or (cls == "trivia" and not include_trivia):
            continue
        start, end = node.start_byte, node.end_byte
        while k < len(arms) and arms[k].raw_range[0] <= start:
            active.append(arms[k])
            k += 1
        active = [a for a in active if a.raw_range[1] > start]
        path = tuple((a.group_id[1], a.arm_id) for a in active if a.raw_range[1] >= end)
        host = policy.host_policy(node.type, parent.type, field) if cls == "branch-container" and parent else None
        split = None                     # SplitInfo arrives with split_info (Task 3)
        out.append(Visit(node, cls, node.type, field, start, end, path, host, split))
        stack.extend((child, f, node) for child, f in reversed(_kids(node)))
    return out
