//! Classified traversal over the all-branches AL tree (roadmap F0, spec 5.1 and 6).
//!
//! Behind the `traversal` cargo feature, off by default: it is the only part of
//! this crate that needs the `tree-sitter` runtime and `serde_json`.
//!
//! Every position is a canonical UTF-8 byte offset. Node classes come from the
//! hand-maintained policy (`traversal/policy.json`, bundled below), never from a
//! node-type name.

use std::collections::{HashMap, HashSet};
use std::fmt;

use serde_json::{json, Map, Value};
use tree_sitter::{Node, Tree};

/// The policy file shipped in this crate, identical to the one in every other package.
pub const POLICY_JSON: &str = include_str!("../../traversal/policy.json");
pub const SCHEMA: u64 = 1;
pub const CLASSES: [&str; 7] = [
    "ordinary", "branch-container", "assembler", "fragment", "token-alias", "directive", "trivia",
];
/// Only these get a `SplitInfo` on their visit. An ordinary node that holds
/// directives (an ERROR node, say) is walked normally.
pub const SPLIT_CLASSES: [&str; 3] = ["branch-container", "assembler", "fragment"];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PolicyError(pub String);

impl fmt::Display for PolicyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "traversal policy: {}", self.0)
    }
}

impl std::error::Error for PolicyError {}

/// An `ArmDescriptor` from another source revision was handed to `bind_arm`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WrongDocument(pub String);

impl fmt::Display for WrongDocument {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "wrong document: {}", self.0)
    }
}

impl std::error::Error for WrongDocument {}

#[derive(Debug, Clone)]
pub struct Policy {
    types: Map<String, Value>,
}

impl Policy {
    pub fn from_json(text: &str) -> Result<Policy, PolicyError> {
        let data: Value = serde_json::from_str(text).map_err(|e| PolicyError(e.to_string()))?;
        if data.get("schema").and_then(Value::as_u64) != Some(SCHEMA) {
            return Err(PolicyError(format!("schema {:?}, expected {SCHEMA}", data.get("schema"))));
        }
        let types = data
            .get("types")
            .and_then(Value::as_object)
            .ok_or_else(|| PolicyError("no `types` object".into()))?
            .clone();
        for (ty, entry) in &types {
            let class = entry.get("class").and_then(Value::as_str).unwrap_or("");
            if !CLASSES.contains(&class) {
                return Err(PolicyError(format!("{ty}: unknown class {class:?}")));
            }
        }
        Ok(Policy { types })
    }

    pub fn bundled() -> Policy {
        Policy::from_json(POLICY_JSON).expect("the bundled policy is valid")
    }

    pub fn class(&self, ty: &str) -> &str {
        self.types
            .get(ty)
            .and_then(|e| e.get("class"))
            .and_then(Value::as_str)
            .unwrap_or("ordinary")
    }

    pub fn role(&self, ty: &str) -> Option<&str> {
        self.types.get(ty).and_then(|e| e.get("role")).and_then(Value::as_str)
    }

    pub fn host_policy(&self, container: &str, parent: &str, field: Option<&str>) -> Option<&str> {
        let key = format!("{parent}:{}", field.unwrap_or("<children>"));
        self.types
            .get(container)
            .and_then(|e| e.get("hosts"))
            .and_then(|h| h.get(&key))
            .and_then(Value::as_str)
    }
}

pub fn fnv1a64(data: &[u8]) -> String {
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for b in data {
        h = (h ^ u64::from(*b)).wrapping_mul(0x0100_0000_01b3);
    }
    format!("{h:016x}")
}

#[derive(Debug, Clone)]
pub struct Directive<'t> {
    pub role: String,
    pub start: usize,
    pub end: usize,
    pub node: Node<'t>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ArmDescriptor {
    /// (revision, '#if' byte offset)
    pub group_id: (String, usize),
    pub arm_id: usize,
    /// '#' of the arm's opening directive, then of its closing one if any.
    pub directive_offsets: Vec<usize>,
    /// The arm body, before any masking.
    pub raw_range: (usize, usize),
}

