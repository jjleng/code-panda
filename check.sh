#!/bin/bash

# Function to check cp-agent
check_agent() {
    echo "Checking cp-agent..."
    cd cp-agent
    make format lint test
    local status=$?
    cd ..
    return $status
}

# Function to check cp-webapp
check_webapp() {
    echo "Checking cp-webapp..."
    cd cp-webapp
    pnpm format && pnpm lint
    local status=$?
    cd ..
    return $status
}

# Function to check cp-runner
check_runner() {
    echo "Checking cp-runner..."
    cd cp-runner
    go fmt ./... && go vet ./...
    local status=$?
    cd ..
    return $status
}

# Function to display help
show_help() {
    echo "Usage: ./check.sh [project]"
    echo "Run code checks for the specified project or all projects if none specified."
    echo ""
    echo "Options:"
    echo "  agent   Check only cp-agent (Python)"
    echo "  webapp  Check only cp-webapp (Next.js)"
    echo "  runner  Check only cp-runner (Go)"
    echo "  all     Check all projects (default)"
    echo "  help    Show this help message"
}

# Main execution
case "$1" in
    "agent")
        check_agent
        ;;
    "webapp")
        check_webapp
        ;;
    "runner")
        check_runner
        ;;
    "help")
        show_help
        exit 0
        ;;
    *)
        echo "Checking all projects..."
        check_agent && check_webapp && check_runner
        ;;
esac

status=$?
if [ $status -eq 0 ]; then
    echo "All checks passed! 🎉"
else
    echo "Checks failed with status $status ❌"
fi
exit $status