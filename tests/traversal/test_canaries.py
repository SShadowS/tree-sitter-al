"""Consumer canaries in Python (spec 6.2 item 3). Each reproduces the consumer's own
rule, cited by file:line (.superpowers/sdd/a7/consumers.md), shows the failure on the
naive walk, and answers the same question on F0. The JS canaries (DevOpsWorker,
al-differ, LethAL R214 part 1) are in tests/traversal/js/canaries.test.js."""


def _text(doc, node):
    return doc.source[node.start_byte:node.end_byte].decode("utf-8")


def _split_names(split, keyword, name_field, doc):
    """A split construct that is a `keyword` construct in every arm, read from SplitInfo."""
    names = []
    for g in split.groups:
        for arm in g.arms:
            name = next((f for f in arm.fragments if f.field == name_field), None)
            if name is None or not any(f.type == keyword for f in arm.fragments):
                return None
            names.append(_text(doc, name.node))
    return names or None


# --- code-graph-rag (81398cae) ------------------------------------------------
# codebase_rag/parsers/al/object_extractor.py:21-86 OBJECT_TYPE_TO_LABELS keys (the
# subset this fixture set reaches); procedure_extractor.py:15-22 PROCEDURE_NODE_TYPES.
OBJECT_TYPES = {"codeunit_declaration", "table_declaration", "page_declaration", "enum_declaration"}
PROCEDURE_NODE_TYPES = {"procedure", "trigger_declaration", "event_declaration", "interface_procedure"}


def cgr_before(doc):
    """object_extractor.py:119-121 (root_node.children only), procedure_extractor.py:115-118
    (object_body(node).children only; utils.py:77-78 object_body = field `body` or node)."""
    out = []
    for obj in doc.tree.root_node.children:
        if obj.type not in OBJECT_TYPES:
            continue
        body = obj.child_by_field_name("body") or obj
        out += [(_text(doc, obj.child_by_field_name("object_name")), _text(doc, p.child_by_field_name("name")))
                for p in body.children if p.type in PROCEDURE_NODE_TYPES]
    return out


def cgr_after(doc, policy, T):
    """Every definition in every arm, owned by the innermost object around it, where a
    split declaration names its object from its arms' `object_name` fragments."""
    visits = T.walk(doc, policy)
    owners = []
    for v in visits:
        if v.type in OBJECT_TYPES:
            owners.append((v.start, v.end, _text(doc, v.node.child_by_field_name("object_name"))))
        elif v.cls == "assembler" and v.split:
            names = _split_names(v.split, "codeunit_keyword", "object_name", doc)
            if names:
                owners.append((v.start, v.end, "|".join(sorted(set(names)))))
    out = []
    for v in visits:
        names = None
        if v.type in PROCEDURE_NODE_TYPES:
            names = [_text(doc, v.node.child_by_field_name("name"))]
        elif v.cls == "assembler" and v.split:
            names = sorted(set(_split_names(v.split, "procedure_keyword", "name", doc) or [])) or None
        if names:
            around = [o for o in owners if o[0] <= v.start and v.end <= o[1]]
            # A definition with no object around it has no owner; report it as such.
            owner = max(around, key=lambda o: o[0])[2] if around else None
            out += [(owner, n) for n in names]
    return out


def test_code_graph_rag_definitions_in_every_arm(T, policy, parse):
    doc = parse("containers.al")
    assert cgr_before(doc) == []
    assert cgr_after(doc, policy, T) == [('"Containers Ø"', "A"), ('"Containers Ø"', "B"),
                                         ('"Containers Ø"', "C"), ('"Containers Ø"', "Stmts")]


def test_code_graph_rag_split_procedure_and_split_declaration(T, policy, parse):
    doc = parse("assemblers.al")
    assert cgr_before(doc) == [('"Assemblers"', "First"), ('"Assemblers"', "Tail"),
                               ('"Assemblers"', "CaseEnd")]
    assert cgr_after(doc, policy, T) == [('"Assemblers"', "First"), ('"Assemblers"', "Split"),
                                         ('"Assemblers"', "Tail"), ('"Assemblers"', "CaseEnd")]
    doc = parse("split_declaration.al")
    assert cgr_before(doc) == []
    assert cgr_after(doc, policy, T) == [('"Test Impl"', "TestMethod")]


