"""Utilities for managing project dependencies using the runner client."""

from pathlib import Path

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from cp_agent.utils.runner_client import AddPackageResponseBody, RunnerClient


def format_output(stdout: bytes, stderr: bytes) -> str:
    """Format command output for display.

    Args:
        stdout: Raw stdout bytes from subprocess
        stderr: Raw stderr bytes from subprocess

    Returns:
        Formatted string combining stdout and stderr
    """
    output = []

    if stdout:
        stdout_str = stdout.decode().strip()
        if stdout_str:
            output.append("Output:")
            output.append(stdout_str)

    if stderr:
        stderr_str = stderr.decode().strip()
        if stderr_str:
            output.append("Errors:" if output else "Error output:")
            output.append(stderr_str)

    return "\n".join(output) if output else "No output from command"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)
async def add_dependency(
    project_root: str, name: str, restart_runner: bool = True
) -> str:
    """Add package dependency using the runner client.
    Will retry up to 3 times with exponential backoff if installation fails.

    Args:
        project_root: The root directory of the project containing config files
        name: Name of the package to add
        restart_runner: Whether to restart the runner server after adding the package

    Returns:
        str: Response message from the package installation

    Raises:
        FileNotFoundError: If no package.json or pyproject.toml found
        RuntimeError: If package installation fails after retries
    """
    logger.info(f"Adding dependency {name} to project at: {project_root}")
    # Look for package.json or pyproject.toml
    package_json = Path(project_root) / "package.json"
    pyproject_toml = Path(project_root) / "pyproject.toml"

    if not (package_json.exists() or pyproject_toml.exists()):
        raise FileNotFoundError(
            "No package.json or pyproject.toml found in the project"
        )

    runner_client = RunnerClient()
    project_id = Path(project_root).name
    response = await runner_client.add_package(
        project_id, name, restart_server=restart_runner
    )

    if isinstance(response, AddPackageResponseBody):
        return f"Successfully added {name} using runner client"

    raise RuntimeError(f"Failed to add dependency: {response}")
