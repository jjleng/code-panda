package api

import (
	"context"
	"encoding/base64"
	"fmt"
	"log"
	"mime"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"

	"github.com/danielgtaylor/huma/v2"
	"github.com/danielgtaylor/huma/v2/adapters/humachi"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/jjleng/cp-runner/pkg/filesystem"
	"github.com/jjleng/cp-runner/pkg/project"
	"github.com/jjleng/cp-runner/pkg/proxy"
	"github.com/jjleng/cp-runner/pkg/runtime"
)

type ControlPlaneServer struct {
	orchestrators  map[string]*project.Orchestrator
	mu             sync.RWMutex
	packageManager runtime.PackageManager
	port           int
	proxyPort      int
	workspacePath  string // Base path for all project workspaces
}

// getProjectPath constructs the full project path from project ID
func (s *ControlPlaneServer) getProjectPath(projectID string) string {
	return filepath.Join(s.workspacePath, projectID)
}

// execGitCommand executes a git command and returns its output
func execGitCommand(workingDir string, args ...string) (string, error) {
	cmd := exec.Command("git", args...)
	cmd.Dir = workingDir
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("git command failed: %v: %s", err, output)
	}
	return string(output), nil
}

// parseGitLog parses git log output into Commit structs
func parseGitLog(output string) []Commit {
	lines := strings.Split(output, "\n")
	commits := []Commit{}

	for _, line := range lines {
		if line == "" {
			continue
		}

		parts := strings.SplitN(line, " ", 5)
		if len(parts) < 5 {
			log.Printf("Invalid line format: %s\n", line)
			continue
		}

		date := fmt.Sprintf("%s %s %s", parts[0], parts[1], parts[2])
		hash := parts[3]
		remaining := parts[4]
		message := remaining

		if idx := strings.Index(remaining, ")"); idx != -1 {
			branchStart := strings.Index(remaining, "(")
			if branchStart != -1 && branchStart < idx {
				message = strings.TrimSpace(remaining[idx+1:])
			}
		}

		if idx := strings.LastIndex(message, " ["); idx != -1 {
			message = strings.TrimSpace(message[:idx])
		}

		commits = append(commits, Commit{
			Hash:    hash,
			Date:    date,
			Message: message,
			Files:   []CommitFile{},
		})
	}

	return commits
}

func NewControlPlaneServer(port int, proxyPort int, pkgManager runtime.PackageManager, workspacePath string) *ControlPlaneServer {
	if !pkgManager.IsValid() {
		pkgManager = runtime.PNPM
	}
	return &ControlPlaneServer{
		orchestrators:  make(map[string]*project.Orchestrator),
		packageManager: pkgManager,
		port:           port,
		proxyPort:      proxyPort,
		workspacePath:  workspacePath,
	}
}

func (s *ControlPlaneServer) getOrchestrator(projectPath string, pkgManager runtime.PackageManager) *project.Orchestrator {
	s.mu.Lock()
	defer s.mu.Unlock()

	if orch, exists := s.orchestrators[projectPath]; exists {
		return orch
	}

	orch := project.NewOrchestrator(projectPath, pkgManager)
	s.orchestrators[projectPath] = orch
	return orch
}

