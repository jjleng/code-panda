package project

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"time"

	"github.com/jjleng/cp-runner/pkg/proxy"
	"github.com/jjleng/cp-runner/pkg/runtime"
)

const startupTimeout = 60 * time.Second

type Orchestrator struct {
	projectPath  string
	supervisor   *runtime.Supervisor
	proxyServer  *proxy.ProxyServer
	isRestarting bool
	mu           sync.Mutex
	appPort      int
}

func NewOrchestrator(projectPath string, pkgManager runtime.PackageManager) *Orchestrator {
	return &Orchestrator{
		projectPath:  projectPath,
		supervisor:   runtime.NewSupervisor(projectPath, pkgManager),
		isRestarting: false,
	}
}

func (o *Orchestrator) setRestarting(value bool) bool {
	o.mu.Lock()
	defer o.mu.Unlock()

	if value && o.isRestarting {
		// Already restarting
		return false
	}
	o.isRestarting = value
	return true
}

func (o *Orchestrator) RestartProject(port int, appPort int) error {
	// Try to set restarting state to true
	if !o.setRestarting(true) {
		// If already restarting, just wait for it to complete
		ctx, cancel := context.WithTimeout(context.Background(), startupTimeout)
		defer cancel()
		return o.waitForAppReady(ctx)
	}

	// Ensure we reset the restarting state when done
	defer o.setRestarting(false)

	o.StopProject()

	o.mu.Lock()
	o.appPort = appPort
	o.mu.Unlock()

	// Check if node_modules exists
	nodeModulesPath := filepath.Join(o.projectPath, "node_modules")
	if _, err := os.Stat(nodeModulesPath); os.IsNotExist(err) {
		// Only install dependencies if node_modules doesn't exist
		installCmd := exec.Command("sh", "-c", o.supervisor.GetPackageManager().GetInstallCmd())
		installCmd.Dir = o.projectPath
		if output, err := installCmd.CombinedOutput(); err != nil {
			return fmt.Errorf("failed to install dependencies: %v\nOutput: %s", err, output)
		}
	}

	// Set up and start the proxy server
	proxyServer := proxy.NewProxyServer(port, appPort)
	proxyServer.SetLoadingMode(true)
	o.proxyServer = proxyServer

	// Start the proxy in a goroutine
	go func() {
		if err := proxyServer.Start(); err != nil {
			fmt.Printf("Proxy server error: %v\n", err)
		}
	}()

	// Start the development server
	if err := o.supervisor.StartDevServer(appPort); err != nil {
		proxyServer.Stop()
		return fmt.Errorf("failed to start development server: %w", err)
	}

	// Create a context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), startupTimeout)
	defer cancel()

	// Wait for the app to be ready
	if err := o.waitForAppReady(ctx); err != nil {
		proxyServer.Stop()
		o.supervisor.StopCurrentProcess()
		return fmt.Errorf("app failed to start: %w", err)
	}

	// Switch to app mode
	proxyServer.SetLoadingMode(false)

	return nil
}

func (o *Orchestrator) waitForAppReady(ctx context.Context) error {
	client := &http.Client{
		Timeout: 1 * time.Second,
	}

	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()

	for {
		url := fmt.Sprintf("http://localhost:%d/", o.appPort)

		select {
		case <-ctx.Done():
			return fmt.Errorf("timeout waiting for app to start")
		case <-ticker.C:
			req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
			if err != nil {
				continue
			}

			resp, err := client.Do(req)
			if err != nil {
				// Log the error but continue trying
				log.Printf("App server not ready: %v", err)
				continue
			}

			// Close body immediately if request succeeds but there's an error reading it
			if resp != nil {
				defer resp.Body.Close()
			}

			// The app server responded successfully, so we know it's ready
			// We don't care about the actual response status code since different
			// frameworks might return different codes on their root path
			return nil
		}
	}
}

func (o *Orchestrator) StopProject() bool {
	// Create a context with timeout to prevent infinite waiting
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Use a channel to handle the result
	done := make(chan bool, 1)
	var success bool

	// Lock before any operations to ensure thread safety
	o.mu.Lock()
	defer o.mu.Unlock()

	var proxyServer *proxy.ProxyServer
	// Store proxy server reference so we can stop it even after timeout
	if o.proxyServer != nil {
		proxyServer = o.proxyServer
		o.proxyServer = nil
	}

	go func() {
		defer func() {
			if r := recover(); r != nil {
				log.Printf("Panic recovered in StopProject: %v", r)
				done <- false
			}
		}()

		// Stop the proxy server if it's running
		if proxyServer != nil {
			proxyServer.Stop()
		}

		// Stop the development server
		success = o.supervisor.StopCurrentProcess()
		done <- success
	}()

	// Wait for completion or timeout
	select {
	case result := <-done:
		return result
	case <-ctx.Done():
		log.Printf("StopProject timed out after 10 seconds, forcing stop")
		// Force stop both proxy server and development server on timeout
		if proxyServer != nil {
			proxyServer.Stop()
		}
		o.supervisor.StopCurrentProcess()
		return false
	}
}

func (o *Orchestrator) Cleanup() {
	if success := o.StopProject(); !success {
		log.Printf("Warning: StopProject failed during cleanup")
	}
}

func (o *Orchestrator) RunLint() (bool, string) {
	return o.supervisor.RunLint()
}

func (o *Orchestrator) CheckBuildErrors() (bool, string) {
	return o.supervisor.CheckBuildErrors()
}

func (o *Orchestrator) IsRestarting() bool {
	o.mu.Lock()
	defer o.mu.Unlock()
	return o.isRestarting
}

func (o *Orchestrator) GetAppPort() int {
	o.mu.Lock()
	defer o.mu.Unlock()
	return o.appPort
}

func (o *Orchestrator) GetProjectPath() string {
	return o.projectPath
}

func (o *Orchestrator) AddPackage(packageName string) (bool, string) {
	return o.supervisor.AddPackage(packageName)
}

// IsRunning checks if the project server is running and healthy
func (o *Orchestrator) IsRunning() bool {
	o.mu.Lock()
	if o.proxyServer == nil || o.isRestarting {
		o.mu.Unlock()
		return false
	}
	appPort := o.appPort
	o.mu.Unlock()

	// Create a context with a short timeout for the health check
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Try to connect to the app server
	client := &http.Client{
		Timeout: 1 * time.Second,
	}

	url := fmt.Sprintf("http://localhost:%d/", appPort)
	req, err := http.NewRequestWithContext(ctx, "HEAD", url, nil)
	if err != nil {
		return false
	}

	resp, err := client.Do(req)
	if err != nil {
		return false
	}
	resp.Body.Close()
	return true
}
