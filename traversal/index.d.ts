// Types for @sshadows/tree-sitter-al/traversal (roadmap F0). The module works on the
// native `tree-sitter` SyntaxNode and on web-tree-sitter's Node: it uses only the
// members both share, listed in TSNode. Positions are UTF-8 byte offsets.

export interface TSNode {
  readonly type: string;
  readonly isNamed: boolean;
  readonly startIndex: number;
  readonly endIndex: number;
  readonly childCount: number;
  readonly parent: TSNode | null;
  readonly id: number;
  child(index: number): TSNode | null;
  fieldNameForChild(index: number): string | null;
  descendantForIndex(start: number, end?: number): TSNode | null;
}

export type TraversalClass =
  | 'ordinary' | 'branch-container' | 'assembler' | 'fragment' | 'token-alias' | 'directive' | 'trivia';

export interface PolicyEntry {
  class: TraversalClass;
  arm_boundary: 'own-directives' | 'cross-node' | 'assembler' | 'none';
  reason: string;
  role?: 'if' | 'elif' | 'else' | 'endif';
  alias_to?: string;
  hosts?: Record<string, string>;
}

export interface PolicyData {
  schema: 1;
  types: Record<string, PolicyEntry>;
}

export declare const SCHEMA: 1;
export declare const CLASSES: readonly TraversalClass[];
export declare const SPLIT_CLASSES: readonly TraversalClass[];
export declare class PolicyError extends Error {}
export declare class WrongDocument extends Error {}

export declare class Policy {
  readonly types: Record<string, PolicyEntry>;
  constructor(types: Record<string, PolicyEntry>);
  cls(type: string): TraversalClass;
  role(type: string): string | null;
  hostPolicy(container: string, parent: string, field: string | null): string | null;
}

/** The bundled policy.json, or the data given. */
export declare function loadPolicy(data?: PolicyData): Policy;

export interface Directive<N extends TSNode = TSNode> { role: string; start: number; end: number; node: N }
export interface ArmDescriptor {
  /** [revision, '#if' byte offset] */
  groupId: [string, number];
  armId: number;
  directiveOffsets: number[];
  rawRange: [number, number];
}
export interface Group<N extends TSNode = TSNode> { ifOffset: number; directives: Directive<N>[]; arms: ArmDescriptor[] }
export interface Fragment<N extends TSNode = TSNode> { field: string | null; node: N }
export interface ArmFragments<N extends TSNode = TSNode> { descriptor: ArmDescriptor; fragments: Fragment<N>[] }
export interface GroupArms<N extends TSNode = TSNode> { groupId: [string, number]; arms: ArmFragments<N>[] }
export interface SplitInfo<N extends TSNode = TSNode> { groups: GroupArms<N>[]; shared: Fragment<N>[] }

export interface Visit<N extends TSNode = TSNode> {
  node: N;
  cls: TraversalClass;
  type: string;
  field: string | null;
  start: number;
  end: number;
  /** [ifOffset, armId] pairs, outermost first. */
  arms: [number, number][];
  host: string | null;
  split: SplitInfo<N> | null;
}

export declare class Document<N extends TSNode = TSNode> {
  constructor(tree: { readonly rootNode: N }, text: string, policy: Policy);
  readonly text: string;
  readonly revision: string;
  readonly groups: Group<N>[];
  readonly unpaired: Directive<N>[];
  start(node: N): number;
  end(node: N): number;
  index(byte: number): number;
  descriptors(): ArmDescriptor[];
}

export interface WalkOptions<N extends TSNode = TSNode> {
  root?: N | null;
  includeDirectives?: boolean;
  includeTrivia?: boolean;
}

export declare function groupsOf<N extends TSNode>(node: N, doc: Document<N>): Group<N>[];
export declare function bindArm<N extends TSNode>(descriptor: ArmDescriptor, doc: Document<N>, policy: Policy): ArmFragments<N>;
/** The arm's fragments, each `fragment`-class piece expanded recursively into its children. */
export declare function armPieces<N extends TSNode>(armFragments: ArmFragments<N>, doc: Document<N>, policy: Policy): Fragment<N>[];
export declare function splitInfo<N extends TSNode>(node: N, doc: Document<N>, policy: Policy): SplitInfo<N> | null;
export declare function walk<N extends TSNode>(doc: Document<N>, policy: Policy, options?: WalkOptions<N>): Visit<N>[];
export declare function visitsToJson<N extends TSNode>(visits: Visit<N>[], doc: Document<N>): unknown[];
export declare function fnv1a64(bytes: Uint8Array): string;
export declare function byteTable(text: string): Uint32Array;
