package tree_sitter_al_test

import (
	"testing"

	tree_sitter_al "github.com/sshadows/tree-sitter-al/bindings/go"
	tree_sitter "github.com/tree-sitter/go-tree-sitter"
)

// NewLanguage only wraps the pointer, so a nil check cannot see an ABI the
// runtime refuses. SetLanguage is where go-tree-sitter compares the grammar's
// ABI (15) against the runtime's supported range, so that is the real load test.
func TestCanLoadGrammar(t *testing.T) {
	parser := tree_sitter.NewParser()
	defer parser.Close()
	if err := parser.SetLanguage(tree_sitter.NewLanguage(tree_sitter_al.Language())); err != nil {
		t.Fatalf("Error loading AL grammar: %v", err)
	}
	tree := parser.Parse([]byte("codeunit 50100 T { trigger OnRun() begin end; }\n"), nil)
	defer tree.Close()
	if root := tree.RootNode(); root.HasError() {
		t.Errorf("parse has errors: %s", root.ToSexp())
	}
}
