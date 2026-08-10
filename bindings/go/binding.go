package tree_sitter_al

// #cgo CFLAGS: -std=c11 -fPIC
// #include "../../src/parser.c"
// // REQUIRED -- same reason as Package.swift. parser.c references five
// // tree_sitter_al_external_scanner_* symbols that exist only in scanner.c,
// // and eight tokens depend on them (PROPERTY_NAME, CONTINUE_AS_IDENTIFIER,
// // PREPROC_OPEN/CLOSE, BEGIN_KEYWORD/END_KEYWORD, both PREPROC_SPLIT_*).
// // This was the tree-sitter template's unedited "add it here" placeholder.
// // Note `go build` on a library package does NOT catch this -- it compiles
// // without linking, so it passed while the binding was broken. Linking is
// // what fails.
// #include "../../src/scanner.c"
import "C"

import "unsafe"

// Get the tree-sitter Language for this grammar.
func Language() unsafe.Pointer {
	return unsafe.Pointer(C.tree_sitter_al())
}