func (s *ControlPlaneServer) Routes() chi.Router {
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Accept, Authorization, Content-Type")
			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusOK)
				return
			}
			next.ServeHTTP(w, r)
		})
	})

	// Create the API configuration and router
	api := humachi.New(r, huma.DefaultConfig("CodePanda Runner Control Plane API", "1.0.0"))

	type HealthResponse struct {
		Status int `json:"status"`
	}

	type CheckPreviewRequest struct {
		ProjectID string `query:"project_id"`
	}

	type CheckPreviewResponse struct {
		Body struct {
			Status  int  `json:"status"`
			Healthy bool `json:"healthy"`
		}
	}

	// Public routes (no auth required)
	huma.Register(api, huma.Operation{
		OperationID: "health",
		Method:      http.MethodGet,
		Path:        "/health",
		Summary:     "Health check endpoint",
		Description: "Returns 200 OK if the service is healthy",
		Tags:        []string{"System"},
	}, func(ctx context.Context, _ *struct{}) (*HealthResponse, error) {
		return &HealthResponse{Status: http.StatusOK}, nil
	})

	// Add preview server status check endpoint
	huma.Register(api, huma.Operation{
		OperationID: "check-preview",
		Method:      http.MethodGet,
		Path:        "/check-preview",
		Summary:     "Check preview server status",
		Description: "Returns status of the preview server for a project",
		Tags:        []string{"System"},
	}, func(ctx context.Context, input *CheckPreviewRequest) (*CheckPreviewResponse, error) {
		if input.ProjectID == "" {
			return nil, huma.Error400BadRequest("project ID is required")
		}

		s.mu.RLock()
		orch, exists := s.orchestrators[s.getProjectPath(input.ProjectID)]
		s.mu.RUnlock()

		resp := &CheckPreviewResponse{}

		if !exists || !orch.IsRunning() {
			resp.Body.Status = http.StatusServiceUnavailable
			resp.Body.Healthy = false
		} else {
			resp.Body.Status = http.StatusOK
			resp.Body.Healthy = true
		}

		return resp, nil
	})

	huma.Register(api, huma.Operation{
		OperationID:   "start-project",
		Method:        http.MethodPost,
		Path:          "/projects/start",
		Summary:       "Start a project",
		Description:   "Starts a project with given ID",
		Tags:          []string{"Projects"},
		DefaultStatus: http.StatusCreated, // 201 for resource creation
		Errors:        []int{500},
	}, s.handleStartProject)

	huma.Register(api, huma.Operation{
		OperationID: "stop-project",
		Method:      http.MethodPost,
		Path:        "/projects/stop",
		Summary:     "Stop a project",
		Description: "Stops a running project",
		Tags:        []string{"Projects"},
		Errors:      []int{500},
	}, s.handleStopProject)

	huma.Register(api, huma.Operation{
		OperationID: "lint-project",
		Method:      http.MethodPost,
		Path:        "/projects/lint",
		Summary:     "Run linting",
		Description: "Run linting checks on a project",
		Tags:        []string{"Projects"},
		Errors:      []int{500},
	}, s.handleRunLint)

	huma.Register(api, huma.Operation{
		OperationID: "add-package",
		Method:      http.MethodPost,
		Path:        "/projects/add-package",
		Summary:     "Add package",
		Description: "Add a package using the project's package manager",
		Tags:        []string{"Projects"},
		Errors:      []int{500},
	}, s.handleAddPackage)

	huma.Register(api, huma.Operation{
		OperationID: "check-build-errors",
		Method:      http.MethodPost,
		Path:        "/projects/check-errors",
		Summary:     "Check build errors",
		Description: "Check for build errors in a project",
		Tags:        []string{"Projects"},
		Errors:      []int{500},
	}, s.handleCheckBuildErrors)

	huma.Register(api, huma.Operation{
		OperationID: "get-file-tree",
		Method:      http.MethodGet,
		Path:        "/files/tree",
		Summary:     "Get file system tree",
		Description: "Get the file system tree structure for a project",
		Tags:        []string{"Files"},
		Errors:      []int{500},
	}, s.handleGetFileTree)

	huma.Register(api, huma.Operation{
		OperationID: "get-file-content",
		Method:      http.MethodGet,
		Path:        "/files/content",
		Summary:     "Get file content",
		Description: "Get the content of a specific file",
		Tags:        []string{"Files"},
		Errors:      []int{400, 500},
	}, s.handleGetFileContent)

	// Register git operations
	huma.Register(api, huma.Operation{
		OperationID: "get-commits",
		Method:      http.MethodGet,
		Path:        "/git/commits",
		Summary:     "Get commit history",
		Description: "Get list of commits in the repository",
		Tags:        []string{"Git"},
		Errors:      []int{400, 500},
	}, s.handleGetCommits)

	huma.Register(api, huma.Operation{
		OperationID: "get-commit-diff",
		Method:      http.MethodGet,
		Path:        "/git/commits/diff",
		Summary:     "Get commit diff",
		Description: "Get diff for a specific commit",
		Tags:        []string{"Git"},
		Errors:      []int{400, 500},
	}, s.handleGetCommitDiff)

	huma.Register(api, huma.Operation{
		OperationID: "get-file-diff",
		Method:      http.MethodGet,
		Path:        "/git/commits/file_diff",
		Summary:     "Get file diff",
		Description: "Get diff for a specific file in a commit",
		Tags:        []string{"Git"},
		Errors:      []int{400, 500},
	}, s.handleGetFileDiff)

	huma.Register(api, huma.Operation{
		OperationID: "switch-commit",
		Method:      http.MethodPost,
		Path:        "/git/commits/switch",
		Summary:     "Switch to commit",
		Description: "Switch working directory to a specific commit",
		Tags:        []string{"Git"},
		Errors:      []int{400, 500},
	}, s.handleSwitchCommit)

	return r
}

