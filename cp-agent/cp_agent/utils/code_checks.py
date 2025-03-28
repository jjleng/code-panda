from typing import List, Tuple

from loguru import logger

from cp_agent.utils.runner_client import (
    BuildErrorResponseBody,
    LintResponseBody,
    RunnerClient,
)

from cp_agent.config import settings


async def perform_code_checks(
    project_id: str,
    runner: RunnerClient,
    skip_lint: bool = settings.SKIP_LINT_BY_DEFAULT,
) -> Tuple[bool, List[str]]:
    """Perform build error checks and optionally linting on the codebase.

    Args:
        project_id: ID of the project to check
        runner: RunnerClient instance to use for checks
        skip_lint: If True, skip linting and only perform build error checks

    Returns:
        Tuple of (has_errors: bool, messages: List[str]) where has_errors is True if
        there were any build errors or lint errors found
    """
    check_results = []
    has_errors = False

    # Check for runtime/build errors first as they're more critical
    error_result = await runner.check_errors(project_id)
    if isinstance(error_result, BuildErrorResponseBody):
        check_results.append(
            f"[Build Error Check]\n{error_result.message or 'No errors found'}"
        )
        has_errors = has_errors or error_result.build_errors

    logger.debug(f"Build error check result for project {project_id}: {error_result}")

    # Run linting only if not skipped
    if not skip_lint:
        lint_result = await runner.lint_project(project_id)
        if isinstance(lint_result, LintResponseBody):
            check_results.append(
                f"[Linting Result]\n{lint_result.message or 'No linting issues found'}"
            )
            has_errors = has_errors or lint_result.lint_errors
        logger.debug(f"Linting result for project {project_id}: {lint_result}")

    return has_errors, check_results
