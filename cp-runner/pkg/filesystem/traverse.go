package filesystem

import (
	"os"
	"path/filepath"
	"strings"
)

// Node represents a file or directory in the file system
type Node struct {
	Name     string  `json:"name"`
	Type     string  `json:"type"` // "file" or "folder"
	Children []*Node `json:"children,omitempty"`
}

// skipDirectory checks if a directory should be skipped
func skipDirectory(name string) bool {
	// List of directory names to skip
	skippedDirs := []string{
		"node_modules",
		"__pycache__",
		".mypy_cache",
		".pytest_cache",
		".git",
		".next",
		"dist",
		"build",
		".venv",
		"venv",
		".env",
		".codepanda",
	}

	name = strings.ToLower(name)
	for _, dir := range skippedDirs {
		if name == dir {
			return true
		}
	}
	return false
}

// BuildFileTree creates a tree structure of the file system starting from the given path
func BuildFileTree(root string) (*Node, error) {
	info, err := os.Stat(root)
	if err != nil {
		return nil, err
	}

	baseName := filepath.Base(root)
	if info.IsDir() && skipDirectory(baseName) {
		return nil, nil
	}

	node := &Node{
		Name: baseName,
		Type: "folder",
	}

	if !info.IsDir() {
		node.Type = "file"
		return node, nil
	}

	entries, err := os.ReadDir(root)
	if err != nil {
		return nil, err
	}

	for _, entry := range entries {
		fullPath := filepath.Join(root, entry.Name())
		child, err := BuildFileTree(fullPath)
		if err != nil {
			continue // Skip files that can't be accessed
		}
		if child != nil { // Only append if child is not nil (not skipped)
			node.Children = append(node.Children, child)
		}
	}

	return node, nil
}
