package tree_sitter_al_test

import (
	"testing"

	tree_sitter "github.com/smacker/go-tree-sitter"
	"github.com/tree-sitter/tree-sitter-al"
)

func TestCanLoadGrammar(t *testing.T) {
	language := tree_sitter.NewLanguage(tree_sitter_al.Language())
	if language == nil {
		t.Errorf("Error loading Al grammar")
	}
}
