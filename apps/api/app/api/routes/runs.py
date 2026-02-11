from __future__ import annotations

import json
import re
import io
import time
import zipfile
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.run import Run
from app.db.models.run_artifact import RunArtifact
from app.db.models.run_checkpoint import RunCheckpoint
from app.db.models.run_event import RunEvent
from app.db.models.user import User
from app.db.session import SessionLocal, get_db
from app.langgraph.executor import execute_run
from app.schemas.runs import (
    ArtifactDetail,
    CreateRunRequest,
    RunArtifacts,
    RunCheckpointPublic,
    RunCheckpoints,
    RunDetail,
    RunEvents,
    RunList,
    RunPublic,
)
from app.services.run_service import RunService

router = APIRouter()

ALLOWED_RUN_MODES = {"engineer", "team"}
_FILENAME_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")
_TERMINAL_STATUSES = {"succeeded", "failed", "canceled"}


def _run_public(r: Run) -> RunPublic:
    return RunPublic(
        id=str(r.id),
        status=r.status,
        mode=r.mode,
        roles=r.roles,
        project_id=str(r.project_id) if r.project_id else None,
        input=r.input,
        created_at=r.created_at,
        started_at=r.started_at,
        finished_at=r.finished_at,
    )


def _assert_owner(run: Run, user: User) -> None:
    if run.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("", response_model=RunDetail, status_code=201)
