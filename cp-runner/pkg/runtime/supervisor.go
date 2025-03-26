package runtime

import (
	"bufio"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"sync"
	"time"
)

type Supervisor struct {
	projectPath   string
	pkgManager    PackageManager
	currentCmd    *exec.Cmd
	cmdMutex      sync.Mutex
	processOutput string
}

func NewSupervisor(projectPath string, pkgManager PackageManager) *Supervisor {
	return &Supervisor{
		projectPath: projectPath,
		pkgManager:  pkgManager,
	}
}

func (s *Supervisor) StartDevServer(port int) error {
	s.cmdMutex.Lock()
	defer s.cmdMutex.Unlock()

	if s.currentCmd != nil {
		s.StopCurrentProcess()
	}

	cmd := exec.Command(s.pkgManager.String(), "run", "dev", "--port", fmt.Sprintf("%d", port))
	cmd.Dir = s.projectPath
	cmd.Env = os.Environ()

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("failed to create stdout pipe: %w", err)
	}

	stderr, err := cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("failed to create stderr pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start dev server: %w", err)
	}

	s.currentCmd = cmd

	// Handle output in goroutines
	go s.handleOutput(stdout)
	go s.handleOutput(stderr)

	return nil
}

func (s *Supervisor) StopCurrentProcess() bool {
	s.cmdMutex.Lock()
	defer s.cmdMutex.Unlock()

	if s.currentCmd != nil && s.currentCmd.Process != nil {
		// Create channels for completion
		done := make(chan error, 1)
		processExited := make(chan struct{})

		// First try to interrupt the process gracefully
		if err := s.currentCmd.Process.Signal(os.Interrupt); err != nil {
			log.Printf("Failed to send interrupt signal: %v", err)
		}

		// Start a goroutine to wait for the process
		go func() {
			done <- s.currentCmd.Wait()
			close(processExited)
		}()

		// Wait for process to exit with timeout
		select {
		case <-time.After(5 * time.Second):
			// If timeout, force kill the process
			log.Printf("Process did not exit after interrupt, killing forcefully")
			if err := s.currentCmd.Process.Kill(); err != nil {
				log.Printf("Failed to kill process: %v", err)
				return false
			}
			// Wait for kill to take effect with another timeout
			select {
			case <-processExited:
				log.Printf("Process killed successfully")
			case <-time.After(2 * time.Second):
				log.Printf("Process kill operation timed out")
				return false
			}
		case err := <-done:
			if err != nil {
				log.Printf("Process exited with error: %v", err)
			} else {
				log.Printf("Process exited gracefully")
			}
		}

		// Clear process state
		s.currentCmd = nil
		s.processOutput = "" // Clear output buffer
		return true
	}

	// No process to stop
	s.currentCmd = nil
	s.processOutput = ""
	return false
}

func (s *Supervisor) RunLint() (bool, string) {
	cmd := exec.Command(s.pkgManager.String(), "run", "lint")
	cmd.Dir = s.projectPath
	output, err := cmd.CombinedOutput()
	return err == nil, string(output)
}

func (s *Supervisor) CheckBuildErrors() (bool, string) {
	// Running the full build command is expensive, so we'll just run the type check command
	typeCheckCmd := s.pkgManager.GetTypeCheckCmd()

	// Run the command using sh -c to ensure shell expansion works properly
	cmd := exec.Command("sh", "-c", typeCheckCmd)
	cmd.Dir = s.projectPath
	output, err := cmd.CombinedOutput()
	return err == nil, string(output)
}

func (s *Supervisor) handleOutput(pipe io.Reader) {
	scanner := bufio.NewScanner(pipe)
	for scanner.Scan() {
		s.cmdMutex.Lock()
		s.processOutput += scanner.Text() + "\n"
		s.cmdMutex.Unlock()
	}
}

func (s *Supervisor) GetProjectPath() string {
	return s.projectPath
}

func (s *Supervisor) Exists() bool {
	_, err := os.Stat(s.projectPath)
	return err == nil
}

func (s *Supervisor) GetLastOutput() string {
	s.cmdMutex.Lock()
	defer s.cmdMutex.Unlock()
	return s.processOutput
}

func (s *Supervisor) ClearOutput() {
	s.cmdMutex.Lock()
	defer s.cmdMutex.Unlock()
	s.processOutput = ""
}

// InstallDependencies installs project dependencies
func (s *Supervisor) InstallDependencies() error {
	if !s.Exists() {
		return fmt.Errorf("project directory does not exist: %s", s.projectPath)
	}

	cmd := exec.Command(s.pkgManager.String(), "install")
	cmd.Dir = s.projectPath

	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("failed to install dependencies: %s\nOutput: %s", err, string(output))
	}

	return nil
}

// GetPackageManager returns the current package manager
func (s *Supervisor) GetPackageManager() PackageManager {
	return s.pkgManager
}

// AddPackage installs a specific package
func (s *Supervisor) AddPackage(packageName string) (bool, string) {
	if !s.Exists() {
		return false, fmt.Sprintf("project directory does not exist: %s", s.projectPath)
	}

	cmd := exec.Command(s.pkgManager.String(), "add", packageName)
	cmd.Dir = s.projectPath

	output, err := cmd.CombinedOutput()
	if err != nil {
		return false, fmt.Sprintf("failed to add package %s: %v\nOutput: %s", packageName, err, output)
	}

	return true, string(output)
}

// IsProcessRunning checks if there's a process currently running
func (s *Supervisor) IsProcessRunning() bool {
	s.cmdMutex.Lock()
	defer s.cmdMutex.Unlock()
	return s.currentCmd != nil && s.currentCmd.Process != nil
}