#[derive(Debug, Clone)]
pub struct Group<'t> {
    pub if_offset: usize,
    pub directives: Vec<Directive<'t>>,
    pub arms: Vec<ArmDescriptor>,
}

#[derive(Debug, Clone)]
pub struct Fragment<'t> {
    pub field: Option<&'static str>,
    pub node: Node<'t>,
}

#[derive(Debug, Clone)]
pub struct ArmFragments<'t> {
    pub descriptor: ArmDescriptor,
    pub fragments: Vec<Fragment<'t>>,
}

#[derive(Debug, Clone)]
pub struct GroupArms<'t> {
    pub group_id: (String, usize),
    pub arms: Vec<ArmFragments<'t>>,
}

#[derive(Debug, Clone)]
pub struct SplitInfo<'t> {
    pub groups: Vec<GroupArms<'t>>,
    /// The node's own children outside every arm, directives excluded.
    pub shared: Vec<Fragment<'t>>,
}

#[derive(Debug, Clone)]
pub struct Visit<'t> {
    pub node: Node<'t>,
    pub class: String,
    pub kind: &'static str,
    pub field: Option<&'static str>,
    pub start: usize,
    pub end: usize,
    /// (if_offset, arm_id), outermost first.
    pub arms: Vec<(usize, usize)>,
    pub host: Option<String>,
    pub split: Option<SplitInfo<'t>>,
}

#[derive(Debug, Clone, Copy, Default)]
pub struct WalkOptions {
    pub include_directives: bool,
    pub include_trivia: bool,
}

/// A P1 tree paired with its source bytes and revision; owns the group index.
pub struct Document<'t> {
    pub tree: &'t Tree,
    pub source: &'t [u8],
    pub revision: String,
    pub groups: Vec<Group<'t>>,
    pub unpaired: Vec<Directive<'t>>,
    by_parent: HashMap<usize, Vec<usize>>, // parent node id -> indexes into groups
}

/// A node's children with their field names, through a cursor: the same calls
/// on tree-sitter 0.25 and 0.26.
fn kids<'t>(node: Node<'t>) -> Vec<(Option<&'static str>, Node<'t>)> {
    let mut out = Vec::new();
    let mut c = node.walk();
    if c.goto_first_child() {
        loop {
            out.push((c.field_name(), c.node()));
            if !c.goto_next_sibling() {
                break;
            }
        }
    }
    out
}

impl<'t> Document<'t> {
    pub fn new(tree: &'t Tree, source: &'t [u8], policy: &Policy) -> Document<'t> {
        let revision = fnv1a64(source);
        let mut open: Vec<Vec<Directive<'t>>> = Vec::new();
        let mut done: Vec<Vec<Directive<'t>>> = Vec::new();
        let mut unpaired = Vec::new();
        // parent id -> '#if' offsets in first-seen order, deduplicated through `seen`.
        // The parent id rides on the stack: a `.parent()` call per directive and a
        // list scan were both quadratic.
        let mut parent_ifs: HashMap<usize, Vec<usize>> = HashMap::new();
        let mut seen: HashSet<(usize, usize)> = HashSet::new();
        let mut stack = vec![(tree.root_node(), usize::MAX)]; // the root has no parent
        while let Some((node, pid)) = stack.pop() {
            let role = if node.is_named() { policy.role(node.kind()) } else { None };
            let Some(role) = role else {
                for (_, k) in kids(node).into_iter().rev() {
                    stack.push((k, node.id()));
                }
                continue;
            };
            let d = Directive { role: role.to_string(), start: node.start_byte(), end: node.end_byte(), node };
            if role == "if" {
                open.push(vec![d]);
            } else if open.is_empty() {
                unpaired.push(d);
                continue;
            } else {
                open.last_mut().unwrap().push(d);
            }
            let if_offset = open.last().unwrap()[0].start;
            if seen.insert((pid, if_offset)) {
                parent_ifs.entry(pid).or_default().push(if_offset);
            }
            if role == "endif" {
                done.push(open.pop().unwrap());
            }
        }
        done.extend(open);
        done.sort_by_key(|ds| ds[0].start);
        let eof = source.len();
        let mut groups = Vec::new();
        for ds in done {
            let if_offset = ds[0].start;
            let mut arms = Vec::new();
            for (idx, d) in ds.iter().enumerate() {
                if d.role == "endif" {
                    continue;
                }
                let closer = ds.get(idx + 1);
                let end = closer.map_or(eof, |c| c.start);
                arms.push(ArmDescriptor {
                    group_id: (revision.clone(), if_offset),
                    arm_id: arms.len(),
                    directive_offsets: match closer {
                        Some(c) => vec![d.start, c.start],
                        None => vec![d.start],
                    },
                    // min: a MISSING #endif (error recovery) can sit before the newline
                    raw_range: (line_end(source, d.end).min(end), end),
                });
            }
            groups.push(Group { if_offset, directives: ds, arms });
        }
        let index: HashMap<usize, usize> = groups.iter().enumerate().map(|(i, g)| (g.if_offset, i)).collect();
        let by_parent = parent_ifs
            .into_iter()
            .map(|(pid, offs)| (pid, offs.iter().map(|o| index[o]).collect()))
            .collect();
        Document { tree, source, revision, groups, unpaired, by_parent }
    }

    pub fn descriptors(&self) -> Vec<&ArmDescriptor> {
        self.groups.iter().flat_map(|g| g.arms.iter()).collect()
    }
}