# --- graphify (6647b56) --------------------------------------------------------
def graphify_before_ranges(doc):
    """graphify/extract.py:3097-3127, verbatim: only preproc_conditional_statement, and
    `#else` negates only the LAST condition. Returns (start_line, end_line, label)."""
    ranges = []

    def collect(node):
        if node.type == "preproc_conditional_statement":
            label = start = None
            for child in node.children:
                if child.type == "preproc_if":
                    cond = child.child_by_field_name("condition")
                    label, start = (_text(doc, cond).strip() if cond else "?"), child.end_point[0] + 1
                elif child.type == "preproc_elif":
                    if label is not None and start is not None:
                        ranges.append((start, child.start_point[0], label))
                    cond = child.child_by_field_name("condition")
                    label, start = (_text(doc, cond).strip() if cond else "?"), child.end_point[0] + 1
                elif child.type == "preproc_else":
                    if label is not None and start is not None:
                        ranges.append((start, child.start_point[0], label))
                    label, start = "!" + (label or "?"), child.end_point[0] + 1
                elif child.type == "preproc_endif":
                    if label is not None and start is not None:
                        ranges.append((start, child.start_point[0], label))
                    label = start = None
        for c in node.children:
            collect(c)

    collect(doc.tree.root_node)
    return ranges


def graphify_before_tag(ranges, node):
    """extract.py:3281-3295, verbatim: a node is tagged by its 1-based source line
    `L{start_point[0] + 1}` (e.g. :2552) and the FIRST range holding it wins, in
    collection order, so an outer range shadows every range nested in it."""
    line = node.start_point[0] + 1
    return next((label for s, e, label in ranges if s <= line <= e), None)


def graphify_after_tag(doc, visit):
    """F0 gives every arm of every kind. Without the symbolic API (spec 3.5) only a
    path of arm-0 arms has an exact condition: the conjunction of their #if
    conditions. An #elif/#else arm's real condition negates every earlier arm, so
    any path through one is reported `unsupported`, never guessed."""
    if not visit.arms:
        return None
    if any(arm_id for _, arm_id in visit.arms):
        return "unsupported"
    conds = []
    for if_offset, _ in visit.arms:
        group = next(g for g in doc.groups if g.if_offset == if_offset)
        conds.append(_text(doc, group.directives[0].node.child_by_field_name("condition")))
    return " and ".join(conds)


def test_graphify_elif_else_condition(T, policy, parse):
    doc = parse("elif_chain.al")
    visits = {(_text(doc, v.node) if v.type == "assignment_statement" else
               _text(doc, v.node.child_by_field_name("name"))): v
              for v in T.walk(doc, policy) if v.type in ("assignment_statement", "procedure")}
    # Assignment statements stand in for graphify's nodes and edges: it tags by source line only.
    ranges = graphify_before_ranges(doc)
    before = {k: graphify_before_tag(ranges, v.node) for k, v in visits.items()}
    assert before["A"] is None             # member-level #if: only preproc_conditional_statement is read
    assert before["X := 3"] == "CLEAN24"   # wrong: the outer range shadows #if CLEAN26
    assert before["X := 4"] == "CLEAN23"   # wrong: an #elif arm is also (not CLEAN24)
    assert before["X := 2"] == "!CLEAN23"  # wrong: the #else arm is (not CLEAN24) and (not CLEAN23)
    assert before["X := 1"] == "CLEAN24"   # the one exact answer: a path of #if arms only
    # DIRECTIVE_EOL drift, recorded: preproc_if/preproc_elif now end at the start of the
    # next row, so `end_point[0] + 1` is the FIRST CONTENT line (22, 27); on 3.0.1 it was
    # the directive line itself. Compared as graphify compares (1-based L lines), no
    # content line is lost either way. #else has no DIRECTIVE_EOL and still starts on
    # its own directive line (28).
    assert ranges == [(22, 25, "CLEAN24"), (27, 27, "CLEAN23"), (28, 29, "!CLEAN23"), (24, 24, "CLEAN26")]
    after = {k: graphify_after_tag(doc, v) for k, v in visits.items()}
    assert after == {"A": "CLEAN24", "B": "unsupported", "C": "unsupported", "Stmts": None,
                     "X := 1": "CLEAN24", "X := 3": "CLEAN24 and CLEAN26",
                     "X := 4": "unsupported", "X := 2": "unsupported"}