def create_run(
    payload: CreateRunRequest,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RunDetail:
    svc = RunService()
    mode = (payload.mode or "engineer").strip().lower()
    if mode not in ALLOWED_RUN_MODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode '{mode}'. Allowed: {sorted(ALLOWED_RUN_MODES)}",
        )

    project_id: UUID | None = None
    if payload.project_id:
        try:
            project_id = UUID(payload.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id") from None

    run = svc.create_run(
        db,
        user_id=user.id,
        input_text=payload.input,
        mode=mode,
        roles=payload.roles,
        project_id=project_id,
        user_rules=payload.user_rules,
    )
    # Commit before queuing the background task so the task can read the Run in a new DB session.
    db.commit()
    bg.add_task(execute_run, run.id)
    return RunDetail(**_run_public(run).model_dump(), output_text=run.output_text, error=run.error)


@router.post("/{run_id}/rerun", response_model=RunDetail, status_code=201)
def rerun_from_checkpoint(
    run_id: UUID,
    *,
    node: str | None = None,
    checkpoint_seq: int | None = None,
    goto: str | None = None,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RunDetail:
    """Create a new run seeded from a previous run checkpoint."""

    src = db.get(Run, run_id)
    if not src:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(src, user)

    cp: RunCheckpoint | None = None
    if checkpoint_seq is not None:
        cp = (
            db.execute(
                select(RunCheckpoint).where(
                    RunCheckpoint.run_id == run_id, RunCheckpoint.seq == checkpoint_seq
                )
            )
            .scalars()
            .first()
        )
    elif node:
        cp = (
            db.execute(
                select(RunCheckpoint)
                .where(RunCheckpoint.run_id == run_id, RunCheckpoint.node == node)
                .order_by(RunCheckpoint.seq.desc())
            )
            .scalars()
            .first()
        )
    else:
        cp = (
            db.execute(
                select(RunCheckpoint)
                .where(RunCheckpoint.run_id == run_id)
                .order_by(RunCheckpoint.seq.desc())
            )
            .scalars()
            .first()
        )

    if not cp:
        raise HTTPException(status_code=400, detail="No checkpoint found to rerun from")

    seed_state = cp.state if isinstance(cp.state, dict) else {}
    seed_goto = (goto or node or cp.node or "").strip()
    if not seed_goto:
        raise HTTPException(status_code=400, detail="Invalid goto/node")

    svc = RunService()
    new_run = svc.create_run(
        db,
        user_id=user.id,
        input_text=src.input,
        mode=(src.mode or "engineer"),
        roles=src.roles,
        project_id=src.project_id,
        user_rules=src.user_rules,
        parent_run_id=src.id,
        seed_state=seed_state,
        seed_goto=seed_goto,
    )
    svc.add_event(
        db,
        new_run.id,
        type="run.seeded",
        message="Seeded from checkpoint",
        data={"parent_run_id": str(src.id), "checkpoint_seq": cp.seq, "checkpoint_node": cp.node, "goto": seed_goto},
    )
    db.commit()
    bg.add_task(execute_run, new_run.id)
    return RunDetail(**_run_public(new_run).model_dump(), output_text=new_run.output_text, error=new_run.error)


@router.get("", response_model=RunList)
def list_runs(
    project_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RunList:
    stmt = select(Run).where(Run.user_id == user.id)
    if project_id:
        try:
            pid = UUID(project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id") from None
        stmt = stmt.where(Run.project_id == pid)
    stmt = stmt.order_by(Run.created_at.desc())
    runs = db.execute(stmt).scalars().all()
    return RunList(runs=[_run_public(r) for r in runs])


@router.get("/{run_id}", response_model=RunDetail)
def get_run(run_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> RunDetail:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)
    return RunDetail(**_run_public(run).model_dump(), output_text=run.output_text, error=run.error)


@router.get("/{run_id}/events", response_model=RunEvents)
def get_events(run_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> RunEvents:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)
    stmt = select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.seq.asc())
    events = db.execute(stmt).scalars().all()
    return RunEvents(
        events=[
            {
                "seq": e.seq,
                "type": e.type,
                "message": e.message,
                "data": e.data,
                "created_at": e.created_at,
            }
            for e in events
        ]
    )


@router.get("/{run_id}/checkpoints", response_model=RunCheckpoints)
def get_checkpoints(
    run_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> RunCheckpoints:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)
    stmt = select(RunCheckpoint).where(RunCheckpoint.run_id == run_id).order_by(RunCheckpoint.seq.asc())
    cps = db.execute(stmt).scalars().all()
    return RunCheckpoints(
        checkpoints=[
            RunCheckpointPublic(seq=c.seq, node=c.node, state=c.state, created_at=c.created_at) for c in cps
        ]
    )


@router.get("/{run_id}/artifacts", response_model=RunArtifacts)
def get_artifacts(
    run_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> RunArtifacts:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)
    stmt = select(RunArtifact).where(RunArtifact.run_id == run_id).order_by(RunArtifact.created_at.asc())
    arts = db.execute(stmt).scalars().all()
    return RunArtifacts(
        artifacts=[
            {
                "id": str(a.id),
                "name": a.name,
                "mime_type": a.mime_type,
                "created_at": a.created_at,
            }
            for a in arts
        ]
    )


@router.get("/{run_id}/artifacts/{artifact_id}", response_model=ArtifactDetail)
def get_artifact(
    run_id: UUID,
    artifact_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ArtifactDetail:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)

    art = db.get(RunArtifact, artifact_id)
    if not art or art.run_id != run_id:
        raise HTTPException(status_code=404, detail="Not found")

    return ArtifactDetail(
        id=str(art.id),
        name=art.name,
        mime_type=art.mime_type,
        created_at=art.created_at,
        content_json=art.content_json,
        content_text=art.content_text,
    )


@router.get("/{run_id}/artifacts/{artifact_id}/download")
def download_artifact(
    run_id: UUID,
    artifact_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)

    art = db.get(RunArtifact, artifact_id)
    if not art or art.run_id != run_id:
        raise HTTPException(status_code=404, detail="Not found")

    filename = _FILENAME_SAFE.sub("_", art.name or "artifact")
    if not filename:
        filename = "artifact"

    if art.content_text is not None:
        body = art.content_text.encode("utf-8")
    elif art.content_json is not None:
        body = json.dumps(art.content_json, ensure_ascii=False, indent=2).encode("utf-8")
        if not filename.endswith(".json") and art.mime_type == "application/json":
            filename += ".json"
    else:
        body = b""

    return Response(
        content=body,
        media_type=art.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{run_id}/workspace.zip")
def download_workspace_zip(
    run_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download a zip archive containing all run artifacts as files."""

    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)

    stmt = select(RunArtifact).where(RunArtifact.run_id == run_id).order_by(RunArtifact.created_at.asc())
    arts = db.execute(stmt).scalars().all()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for a in arts:
            name = (a.name or "").strip().replace("\\", "/").lstrip("/")
            if not name:
                continue
            if a.content_text is not None:
                zf.writestr(name, a.content_text)
            elif a.content_json is not None:
                zf.writestr(name, json.dumps(a.content_json, ensure_ascii=False, indent=2))
            else:
                zf.writestr(name, "")

        # Helpful metadata for local run reproduction.
        zf.writestr(
            "run_meta.json",
            json.dumps(
                {
                    "id": str(run.id),
                    "status": run.status,
                    "mode": run.mode,
                    "roles": run.roles,
                    "project_id": str(run.project_id) if run.project_id else None,
                    "input": run.input,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

    body = buf.getvalue()
    filename = f"run-{run_id}.zip"
    return Response(
        content=body,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'},
    )


@router.get("/{run_id}/stream")
def stream_events(
    run_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream run events via Server-Sent Events (SSE).

    This is intentionally simple: it tails the DB in a loop and emits new events.
    """

    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)

    def sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    terminal = _TERMINAL_STATUSES

    def gen():
        last_seq = 0
        idle = 0
        while True:
            with SessionLocal() as sdb:
                stmt = (
                    select(RunEvent)
                    .where(RunEvent.run_id == run_id, RunEvent.seq > last_seq)
                    .order_by(RunEvent.seq.asc())
                )
                events = sdb.execute(stmt).scalars().all()
                for e in events:
                    last_seq = e.seq
                    idle = 0
                    yield sse(
                        "run_event",
                        {
                            "seq": e.seq,
                            "type": e.type,
                            "message": e.message,
                            "data": e.data,
                            "created_at": e.created_at.isoformat(),
                        },
                    )

                r = sdb.get(Run, run_id)
                if r and r.status in terminal:
                    yield sse("done", {"status": r.status})
                    break

            if idle % 10 == 0:
                # Keep connection alive through proxies.
                yield ": ping\n\n"
            idle += 1
            time.sleep(0.5)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{run_id}/cancel", response_model=RunDetail)
def cancel_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RunDetail:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)
    if run.status in _TERMINAL_STATUSES:
        return RunDetail(**_run_public(run).model_dump(), output_text=run.output_text, error=run.error)
    svc = RunService()
    svc.set_status(db, run, "canceled")
    svc.add_event(db, run_id, type="run.canceled.requested", message="Cancel requested", data={})
    db.commit()
    return RunDetail(**_run_public(run).model_dump(), output_text=run.output_text, error=run.error)


@router.post("/{run_id}/pause", response_model=RunDetail)
def pause_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RunDetail:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)
    if run.status in _TERMINAL_STATUSES:
        return RunDetail(**_run_public(run).model_dump(), output_text=run.output_text, error=run.error)
    if run.status != "running":
        raise HTTPException(status_code=400, detail="Run is not running")
    svc = RunService()
    run.status = "paused"
    svc.add_event(db, run_id, type="run.pause.requested", message="Pause requested", data={})
    db.add(run)
    db.commit()
    return RunDetail(**_run_public(run).model_dump(), output_text=run.output_text, error=run.error)


@router.post("/{run_id}/resume", response_model=RunDetail)
def resume_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RunDetail:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    _assert_owner(run, user)
    if run.status in _TERMINAL_STATUSES:
        return RunDetail(**_run_public(run).model_dump(), output_text=run.output_text, error=run.error)
    if run.status != "paused":
        raise HTTPException(status_code=400, detail="Run is not paused")
    svc = RunService()
    run.status = "running"
    svc.add_event(db, run_id, type="run.resume.requested", message="Resume requested", data={})
    db.add(run)
    db.commit()
    return RunDetail(**_run_public(run).model_dump(), output_text=run.output_text, error=run.error)
