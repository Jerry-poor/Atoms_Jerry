from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.run import Run
from app.db.models.run_artifact import RunArtifact
from app.db.models.run_checkpoint import RunCheckpoint
from app.db.models.run_event import RunEvent

UNKNOWN_TABLE_KIND_ERROR = "unknown table kind"


def _now() -> datetime:
    return datetime.now(tz=UTC)


class RunService:
    def create_run(
        self,
        db: Session,
        user_id: UUID,
        *,
        input_text: str,
        mode: str = "engineer",
        roles: list[str] | None = None,
        project_id: UUID | None = None,
        user_rules: list[str] | None = None,
        parent_run_id: UUID | None = None,
        seed_state: dict | None = None,
        seed_goto: str | None = None,
    ) -> Run:
        run = Run(
            user_id=user_id,
            project_id=project_id,
            status="queued",
            mode=mode,
            roles=roles,
            user_rules=user_rules,
            parent_run_id=parent_run_id,
            seed_state=seed_state,
            seed_goto=seed_goto,
            input=input_text,
        )
        db.add(run)
        db.flush()
        self.add_event(db, run.id, type="run.created", message="Run created", data={})
        return run

    def set_status(self, db: Session, run: Run, status: str) -> None:
        run.status = status
        if status == "running" and run.started_at is None:
            run.started_at = _now()
        if status in {"succeeded", "failed", "canceled"}:
            run.finished_at = _now()
        db.add(run)

    def next_seq(self, db: Session, run_id: UUID, table: str) -> int:
        if table == "events":
            stmt = select(func.coalesce(func.max(RunEvent.seq), 0) + 1).where(RunEvent.run_id == run_id)
        elif table == "checkpoints":
            stmt = (
                select(func.coalesce(func.max(RunCheckpoint.seq), 0) + 1)
                .where(RunCheckpoint.run_id == run_id)
            )
        else:
            raise ValueError(UNKNOWN_TABLE_KIND_ERROR)
        return int(db.execute(stmt).scalar_one())

    def add_event(
        self, db: Session, run_id: UUID, *, type: str, message: str, data: dict | None
    ) -> RunEvent:
        seq = self.next_seq(db, run_id, "events")
        ev = RunEvent(run_id=run_id, seq=seq, type=type, message=message, data=data)
        db.add(ev)
        db.flush()
        return ev

    def add_checkpoint(self, db: Session, run_id: UUID, *, node: str, state: dict) -> RunCheckpoint:
        seq = self.next_seq(db, run_id, "checkpoints")
        cp = RunCheckpoint(run_id=run_id, seq=seq, node=node, state=state)
        db.add(cp)
        db.flush()
        return cp

    def add_artifact(
        self,
        db: Session,
        run_id: UUID,
        *,
        name: str,
        mime_type: str,
        content_json: dict | None = None,
        content_text: str | None = None,
    ) -> RunArtifact:
        art = RunArtifact(
            run_id=run_id,
            name=name,
            mime_type=mime_type,
            content_json=content_json,
            content_text=content_text,
        )
        db.add(art)
        db.flush()
        return art