/// The first byte after the newline ending the line a directive ends on, or EOF.
/// `#if`/`#elif` nodes end after their newline and `#else` before it; every arm
/// starts here, so a trailing comment on any directive line is outside the arm.
fn line_end(source: &[u8], end: usize) -> usize {
    let from = end.saturating_sub(1).min(source.len());
    source[from..].iter().position(|&b| b == b'\n').map_or(source.len(), |i| from + i + 1)
}

pub fn groups_of<'d, 't>(node: Node<'t>, doc: &'d Document<'t>) -> Vec<&'d Group<'t>> {
    doc.by_parent
        .get(&node.id())
        .map(|ix| ix.iter().map(|&i| &doc.groups[i]).collect())
        .unwrap_or_default()
}

pub fn bind_arm<'t>(d: &ArmDescriptor, doc: &Document<'t>, policy: &Policy) -> Result<ArmFragments<'t>, WrongDocument> {
    if d.group_id.0 != doc.revision {
        return Err(WrongDocument(format!("descriptor revision {} != document {}", d.group_id.0, doc.revision)));
    }
    let (lo, hi) = d.raw_range;
    let mut out = Vec::new();
    // Start at the smallest node holding the whole arm, one level up if the arm IS
    // that node, so its field name is known (walking from the root is quadratic).
    let root = doc.tree.root_node();
    let mut top = root.descendant_for_byte_range(lo, hi).unwrap_or(root);
    while let Some(p) = top.parent() {
        if !(lo <= top.start_byte() && top.end_byte() <= hi) {
            break;
        }
        top = p;
    }
    let mut stack = vec![(top, None)];
    while let Some((node, field)) = stack.pop() {
        if node.end_byte() <= lo || node.start_byte() >= hi {
            continue;
        }
        if lo <= node.start_byte() && node.end_byte() <= hi {
            if !(node.is_named() && policy.class(node.kind()) == "directive") {
                out.push(Fragment { field, node });
            }
            continue;
        }
        for (f, k) in kids(node).into_iter().rev() {
            stack.push((k, f));
        }
    }
    Ok(ArmFragments { descriptor: d.clone(), fragments: out })
}

