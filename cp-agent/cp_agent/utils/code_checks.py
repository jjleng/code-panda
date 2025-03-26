from typing import List, Tuple

from loguru import logger

from cp_agent.utils.runner_client import (
    BuildErrorResponseBody,
    LintResponseBody,
    RunnerClient,
)


async def perform_code_checks(
    project_id: str, runner: RunnerClient
) -> Tuple[bool, List[str]]:
    """Perform linting and runtime error checks on the codebase.

    Args:
        project_id: ID of the project to check
        runner: RunnerClient instance to use for checks

    Returns:
        Tuple of (has_errors: bool, messages: List[str]) where has_errors is True if
        there were any lint errors or build errors found
    """
    check_results = []
    has_errors = False

    # Run linting
    lint_result = await runner.lint_project(project_id)
    if isinstance(lint_result, LintResponseBody):
        check_results.append(f"[Linting Result]\n{lint_result.message}")
        has_errors = has_errors or lint_result.lint_errors
    logger.debug(f"Linting result for project {project_id}: {lint_result}")

    # Check for runtime errors
    error_result = await runner.check_errors(project_id)
    if isinstance(error_result, BuildErrorResponseBody):
        check_results.append(f"[Build Error Check]\n{error_result.message}")
        has_errors = has_errors or error_result.build_errors

    logger.debug(f"Build error check result for project {project_id}: {error_result}")

    return has_errors, check_results