// handleSwitchCommit switches the working directory to a specific commit
func (s *ControlPlaneServer) handleSwitchCommit(ctx context.Context, input *SwitchCommitRequest) (*SwitchCommitResponse, error) {
	projectPath := s.getProjectPath(input.Body.ProjectID)
	commitHash := input.Body.CommitHash

	// Validate project path exists and is a git repository
	if _, err := os.Stat(filepath.Join(projectPath, ".git")); os.IsNotExist(err) {
		return nil, huma.Error400BadRequest("not a git repository")
	}

	// Use git reset --hard to reset to the specified commit
	// This will discard all uncommitted changes and reset the branch pointer
	if _, err := execGitCommand(projectPath, "reset", "--hard", commitHash); err != nil {
		return nil, huma.Error500InternalServerError(fmt.Sprintf("failed to reset to commit: %v", err), err)
	}

	resp := &SwitchCommitResponse{}
	resp.Body.Message = fmt.Sprintf("Successfully reset to commit %s", commitHash)
	return resp, nil
}

// handleGetFileTree returns a tree structure of the file system
func (s *ControlPlaneServer) handleGetFileTree(ctx context.Context, input *GetFileTreeRequest) (*FileSystemResponse, error) {
	if input.ProjectID == "" {
		return nil, huma.Error400BadRequest("project ID is required")
	}

	projectPath := s.getProjectPath(input.ProjectID)
	log.Printf("Getting file tree for project at %s\n", projectPath)

	// Build the file tree using the filesystem package
	tree, err := filesystem.BuildFileTree(projectPath)
	if err != nil {
		return nil, huma.Error500InternalServerError(fmt.Sprintf("Failed to build file tree: %v", err), err)
	}

	fileNode := FileNode{
		Name: tree.Name,
		Type: tree.Type,
	}
	if tree.Children != nil {
		fileNode.Children = make([]FileNode, len(tree.Children))
		for i, child := range tree.Children {
			fileNode.Children[i] = convertFsNode(child)
		}
	}

	resp := &FileSystemResponse{}
	resp.Body.Root = &fileNode

	return resp, nil
}

// convertFsNode converts a filesystem.Node to a FileNode
func convertFsNode(node *filesystem.Node) FileNode {
	fileNode := FileNode{
		Name: node.Name,
		Type: node.Type,
	}
	if node.Children != nil {
		fileNode.Children = make([]FileNode, len(node.Children))
		for i, child := range node.Children {
			fileNode.Children[i] = convertFsNode(child)
		}
	}
	return fileNode
}