/// An arm's fragments with every `fragment`-class piece replaced, in place and
/// recursively, by its own children (field names kept, anonymous tokens kept). A
/// fragment wholly inside one arm gets no `SplitInfo` of its own; this reaches inside it.
pub fn arm_pieces<'t>(arm: &ArmFragments<'t>, doc: &Document<'t>, policy: &Policy) -> Result<Vec<Fragment<'t>>, WrongDocument> {
    let d = &arm.descriptor;
    if d.group_id.0 != doc.revision {
        return Err(WrongDocument(format!("descriptor revision {} != document {}", d.group_id.0, doc.revision)));
    }
    fn add<'t>(pieces: Vec<Fragment<'t>>, policy: &Policy, out: &mut Vec<Fragment<'t>>) {
        for f in pieces {
            let class = if f.node.is_named() { policy.class(f.node.kind()) } else { "" };
            if class == "directive" {
                continue; // never a piece, even as an expanded fragment's own child
            }
            if class == "fragment" {
                add(kids(f.node).into_iter().map(|(field, node)| Fragment { field, node }).collect(), policy, out);
            } else {
                out.push(f);
            }
        }
    }
    let mut out = Vec::new();
    add(arm.fragments.clone(), policy, &mut out);
    Ok(out)
}

pub fn split_info<'t>(node: Node<'t>, doc: &Document<'t>, policy: &Policy) -> Option<SplitInfo<'t>> {
    let groups = groups_of(node, doc);
    if groups.is_empty() {
        return None;
    }
    // Each arm, and its directive line ('#' to the arm start): a trailing comment there is the directive's.
    let ranges: Vec<(usize, usize)> = groups
        .iter()
        .flat_map(|g| g.arms.iter().flat_map(|a| [a.raw_range, (a.directive_offsets[0], a.raw_range.0)]))
        .collect();
    let shared = kids(node)
        .into_iter()
        .filter(|(_, c)| !(c.is_named() && policy.class(c.kind()) == "directive"))
        .filter(|(_, c)| !ranges.iter().any(|&(lo, hi)| lo <= c.start_byte() && c.end_byte() <= hi))
        .map(|(field, node)| Fragment { field, node })
        .collect();
    let groups = groups
        .iter()
        .map(|g| GroupArms {
            group_id: (doc.revision.clone(), g.if_offset),
            arms: g.arms.iter().map(|a| bind_arm(a, doc, policy).expect("same document")).collect(),
        })
        .collect();
    Some(SplitInfo { groups, shared })
}

pub fn walk<'t>(doc: &Document<'t>, policy: &Policy, root: Option<Node<'t>>, opts: WalkOptions) -> Vec<Visit<'t>> {
    let mut arms = doc.descriptors();
    arms.sort_by_key(|a| (a.raw_range.0, std::cmp::Reverse(a.raw_range.1)));
    let mut active: Vec<&ArmDescriptor> = Vec::new();
    let mut k = 0;
    let mut out = Vec::new();
    // A subtree root keeps its real parent and field, so a branch container walked
    // directly reports the same host and field as it does in a full walk.
    let start0 = root.unwrap_or_else(|| doc.tree.root_node());
    let parent0 = start0.parent();
    let field0 = parent0.and_then(|p| kids(p).into_iter().find(|(_, c)| c.id() == start0.id()).and_then(|(f, _)| f));
    let mut stack = vec![(start0, field0, parent0)];
    while let Some((node, field, parent)) = stack.pop() {
        if !node.is_named() {
            continue;
        }
        let class = policy.class(node.kind());
        if (class == "directive" && !opts.include_directives) || (class == "trivia" && !opts.include_trivia) {
            continue;
        }
        let (start, end) = (node.start_byte(), node.end_byte());
        while k < arms.len() && arms[k].raw_range.0 <= start {
            active.push(arms[k]);
            k += 1;
        }
        active.retain(|a| a.raw_range.1 > start);
        let path = active.iter().filter(|a| a.raw_range.1 >= end).map(|a| (a.group_id.1, a.arm_id)).collect();
        let host = match (class, parent) {
            ("branch-container", Some(p)) => policy.host_policy(node.kind(), p.kind(), field).map(str::to_string),
            _ => None,
        };
        out.push(Visit {
            node,
            class: class.to_string(),
            kind: node.kind(),
            field,
            start,
            end,
            arms: path,
            host,
            split: if SPLIT_CLASSES.contains(&class) { split_info(node, doc, policy) } else { None },
        });
        for (f, c) in kids(node).into_iter().rev() {
            stack.push((c, f, Some(node)));
        }
    }
    out
}

