from datetime import datetime
from typing import Optional, TypedDict


class Project(TypedDict, total=False):
    id: str
    name: str
    description: Optional[str]
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class Database(TypedDict):
    projects: Project
