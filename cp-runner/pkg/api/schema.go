package api

// FileSystemResponse represents a response containing file system structure
type FileSystemResponse struct {
	Body struct {
		Root *FileNode `json:"root" doc:"Root node of the file system tree"`
	}
}

// FileNode represents a file or directory in the file system
type FileNode struct {
	Name     string     `json:"name" doc:"Name of the file or directory"`
	Type     string     `json:"type" doc:"Type of the node (file or folder)"`
	Children []FileNode `json:"children,omitempty" doc:"Child nodes for directories"`
}

// ProjectOperationRequest represents a request to perform an operation on a project
type ProjectOperationRequest struct {
	Body struct {
		ProjectID string `json:"project_id" required:"true" doc:"ID of the project"`
	}
}

// ProjectOperationResponse represents a response from a project operation
type ProjectOperationResponse struct {
	Body struct {
		Message string `json:"message" doc:"Operation result message"`
	}
}

// LintResponse represents a response from a lint operation
type LintResponse struct {
	Body struct {
		Message    string `json:"message" doc:"Linting output message"`
		LintErrors bool   `json:"lintErrors" doc:"Whether there were any lint errors"`
	}
}

// BuildErrorResponse represents a response from a build error check
type BuildErrorResponse struct {
	Body struct {
		Message     string `json:"message" doc:"Build error check output message"`
		BuildErrors bool   `json:"buildErrors" doc:"Whether there were any build errors"`
	}
}

type GetFileTreeRequest struct {
	ProjectID string `json:"project_id" query:"project_id" required:"true" doc:"ID of the project"`
}

// GetFileContentRequest represents a request to get file content
type GetFileContentRequest struct {
	ProjectID string `json:"project_id" query:"project_id" required:"true" doc:"ID of the project"`
	FilePath  string `json:"file_path" query:"file_path" required:"true" doc:"Path to the file relative to project path"`
}

// GetFileContentResponse represents a response containing file content
type GetFileContentResponse struct {
	Body struct {
		Content  string `json:"content" doc:"Content of the file (base64 encoded for binary files)"`
		MimeType string `json:"mime_type" doc:"MIME type of the file"`
	}
}

// GetCommitsRequest represents a request to get list of commits
type GetCommitsRequest struct {
	ProjectID string `json:"project_id" query:"project_id" required:"true" doc:"ID of the project"`
	Cursor    string `json:"cursor" query:"cursor" doc:"Cursor for pagination (commit hash)"`
	Limit     int    `json:"limit" query:"limit" doc:"Maximum number of commits to return (default: 20)"`
}

// CommitFile represents a file in a commit
type CommitFile struct {
	Path string `json:"path" doc:"Path of the changed file"`
	Type string `json:"type" doc:"Type of change (added, modified, deleted)"`
}

// Commit represents a git commit
type Commit struct {
	Hash    string       `json:"hash" doc:"Commit hash"`
	Message string       `json:"message" doc:"Commit message"`
	Date    string       `json:"date" doc:"Commit date"`
	Files   []CommitFile `json:"files" doc:"Changed files in the commit"`
}

// GetCommitsResponse represents a response containing list of commits
type GetCommitsResponse struct {
	Body struct {
		Commits     []Commit `json:"commits" doc:"List of commits"`
		NextCursor  string   `json:"next_cursor,omitempty" doc:"Cursor for the next page"`
		HasNextPage bool     `json:"has_next_page" doc:"Whether there are more commits available"`
	}
}

// GetCommitDiffRequest represents a request to get commit diff
type GetCommitDiffRequest struct {
	ProjectID  string `json:"project_id" query:"project_id" required:"true" doc:"ID of the project"`
	CommitHash string `json:"commit_hash" query:"commit_hash" required:"true" doc:"Hash of the commit"`
}

// GetCommitDiffResponse represents a response containing commit diff
type GetCommitDiffResponse struct {
	Body struct {
		Changes []FileDiff `json:"changes" doc:"List of file changes"`
	}
}

// GetFileDiffRequest represents a request to get file diff
type GetFileDiffRequest struct {
	ProjectID  string `json:"project_id" query:"project_id" required:"true" doc:"ID of the project"`
	CommitHash string `json:"commit_hash" query:"commit_hash" required:"true" doc:"Hash of the commit"`
	FilePath   string `json:"file_path" query:"file_path" required:"true" doc:"Path of the file"`
}

// FileDiff represents changes in a file
type FileDiff struct {
	Path    string `json:"path" doc:"Path of the file"`
	OldText string `json:"old_text" doc:"Original content of the file"`
	NewText string `json:"new_text" doc:"Modified content of the file"`
}

// GetFileDiffResponse represents a response containing file diff
type GetFileDiffResponse struct {
	Body struct {
		Diff FileDiff `json:"diff" doc:"File diff details"`
	}
}

// SwitchCommitRequest represents a request to switch to a specific commit
type SwitchCommitRequest struct {
	Body struct {
		ProjectID  string `json:"project_id" required:"true" doc:"ID of the project"`
		CommitHash string `json:"commit_hash" required:"true" doc:"Hash of the commit to switch to"`
	}
}

// SwitchCommitResponse represents a response from a commit switch operation
type SwitchCommitResponse struct {
	Body struct {
		Message string `json:"message" doc:"Operation result message"`
	}
}

// AddPackageRequest represents a request to add a package
type AddPackageRequest struct {
	Body struct {
		ProjectID     string `json:"project_id" required:"true" doc:"ID of the project"`
		PackageName   string `json:"package_name" required:"true" doc:"Name of the package to add"`
		RestartServer bool   `json:"restart_server" doc:"Whether to restart the server after installing the package (default: false)"`
	}
}

// AddPackageResponse represents a response from a package installation
type AddPackageResponse struct {
	Body struct {
		Success bool   `json:"success" doc:"Whether the package installation was successful"`
		Message string `json:"message" doc:"Installation output or error message"`
	}
}
