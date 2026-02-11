from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class ProjectPublic(BaseModel):
    id: str
    name: str
    created_at: datetime


class ProjectList(BaseModel):
    projects: list[ProjectPublic]