// handleGetFileContent returns the content of a specific file
func (s *ControlPlaneServer) handleGetFileContent(ctx context.Context, input *GetFileContentRequest) (*GetFileContentResponse, error) {
	if input.ProjectID == "" || input.FilePath == "" {
		return nil, huma.Error400BadRequest("project ID and file path are required")
	}

	projectPath := s.getProjectPath(input.ProjectID)
	filePath := filepath.Clean(filepath.FromSlash(input.FilePath))

	// Ensure the final path is within the project directory for security
	fullPath := filepath.Join(projectPath, filePath)
	if !strings.HasPrefix(fullPath, projectPath) {
		return nil, huma.Error400BadRequest("invalid file path: attempting to access file outside project directory")
	}

	// Check if file exists
	fileInfo, err := os.Stat(fullPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, huma.Error400BadRequest(fmt.Sprintf("file not found: %s", filePath))
		}
		return nil, huma.Error500InternalServerError(fmt.Sprintf("failed to access file: %v", err), err)
	}

	// Ensure it's a file, not a directory
	if fileInfo.IsDir() {
		return nil, huma.Error400BadRequest(fmt.Sprintf("path is a directory, not a file: %s", filePath))
	}

	// Read file content
	content, err := os.ReadFile(fullPath)
	if err != nil {
		return nil, huma.Error500InternalServerError(fmt.Sprintf("failed to read file: %v", err), err)
	}

	// Detect MIME type
	mimeType := http.DetectContentType(content)
	if mimeType == "" {
		// If we can't determine MIME type from extension, try to detect it from content
		mimeType = mime.TypeByExtension(filepath.Ext(filePath))
	}

	resp := &GetFileContentResponse{}

	resp.Body.Content = base64.StdEncoding.EncodeToString(content)

	resp.Body.MimeType = mimeType
	return resp, nil
}

func (s *ControlPlaneServer) stopAllProjects() {
	s.mu.Lock()
	defer s.mu.Unlock()

	log.Println("Stopping all running projects")
	for path, orch := range s.orchestrators {
		if orch.IsRunning() {
			log.Printf("Stopping project at path: %s", path)
			if !orch.StopProject() {
				log.Printf("Warning: Failed to stop project at %s", path)
			}
		}
	}
}

func (s *ControlPlaneServer) handleStartProject(ctx context.Context, input *ProjectOperationRequest) (*ProjectOperationResponse, error) {
	projectPath := s.getProjectPath(input.Body.ProjectID)

	// Check if project directory exists
	if _, err := os.Stat(projectPath); os.IsNotExist(err) {
		return nil, huma.Error400BadRequest("Project directory does not exist")
	}

	// Stop all running projects to free up the proxy port
	s.stopAllProjects()

	appPort, err := proxy.FindFreePort()
	if err != nil {
		return nil, huma.Error500InternalServerError(fmt.Sprintf("Failed to find free port: %v", err), err)
	}

	orch := s.getOrchestrator(projectPath, s.packageManager)

	if err := orch.RestartProject(s.proxyPort, appPort); err != nil {
		return nil, huma.Error500InternalServerError(fmt.Sprintf("Failed to start project: %v", err), err)
	}

	resp := &ProjectOperationResponse{}
	resp.Body.Message = "Project started successfully"
	return resp, nil
}

func (s *ControlPlaneServer) handleStopProject(ctx context.Context, input *ProjectOperationRequest) (*ProjectOperationResponse, error) {
	projectPath := s.getProjectPath(input.Body.ProjectID)
	orch := s.getOrchestrator(projectPath, s.packageManager)
	success := orch.StopProject()

	if !success {
		return nil, huma.Error500InternalServerError("Failed to stop project")
	}

	resp := &ProjectOperationResponse{}
	resp.Body.Message = "Project stopped successfully"
	return resp, nil
}

func (s *ControlPlaneServer) handleRunLint(ctx context.Context, input *ProjectOperationRequest) (*LintResponse, error) {
	projectPath := s.getProjectPath(input.Body.ProjectID)
	orch := s.getOrchestrator(projectPath, s.packageManager)
	success, output := orch.RunLint()

	resp := &LintResponse{}
	resp.Body.Message = output
	resp.Body.LintErrors = !success // invert since RunLint returns true when there are no errors
	return resp, nil
}

