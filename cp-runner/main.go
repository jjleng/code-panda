package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/jjleng/cp-runner/pkg/api"
	"github.com/jjleng/cp-runner/pkg/project"
	"github.com/jjleng/cp-runner/pkg/proxy"
	"github.com/jjleng/cp-runner/pkg/runtime"
	"github.com/joho/godotenv"
	"github.com/spf13/cobra"
)

type Environment string

const (
	Development Environment = "development"
	Production  Environment = "production"
)

// getEnvFile returns the appropriate environment file path based on the environment
func getEnvFile(env string) string {
	if env == string(Production) {
		return ".env.production"
	}
	return ".env.development"
}

func getEnvFromEnvVar() Environment {
	env := os.Getenv("ENV")
	if env == string(Production) {
		return Production
	}
	return Development
}

func main() {
	var rootCmd = &cobra.Command{
		Use:   "CodePanda",
		Short: "CP Runner - Project Development Tool",
	}

	// preview command
	var (
		packageManager string
		port           int
	)

	previewCmd := &cobra.Command{
		Use:   "preview [PROJECT_PATH]",
		Short: "Run the development preview server",
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			projectPath := "."
			if len(args) > 0 {
				projectPath = args[0]
			}

			// Parse package manager
			pm, err := runtime.ParsePackageManager(packageManager)
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}

			// Find a free port for the app server
			appPort, err := proxy.FindFreePort()
			if err != nil {
				log.Fatalf("Failed to find free port: %v", err)
			}

			// Initialize project orchestrator
			orchestrator := project.NewOrchestrator(projectPath, pm)

			// Run the project
			if err := orchestrator.RestartProject(port, appPort); err != nil {
				log.Fatalf("Failed to start project: %v", err)
			}

			fmt.Printf("Development server started on port %d\n", port)

			// Keep the process running
			select {}
		},
	}

	previewCmd.Flags().StringVar(&packageManager, "package-manager", "pnpm", "Package manager to use (npm|pnpm|yarn)")
	previewCmd.Flags().IntVar(&port, "port", 3000, "Port to run the preview server on")

	// control command
	var (
		host        string
		controlPort int
		proxyPort   int
	)

	controlCmd := &cobra.Command{
		Use:   "control",
		Short: "Run the control plane server",
		Run: func(cmd *cobra.Command, args []string) {
			env := getEnvFromEnvVar()

			// Load environment variables from environment-specific .env file
			envFile := getEnvFile(string(env))
			if err := godotenv.Load(envFile); err != nil {
				log.Printf("Warning: %s file not found, falling back to .env: %v", envFile, err)
				// Fallback to default .env file
				if err := godotenv.Load(); err != nil {
					log.Printf("Warning: .env file not found: %v", err)
				}
			}

			// Parse package manager
			pm, err := runtime.ParsePackageManager(packageManager)
			if err != nil {
				fmt.Println(err)
				os.Exit(1)
			}

			// Get WORKSPACE_PATH from environment
			workspacePath := os.Getenv("WORKSPACE_PATH")
			if workspacePath == "" {
				log.Fatal("WORKSPACE_PATH environment variable must be set")
			}

			// Create workspace directory if it doesn't exist
			if err := os.MkdirAll(workspacePath, 0755); err != nil {
				log.Fatalf("Failed to create workspace directory: %v", err)
			}

			// Initialize the control plane server
			controlServer := api.NewControlPlaneServer(controlPort, proxyPort, pm, workspacePath)

			// Start the control plane server
			log.Printf("Starting control plane server on %s:%d", host, controlPort)
			log.Printf("Using workspace path: %s", workspacePath)
			if err := http.ListenAndServe(fmt.Sprintf("%s:%d", host, controlPort), controlServer.Routes()); err != nil {
				log.Fatalf("Control plane server error: %v", err)
			}
		},
	}

	controlCmd.Flags().StringVar(&host, "host", "127.0.0.1", "Host to run the control plane on")
	controlCmd.Flags().IntVar(&controlPort, "port", 8088, "Port to run the control plane on")
	controlCmd.Flags().IntVar(&proxyPort, "proxy-port", 3000, "Port to run the proxy server on")
	controlCmd.Flags().StringVar(&packageManager, "package-manager", "pnpm", "Package manager to use (npm|pnpm|yarn)")

	rootCmd.AddCommand(previewCmd, controlCmd)

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
