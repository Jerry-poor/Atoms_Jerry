from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.project import Project
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.projects import CreateProjectRequest, ProjectList, ProjectPublic

router = APIRouter()


def _project_public(p: Project) -> ProjectPublic:
    return ProjectPublic(id=str(p.id), name=p.name, created_at=p.created_at)


def _default_name() -> str:
    ts = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M")
    return f"新项目 {ts}"


@router.get("", response_model=ProjectList)
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProjectList:
    stmt = select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc())
    projects = db.execute(stmt).scalars().all()
    return ProjectList(projects=[_project_public(p) for p in projects])


@router.post("", response_model=ProjectPublic, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectPublic:
    name = (payload.name or "").strip() or _default_name()
    proj = Project(user_id=user.id, name=name)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return _project_public(proj)

