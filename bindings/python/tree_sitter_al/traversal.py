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
    raw_range: tuple         # (start, end) of the arm body, before masking. It starts after
                             # the line terminator of the arm's directive line (spec 3.3: a
                             # trailing `//` belongs to the directive), or at EOF


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
        self.groups, self.unpaired, self._by_parent = _pair(tree.root_node, policy, self.revision, source)

    def descriptors(self):
        return [a for g in self.groups for a in g.arms]


def _line_end(source: bytes, end: int) -> int:
    """The first byte after the newline ending the line a directive ends on (or EOF).

    `#if`/`#elif` nodes end after their newline and `#else` before it, so this is
    what makes every arm start in the same place: a trailing comment on any
    directive line is outside the arm.
    """
    nl = source.find(b"\n", max(end - 1, 0))
    return len(source) if nl < 0 else nl + 1


def _pair(root, policy, revision, source):
    eof = len(source)
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
            end = closer.start if closer else eof
            # min: a MISSING #endif (error recovery) can sit before the newline
            arms.append(ArmDescriptor((revision, ds[0].start), len(arms), offsets,
                                      (min(_line_end(source, d.end), end), end)))
        groups[ds[0].start] = Group(ds[0].start, tuple(ds), tuple(arms))
    return tuple(groups.values()), tuple(unpaired), {k: [groups[o] for o in v] for k, v in by_parent.items()}


def _kids(node):
    """(child, field name) pairs, the children list read once."""
    return [(c, node.field_name_for_child(i)) for i, c in enumerate(node.children)]


def groups_of(node, document: Document):
    return list(document._by_parent.get(node.id, ()))


def bind_arm(descriptor: ArmDescriptor, document: Document, policy: Policy) -> ArmFragments:
    if descriptor.group_id[0] != document.revision:
        raise WrongDocument(f"descriptor revision {descriptor.group_id[0]} != document {document.revision}")
    lo, hi = descriptor.raw_range
    out = []
    # Start at the smallest node holding the whole arm, one level up if the arm IS
    # that node, so its field name is known: walking from the root is O(siblings)
    # per arm, quadratic in a body of thousands of groups.
    top = document.tree.root_node.descendant_for_byte_range(lo, hi) or document.tree.root_node
    while top.parent is not None and lo <= top.start_byte and top.end_byte <= hi:
        top = top.parent
    stack = [(top, None)]
    while stack:
        node, field = stack.pop()
        if node.end_byte <= lo or node.start_byte >= hi:
            continue
        if lo <= node.start_byte and node.end_byte <= hi:
            if not (node.is_named and policy.cls(node.type) == "directive"):
                out.append(Fragment(field, node))
            continue
        stack.extend(reversed(_kids(node)))
    return ArmFragments(descriptor, tuple(out))


def arm_pieces(arm_fragments: ArmFragments, document: Document, policy: Policy):
    """An arm's fragments with every `fragment`-class piece replaced, in place and
    recursively, by its own children (field names kept, anonymous tokens kept).

    A fragment wholly inside one arm gets no SplitInfo of its own, so this is how a
    consumer reaches the statements it holds. Source order, UTF-8 byte offsets.
    """
    if arm_fragments.descriptor.group_id[0] != document.revision:
        raise WrongDocument(f"descriptor revision {arm_fragments.descriptor.group_id[0]} != document {document.revision}")
    out = []

    def add(pieces):
        for f in pieces:
            if f.node.is_named and policy.cls(f.node.type) == "fragment":
                add(Fragment(field, child) for child, field in _kids(f.node))
            else:
                out.append(f)

    add(arm_fragments.fragments)
    return out


def arm_pieces_to_json(document: Document, visits, policy: Policy) -> str:
    """The shared arm-pieces file: per split visit, per group, per arm, one line."""
    lines = []
    for v in visits:
        if v.split is None:
            continue
        for g in v.split.groups:
            for a in g.arms:
                lines.append(json.dumps({"type": v.type, "start": v.start, "if": g.group_id[1],
                                         "arm": a.descriptor.arm_id,
                                         "pieces": [_frag_json(f) for f in arm_pieces(a, document, policy)]},
                                        ensure_ascii=False))
    return '{"revision": "%s", "arms": [\n%s\n]}\n' % (document.revision, ",\n".join(lines))


def split_info(node, document: Document, policy: Policy):
    groups = groups_of(node, document)
    if not groups:
        return None
    ranges = [a.raw_range for g in groups for a in g.arms]
    # an arm's directive line, '#' to the arm start: a trailing comment there is the directive's
    ranges += [(a.directive_offsets[0], a.raw_range[0]) for g in groups for a in g.arms]
    shared = []
    for child, field in _kids(node):
        if child.is_named and policy.cls(child.type) == "directive":
            continue
        if any(lo <= child.start_byte and child.end_byte <= hi for lo, hi in ranges):
            continue
        shared.append(Fragment(field, child))
    return SplitInfo(tuple(GroupArms((document.revision, g.if_offset),
                                     tuple(bind_arm(a, document, policy) for a in g.arms)) for g in groups),
                     tuple(shared))


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
        split = split_info(node, document, policy) if cls in SPLIT_CLASSES else None
        out.append(Visit(node, cls, node.type, field, start, end, path, host, split))
        stack.extend((child, f, node) for child, f in reversed(_kids(node)))
    return out


def _frag_json(f: Fragment):
    return [f.field, f.node.type, f.node.is_named, f.node.start_byte, f.node.end_byte]


def split_to_json(s: SplitInfo):
    return {"groups": [{"if": g.group_id[1],
                        "arms": [{"arm": a.descriptor.arm_id, "range": list(a.descriptor.raw_range),
                                  "fragments": [_frag_json(f) for f in a.fragments]} for a in g.arms]}
                       for g in s.groups],
            "shared": [_frag_json(f) for f in s.shared]}


def visits_to_json(visits):
    """The parity form: what every runtime must produce for the same fixture."""
    return [{"class": v.cls, "type": v.type, "field": v.field, "start": v.start, "end": v.end,
             "arms": [list(a) for a in v.arms], "host": v.host,
             "split": split_to_json(v.split) if v.split else None} for v in visits]


def dump_expected(document: Document, visits) -> str:
    """A fixture's expected-visits file: one visit per line, so a review reads a diff."""
    lines = [json.dumps(v, ensure_ascii=False) for v in visits_to_json(visits)]
    return '{"revision": "%s", "visits": [\n%s\n]}\n' % (document.revision, ",\n".join(lines))