fn frag_json(f: &Fragment) -> Value {
    json!([f.field, f.node.kind(), f.node.is_named(), f.node.start_byte(), f.node.end_byte()])
}

fn split_json(s: &SplitInfo) -> Value {
    json!({
        "groups": s.groups.iter().map(|g| json!({
            "if": g.group_id.1,
            "arms": g.arms.iter().map(|a| json!({
                "arm": a.descriptor.arm_id,
                "range": [a.descriptor.raw_range.0, a.descriptor.raw_range.1],
                "fragments": a.fragments.iter().map(frag_json).collect::<Vec<_>>(),
            })).collect::<Vec<_>>(),
        })).collect::<Vec<_>>(),
        "shared": s.shared.iter().map(frag_json).collect::<Vec<_>>(),
    })
}

/// The parity form: what every runtime must produce for the same fixture.
pub fn visits_to_json(visits: &[Visit]) -> Value {
    Value::Array(
        visits
            .iter()
            .map(|v| {
                json!({
                    "class": v.class, "type": v.kind, "field": v.field, "start": v.start, "end": v.end,
                    "arms": v.arms.iter().map(|&(i, a)| json!([i, a])).collect::<Vec<_>>(),
                    "host": v.host,
                    "split": v.split.as_ref().map(split_json),
                })
            })
            .collect(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::{Path, PathBuf};

    fn fixtures() -> Vec<PathBuf> {
        let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/traversal/fixtures");
        let mut out: Vec<PathBuf> = std::fs::read_dir(&dir)
            .expect("tests/traversal/fixtures")
            .map(|e| e.expect("dir entry").path())
            .filter(|p| p.extension().is_some_and(|x| x == "al"))
            .collect();
        out.sort();
        out
    }

    fn parser() -> tree_sitter::Parser {
        let mut parser = tree_sitter::Parser::new();
        parser.set_language(&crate::LANGUAGE.into()).expect("load AL");
        parser
    }

    #[test]
    fn every_fixture_matches_its_expected_visits() {
        let policy = Policy::bundled();
        let mut parser = parser();
        let paths = fixtures();
        assert_eq!(paths.len(), 14);
        for path in paths {
            let source = std::fs::read(&path).unwrap();
            let tree = parser.parse(&source, None).unwrap();
            let doc = Document::new(&tree, &source, &policy);
            let got = json!({
                "revision": doc.revision,
                "visits": visits_to_json(&walk(&doc, &policy, None, WalkOptions::default())),
            });
            let want: Value =
                serde_json::from_str(&std::fs::read_to_string(path.with_extension("visits.json")).unwrap()).unwrap();
            assert_eq!(got, want, "{}", path.display());
        }
    }

    #[test]
    fn assemblers_matches_its_expected_arm_pieces() {
        let policy = Policy::bundled();
        let (source, tree) = parse_fixture(&mut parser(), "assemblers.al");
        let doc = Document::new(&tree, &source, &policy);
        let mut arms = Vec::new();
        for v in walk(&doc, &policy, None, WalkOptions::default()) {
            let Some(split) = &v.split else { continue };
            for g in &split.groups {
                for a in &g.arms {
                    let pieces = arm_pieces(a, &doc, &policy).unwrap();
                    arms.push(json!({
                        "type": v.kind, "start": v.start, "if": g.group_id.1, "arm": a.descriptor.arm_id,
                        "pieces": pieces.iter().map(frag_json).collect::<Vec<_>>(),
                    }));
                }
            }
        }
        let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/traversal/fixtures/assemblers.arm_pieces.json");
        let want: Value = serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
        assert_eq!(json!({"revision": doc.revision, "arms": arms}), want);
    }

    #[test]
    fn every_group_of_a_value_sequence_carries_its_own_split() {
        // B11 witness (spec 5.5): the sequence owns no directives; each group does.
        let policy = Policy::bundled();
        let (source, tree) = parse_fixture(&mut parser(), "value_run.al");
        let doc = Document::new(&tree, &source, &policy);
        let visits = walk(&doc, &policy, None, WalkOptions::default());
        let seq: Vec<&Visit> = visits.iter().filter(|v| v.kind == "preproc_conditional_property_value_sequence").collect();
        assert_eq!(seq.len(), 1);
        assert!(seq[0].split.is_none());
        let arms: Vec<Vec<Vec<(Option<&str>, &str, &[u8])>>> = visits
            .iter()
            .filter(|v| v.kind == "preproc_conditional_property_value")
            .map(|v| {
                v.split.as_ref().expect("a group carries its split").groups[0]
                    .arms
                    .iter()
                    .map(|a| a.fragments.iter().map(|f| (f.field, f.node.kind(), &source[f.node.byte_range()])).collect())
                    .collect()
            })
            .collect();
        let arm = |lit: &'static [u8]| vec![vec![(Some("value"), "string_literal", lit), (None, ";", b";".as_slice())]];
        assert_eq!(arms, vec![arm(b"'a'"), arm(b"'b'")]);
    }

    #[test]
    fn fnv1a64_reference_vectors() {
        assert_eq!(fnv1a64(b""), "cbf29ce484222325");
        assert_eq!(fnv1a64(b"a"), "af63dc4c8601ec8c");
    }

    #[test]
    fn policy_rejects_an_unknown_schema_or_class() {
        assert!(Policy::from_json(r#"{"schema": 2, "types": {}}"#).is_err());
        assert!(Policy::from_json(r#"{"schema": 1, "types": {"x": {"class": "special"}}}"#).is_err());
        let p = Policy::bundled();
        assert_eq!(p.class("preproc_conditional_expression_tail"), "assembler");
        assert_eq!(p.class("identifier"), "ordinary");
    }

    fn parse_fixture(parser: &mut tree_sitter::Parser, name: &str) -> (Vec<u8>, Tree) {
        let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/traversal/fixtures").join(name);
        let source = std::fs::read(path).unwrap();
        let tree = parser.parse(&source, None).unwrap();
        (source, tree)
    }

    #[test]
    fn a_subtree_walk_root_visit_equals_the_full_walk_visit() {
        let policy = Policy::bundled();
        let (source, tree) = parse_fixture(&mut parser(), "containers.al");
        let doc = Document::new(&tree, &source, &policy);
        let full = walk(&doc, &policy, None, WalkOptions::default());
        let containers: Vec<&Visit> = full.iter().filter(|v| v.class == "branch-container").collect();
        assert!(!containers.is_empty() && containers.iter().all(|v| v.host.is_some()));
        for v in containers {
            let sub = walk(&doc, &policy, Some(v.node), WalkOptions::default());
            assert_eq!(sub[0].node, v.node);
            assert_eq!(visits_to_json(&sub[..1]), visits_to_json(std::slice::from_ref(v)));
        }
    }

    #[test]
    fn crlf_and_a_leading_bom_keep_byte_offsets() {
        let policy = Policy::bundled();
        let (source, tree) = parse_fixture(&mut parser(), "crlf_bom.al");
        assert!(source.starts_with(b"\xef\xbb\xbf") && source.windows(2).any(|w| w == b"\r\n"));
        let doc = Document::new(&tree, &source, &policy);
        assert_eq!(doc.groups.len(), 1);
        let g = &doc.groups[0];
        assert_eq!(g.if_offset, source.windows(3).position(|w| w == b"#if").unwrap());
        let ranges: Vec<(usize, usize)> = g.arms.iter().map(|a| a.raw_range).collect();
        // #else is 86-91; its arm starts after the CRLF at 91-93, like the #if arm.
        assert_eq!(ranges, [(46, 86), (93, 133)]);
        assert_eq!(&source[g.arms[0].raw_range.0 - 2..g.arms[0].raw_range.0], b"\r\n");
    }

    #[test]
    fn bind_arm_rejects_a_descriptor_from_another_document() {
        let policy = Policy::bundled();
        let mut parser = parser();
        let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/traversal/fixtures");
        let (a_src, b_src) = (std::fs::read(dir.join("containers.al")).unwrap(),
                              std::fs::read(dir.join("elif_chain.al")).unwrap());
        let (a_tree, b_tree) = (parser.parse(&a_src, None).unwrap(), parser.parse(&b_src, None).unwrap());
        let a = Document::new(&a_tree, &a_src, &policy);
        let b = Document::new(&b_tree, &b_src, &policy);
        assert!(bind_arm(a.descriptors()[0], &b, &policy).is_err());
    }

    #[test]
    fn walk_also_visits_an_assemblers_arm_pieces() {
        // Consumers that read both SplitInfo and walk must dedupe by node id.
        let policy = Policy::bundled();
        let (source, tree) = parse_fixture(&mut parser(), "assemblers.al");
        let doc = Document::new(&tree, &source, &policy);
        let visits = walk(&doc, &policy, None, WalkOptions::default());
        let by_id: HashMap<usize, &Visit> = visits.iter().map(|v| (v.node.id(), v)).collect();
        let v = visits.iter().find(|v| v.kind == "preproc_split_procedure").unwrap();
        for g in &v.split.as_ref().unwrap().groups {
            for a in &g.arms {
                let named: Vec<_> = a.fragments.iter().filter(|f| f.node.is_named()).collect();
                assert!(!named.is_empty());
                for f in named {
                    let seen = by_id.get(&f.node.id()).expect("an arm piece is also a walk visit");
                    assert_eq!(seen.arms.last(), Some(&(g.group_id.1, a.descriptor.arm_id)));
                }
            }
        }
    }

    #[test]
    fn arm_pieces_never_keeps_a_directive_of_an_expanded_fragment() {
        // No grammar fixture can trigger it (see the Python test), so the nested statement
        // conditional of containers.al (#if at 489, in arm 0 of 441) is made a fragment.
        let mut data: Value = serde_json::from_str(POLICY_JSON).unwrap();
        data["types"]["preproc_conditional_statement"]["class"] = json!("fragment");
        let over = Policy::from_json(&data.to_string()).unwrap();
        let (source, tree) = parse_fixture(&mut parser(), "containers.al");
        let doc = Document::new(&tree, &source, &over);
        let outer = doc.groups.iter().find(|g| g.if_offset == 441).unwrap();
        let arm = bind_arm(&outer.arms[0], &doc, &over).unwrap();
        assert!(arm.fragments.iter().any(|f| f.node.start_byte() == 489));
        let pieces = arm_pieces(&arm, &doc, &over).unwrap();
        assert!(!pieces.iter().any(|f| f.node.is_named() && over.class(f.node.kind()) == "directive"));
        let stmts: Vec<&[u8]> = pieces
            .iter()
            .filter(|f| f.node.kind() == "assignment_statement")
            .map(|f| &source[f.node.byte_range()])
            .collect();
        assert_eq!(stmts, [b"X := 1".as_slice(), b"X := 3".as_slice()]);
    }

    #[test]
    fn an_unclosed_else_on_the_last_line_has_an_empty_arm() {
        let policy = Policy::bundled();
        let mut parser = parser();
        let cases: [(&[u8], (usize, usize)); 4] = [
            (b"codeunit 1 C\n{\n}\n#if A\n#else", (28, 28)),
            (b"codeunit 1 C\n{\n}\n#if A\n#else // c", (33, 33)),
            (b"codeunit 1 C\n{\n}\n#if A\n#else\n", (28, 28)),
            (b"codeunit 1 C\r\n{\r\n}\r\n#if A\r\n#else\r\n", (32, 32)),
        ];
        for (src, want) in cases {
            let tree = parser.parse(src, None).unwrap();
            let doc = Document::new(&tree, src, &policy);
            assert_eq!(doc.groups[0].arms[1].raw_range, want, "{:?}", String::from_utf8_lossy(src));
        }
    }
}