func (s *ControlPlaneServer) handleCheckBuildErrors(ctx context.Context, input *ProjectOperationRequest) (*BuildErrorResponse, error) {
	projectPath := s.getProjectPath(input.Body.ProjectID)
	orch := s.getOrchestrator(projectPath, s.packageManager)
	success, output := orch.CheckBuildErrors()

	resp := &BuildErrorResponse{}
	resp.Body.Message = output
	resp.Body.BuildErrors = !success // invert since CheckBuildErrors returns true when there are no errors
	return resp, nil
}

// handleGetCommits returns the commit history of a repository
func (s *ControlPlaneServer) handleGetCommits(ctx context.Context, input *GetCommitsRequest) (*GetCommitsResponse, error) {
	projectPath := s.getProjectPath(input.ProjectID)

	if _, err := os.Stat(filepath.Join(projectPath, ".git")); os.IsNotExist(err) {
		return nil, huma.Error400BadRequest("not a git repository")
	}

	// Set default limit if not specified
	limit := input.Limit
	if limit <= 0 {
		limit = 20
	}

	// Fetch all commits, we'll manually handle pagination
	args := []string{"--no-pager", "log", "--pretty=format:%ai %H %d %s [%an]"}

	// Get git log with commit info
	output, err := execGitCommand(projectPath, args...)
	if err != nil {
		return nil, huma.Error500InternalServerError(fmt.Sprintf("failed to get git log: %v", err), err)
	}

	// Parse git log output into structured commits
	allCommits := parseGitLog(output)

	// Find starting index based on cursor
	startIndex := 0
	if input.Cursor != "" {
		for i, commit := range allCommits {
			if commit.Hash == input.Cursor {
				startIndex = i + 1 // Start from the commit after the cursor
				break
			}
		}
	}

	// Slice the commits to handle pagination
	endIndex := min(startIndex+limit, len(allCommits))

	// Check if we have more pages
	hasNextPage := endIndex < len(allCommits)

	// Get the page of commits
	var pageCommits []Commit
	if startIndex < len(allCommits) {
		pageCommits = allCommits[startIndex:endIndex]
	} else {
		pageCommits = []Commit{}
	}

	// Get files changed for each commit in this page
	for i := range pageCommits {
		// Get status of files in commit
		filesOutput, err := execGitCommand(projectPath, "show", "--name-status", "--pretty=format:", pageCommits[i].Hash)
		if err != nil {
			return nil, huma.Error500InternalServerError(fmt.Sprintf("failed to get changed files: %v", err), err)
		}

		// Parse changed files list with status
		files := strings.Split(strings.TrimSpace(filesOutput), "\n")
		for _, file := range files {
			if file == "" {
				continue
			}
			parts := strings.Fields(file)
			if len(parts) < 2 {
				continue
			}

			status := parts[0]
			path := parts[1]
			fileType := ""

			switch status {
			case "A":
				fileType = "added"
			case "M":
				fileType = "modified"
			case "D":
				fileType = "deleted"
			default:
				fileType = "modified"
			}

			pageCommits[i].Files = append(pageCommits[i].Files, CommitFile{
				Path: path,
				Type: fileType,
			})
		}
	}

	resp := &GetCommitsResponse{}
	resp.Body.Commits = pageCommits
	resp.Body.HasNextPage = hasNextPage
	if hasNextPage && len(pageCommits) > 0 {
		resp.Body.NextCursor = pageCommits[len(pageCommits)-1].Hash
	}
	return resp, nil
}

