from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    input: str = Field(min_length=1, max_length=20_000)
    mode: str | None = None  # engineer|team
    roles: list[str] | None = None
    project_id: str | None = None
    user_rules: list[str] | None = None


class RunPublic(BaseModel):
    id: str
    status: str
    mode: str | None = None
    roles: list[str] | None = None
    project_id: str | None = None
    input: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class RunDetail(RunPublic):
    output_text: str | None = None
    error: str | None = None


class RunList(BaseModel):
    runs: list[RunPublic]


class RunEventPublic(BaseModel):
    seq: int
    type: str
    message: str
    data: dict | None = None
    created_at: datetime


class RunEvents(BaseModel):
    events: list[RunEventPublic]


class ArtifactPublic(BaseModel):
    id: str
    name: str
    mime_type: str
    created_at: datetime


class RunArtifacts(BaseModel):
    artifacts: list[ArtifactPublic]


class ArtifactDetail(ArtifactPublic):
    content_json: dict | None = None
    content_text: str | None = None


class RunCheckpointPublic(BaseModel):
    seq: int
    node: str
    state: dict
    created_at: datetime


class RunCheckpoints(BaseModel):
    checkpoints: list[RunCheckpointPublic]
