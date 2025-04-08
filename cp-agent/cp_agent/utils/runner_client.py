"""Client for interacting with cp-runner API."""

from cp_agent.config import settings
from cp_agent.generated.api.git import (
    switch_commit as switch_commit_api,
)
from cp_agent.generated.api.projects import add_package as add_package_api
from cp_agent.generated.api.projects import check_build_errors
from cp_agent.generated.api.projects import lint_project as lint_project_api
from cp_agent.generated.api.projects import start_project as start_project_api
from cp_agent.generated.client import Client
from cp_agent.generated.models.add_package_request_body import AddPackageRequestBody
from cp_agent.generated.models.add_package_response_body import AddPackageResponseBody
from cp_agent.generated.models.build_error_response_body import BuildErrorResponseBody
from cp_agent.generated.models.error_model import ErrorModel
from cp_agent.generated.models.lint_response_body import LintResponseBody
from cp_agent.generated.models.project_operation_request_body import (
    ProjectOperationRequestBody,
)
from cp_agent.generated.models.project_operation_response_body import (
    ProjectOperationResponseBody,
)
from cp_agent.generated.models.switch_commit_request_body import (
    SwitchCommitRequestBody,
)
from cp_agent.generated.models.switch_commit_response_body import (
    SwitchCommitResponseBody,
)

ResponseType = ErrorModel | ProjectOperationResponseBody
BuildErrorType = ErrorModel | BuildErrorResponseBody
LintResponseType = ErrorModel | LintResponseBody
AddPackageResponseType = ErrorModel | AddPackageResponseBody
SwitchCommitResponseType = ErrorModel | SwitchCommitResponseBody  # Added type alias


class RunnerClient:
    """Client for interacting with cp-runner API."""

    def __init__(self, base_url: str | None = None):
        self.client = Client(base_url=base_url or settings.RUNNER_BASE_URL)

    async def check_errors(self, project_id: str) -> BuildErrorType:
        """Check for runtime errors in the project."""
        try:
            request_body = ProjectOperationRequestBody(project_id=project_id)
            response = await check_build_errors.asyncio(
                client=self.client, body=request_body
            )
            if not response:
                raise RuntimeError("No response received")
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to check errors: {e}")

    async def restart_project(self, project_id: str) -> ResponseType:
        """(Re)Start the project server."""
        try:
            request_body = ProjectOperationRequestBody(project_id=project_id)
            response = await start_project_api.asyncio(
                client=self.client, body=request_body
            )
            if not response:
                raise RuntimeError("No response received")
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to (re)start project: {e}")

    async def lint_project(self, project_id: str) -> LintResponseType:
        """Run linting on the project."""
        try:
            request_body = ProjectOperationRequestBody(project_id=project_id)
            response = await lint_project_api.asyncio(
                client=self.client, body=request_body
            )
            if not response:
                raise RuntimeError("No response received")
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to lint project: {e}")

    async def add_package(
        self, project_id: str, package_name: str, restart_server: bool
    ) -> AddPackageResponseType:
        """Install a package in the project."""
        try:
            request_body = AddPackageRequestBody(
                project_id=project_id,
                package_name=package_name,
                restart_server=restart_server,
            )
            response = await add_package_api.asyncio(
                client=self.client, body=request_body
            )
            if not response:
                raise RuntimeError("No response received")
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to install package: {e}")

    async def switch_commit(
        self, project_id: str, commit_hash: str
    ) -> SwitchCommitResponseType:
        """Switch the project's working directory to a specific commit via the runner."""
        try:
            request_body = SwitchCommitRequestBody(
                project_id=project_id, commit_hash=commit_hash
            )
            response = await switch_commit_api.asyncio(
                client=self.client, body=request_body
            )

            if not response:
                raise RuntimeError("No response received from runner")

            return response
        except Exception as e:
            raise RuntimeError(f"Failed to switch commit for project {project_id}: {e}")