// handleGetCommitDiff returns the diff for a specific commit
func (s *ControlPlaneServer) handleGetCommitDiff(ctx context.Context, input *GetCommitDiffRequest) (*GetCommitDiffResponse, error) {
	projectPath := s.getProjectPath(input.ProjectID)
	commitHash := input.CommitHash

	// Validate project path exists and is a git repository
	if _, err := os.Stat(filepath.Join(projectPath, ".git")); os.IsNotExist(err) {
		return nil, huma.Error400BadRequest("not a git repository")
	}

	// Get list of changed files
	filesOutput, err := execGitCommand(projectPath, "show", "--name-only", "--pretty=format:", commitHash)
	if err != nil {
		return nil, huma.Error500InternalServerError(fmt.Sprintf("failed to get changed files: %v", err), err)
	}

	files := strings.Split(strings.TrimSpace(filesOutput), "\n")
	changes := make([]FileDiff, 0, len(files))

	// Get diff for each changed file
	for _, file := range files {
		if file == "" {
			continue
		}

		// Get old version (before commit)
		oldContent, err := execGitCommand(projectPath, "show", fmt.Sprintf("%s^:%s", commitHash, file))
		if err != nil {
			oldContent = "" // File might be new
		}

		// Get new version (at commit)
		newContent, err := execGitCommand(projectPath, "show", fmt.Sprintf("%s:%s", commitHash, file))
		if err != nil {
			newContent = "" // File might be deleted
		}

		changes = append(changes, FileDiff{
			Path:    file,
			OldText: oldContent,
			NewText: newContent,
		})
	}

	resp := &GetCommitDiffResponse{}
	resp.Body.Changes = changes
	return resp, nil
}

func (s *ControlPlaneServer) handleAddPackage(ctx context.Context, input *AddPackageRequest) (*AddPackageResponse, error) {
	projectPath := s.getProjectPath(input.Body.ProjectID)
	orch := s.getOrchestrator(projectPath, s.packageManager)

	success, output := orch.AddPackage(input.Body.PackageName)

	resp := &AddPackageResponse{}
	resp.Body.Success = success
	resp.Body.Message = output

	// If package added successfully and restart is requested, restart the project
	if success && input.Body.RestartServer {
		// Stop all running projects to free up the proxy port
		s.stopAllProjects()

		// Find a free port for the application
		appPort, err := proxy.FindFreePort()
		if err != nil {
			log.Printf("Failed to find free port for restart: %v", err)
			resp.Body.Message += "\nWarning: Failed to restart server after package installation."
			return resp, nil
		}

		if err := orch.RestartProject(s.proxyPort, appPort); err != nil {
			log.Printf("Failed to restart project after adding package: %v", err)
			resp.Body.Message += "\nWarning: Failed to restart server after package installation."
		} else {
			resp.Body.Message += "\nServer restarted successfully with the new package."
		}
	} else if success && !input.Body.RestartServer {
		resp.Body.Message += "\nServer restart was not requested."
	}

	return resp, nil
}

// handleGetFileDiff returns the diff for a specific file in a commit
func (s *ControlPlaneServer) handleGetFileDiff(ctx context.Context, input *GetFileDiffRequest) (*GetFileDiffResponse, error) {
	projectPath := s.getProjectPath(input.ProjectID)
	commitHash := input.CommitHash
	filePath := input.FilePath

	// Validate project path exists and is a git repository
	if _, err := os.Stat(filepath.Join(projectPath, ".git")); os.IsNotExist(err) {
		return nil, huma.Error400BadRequest("not a git repository")
	}

	// Get old version (before commit)
	oldContent, err := execGitCommand(projectPath, "show", fmt.Sprintf("%s^:%s", commitHash, filePath))
	if err != nil {
		oldContent = "" // File might be new
	}

	// Get new version (at commit)
	newContent, err := execGitCommand(projectPath, "show", fmt.Sprintf("%s:%s", commitHash, filePath))
	if err != nil {
		newContent = "" // File might be deleted
	}

	resp := &GetFileDiffResponse{}
	resp.Body.Diff = FileDiff{
		Path:    filePath,
		OldText: oldContent,
		NewText: newContent,
	}
	return resp, nil
}
