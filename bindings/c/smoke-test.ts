// bindings/c/smoke-test.ts — Bun-side smoke test for the fat shim.
// Usage: bun run smoke-test.ts <path-to-artifact>
import { dlopen, FFIType, ptr } from "bun:ffi";
import { argv } from "node:process";

const lib = argv[2];
if (!lib) {
  console.error("usage: bun run smoke-test.ts <lib path>");
  process.exit(1);
}

const v = dlopen(lib, {
  al_shim_abi_version: { args: [], returns: FFIType.u32 },
});
const version = v.symbols.al_shim_abi_version();
if (version !== (1 << 16)) {
  console.error(`smoke: unexpected ABI version 0x${version.toString(16)}`);
  process.exit(1);
}

const h = dlopen(lib, {
  al_shim_language: { args: [], returns: FFIType.ptr },
  al_shim_parser_new: { args: [], returns: FFIType.ptr },
  al_shim_parser_set_language: { args: [FFIType.ptr, FFIType.ptr], returns: FFIType.u32 },
  al_shim_parse_utf8: { args: [FFIType.ptr, FFIType.ptr, FFIType.u32], returns: FFIType.ptr },
  al_shim_tree_root_node: { args: [FFIType.ptr, FFIType.ptr], returns: FFIType.void },
  al_shim_node_type: { args: [FFIType.ptr], returns: FFIType.cstring },
  al_shim_node_size: { args: [], returns: FFIType.u32 },
  al_shim_tree_delete: { args: [FFIType.ptr], returns: FFIType.void },
  al_shim_parser_delete: { args: [FFIType.ptr], returns: FFIType.void },
});
const language = h.symbols.al_shim_language();
const parser = h.symbols.al_shim_parser_new();
if (h.symbols.al_shim_parser_set_language(parser, language) === 0) {
  console.error("smoke: set_language failed");
  process.exit(1);
}
const source = new TextEncoder().encode('codeunit 50100 "Test" { procedure Foo() begin end; }');
const tree = h.symbols.al_shim_parse_utf8(parser, ptr(source), source.byteLength);
if (!tree) {
  console.error("smoke: parse returned null");
  process.exit(1);
}
const nodeBuf = new Uint8Array(h.symbols.al_shim_node_size());
h.symbols.al_shim_tree_root_node(tree, ptr(nodeBuf));
const rootType = h.symbols.al_shim_node_type(ptr(nodeBuf))?.toString();
if (rootType !== "source_file") {
  console.error(`smoke: expected root type 'source_file', got '${rootType}'`);
  process.exit(1);
}
h.symbols.al_shim_tree_delete(tree);
h.symbols.al_shim_parser_delete(parser);
console.log("smoke: OK");
