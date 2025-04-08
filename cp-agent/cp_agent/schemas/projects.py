"""Project API schemas."""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Project creation request schema."""

    project_id: str = Field(description="Unique identifier for the project")
    name: Optional[str] = Field(
        default=None, description="Project name, defaults to shortened project_id"
    )


class GenerateSummaryRequest(BaseModel):
    """Request model for generating project summary."""

    message: str = Field(
        ...,
        description="User message to analyze for generating project name and description",
    )


class GenerateSummaryResponse(BaseModel):
    """Response model for generated project summary."""

    name: str = Field(..., description="Generated project name")
    description: str = Field(..., description="Generated project description")


class MigrationRequest(BaseModel):
    """Request model for SQL migration execution."""

    sql: str
    name: Optional[str] = None


class MigrationResponse(BaseModel):
    """Response model for SQL migration execution."""

    name: str = Field(..., description="Name of the migration")
    success: bool = Field(..., description="Whether the migration was successful")
    timestamp: datetime = Field(..., description="When the migration was executed")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ListProjectPathsResponse(BaseModel):
    """Response model for listing project paths."""

    paths: List[str]


class SwitchCommitRequest(BaseModel):
    """Request model for switching git commit."""

    commit_hash: str = Field(..., description="The git commit hash to switch to")


class SwitchCommitResponse(BaseModel):
    """Response model for switching git commit."""

    message: str = Field(..., description="Success or error message")
    success: bool = Field(..., description="Whether the switch was successful")
