from __future__ import annotations

import mimetypes
import re
import time
from uuid import UUID

from app.db.models.run import Run
from app.db.session import SessionLocal
from langgraph.types import Command

from app.langgraph.workflow import WORKFLOW, RunState
from app.llm.client import LLM_STREAM_EMITTER
from app.services.run_service import RunService

_NAME_SAFE = re.compile(r"[^a-zA-Z0-9._/ -]+")


def _sanitize_name(name: str) -> str:
    n = (name or "").strip().replace("\\", "/")
    n = n.lstrip("/")
    n = n.replace("..", ".")
    n = _NAME_SAFE.sub("_", n)
    return n[:200] or "file.txt"


def _guess_mime(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    custom = {
        "ts": "text/plain",
        "tsx": "text/plain",
        "js": "text/plain",
        "jsx": "text/plain",
        "py": "text/plain",
        "md": "text/markdown",
        "json": "application/json",
        "html": "text/html",
        "css": "text/css",
        "txt": "text/plain",
    }
    if ext in custom:
        return custom[ext]
    mt, _ = mimetypes.guess_type(filename)
    return mt or "text/plain"

_RE_SECRETS = re.compile(
    r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
)
_RE_SK = re.compile(r"\bsk-[A-Za-z0-9]{16,}\b")
_RE_AZURE = re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b")
_RE_EXEC = re.compile(r"(?i)\b(eval|exec)\s*\(")

_RE_IMPORT_OS = re.compile(r"(?m)^\s*import\s+os\b|^\s*from\s+os\s+import\b")
_RE_FS_WRITE = re.compile(
    r"(?i)\b(open|write_text|write_bytes|mkdir|rmdir|remove|unlink|rename|replace)\b"
)


def _scan_rule_violations(files: list[dict]) -> list[str]:
    violations: list[str] = []
    dep_changes: list[str] = []
    for f in files or []:
        if not isinstance(f, dict):
            continue
        path = str(f.get("path") or "")
        content = str(f.get("content") or "")
        if not content:
            continue
        if _RE_EXEC.search(content):
            violations.append(f"{path}: violates G-001 (eval/exec detected)")
        if _RE_SECRETS.search(content) or _RE_SK.search(content) or _RE_AZURE.search(content):
            violations.append(f"{path}: violates G-003 (possible secret literal)")
        lp = path.lower().replace("\\", "/")
        if lp.endswith("package.json") or lp.endswith("requirements.txt") or lp.endswith("pyproject.toml"):
            dep_changes.append(path)
        # Heuristic for "implicit side effects": direct filesystem writes.
        if lp.endswith(".py") and _RE_IMPORT_OS.search(content) and _RE_FS_WRITE.search(content):
            violations.append(f"{path}: possible implicit side effects (filesystem operations detected)")

    if dep_changes:
        violations.append(
            "Dependency files present in output (review required): " + ", ".join(dep_changes)
        )
    return violations


def execute_run(run_id: UUID) -> None:
    """Execute a run end-to-end.

    This is deterministic unless LLM env vars are configured.
    """

    svc = RunService()
    with SessionLocal() as db:
        run = db.get(Run, run_id)
        if not run:
            return
        input_text = run.input
        mode = (run.mode or "engineer").strip().lower()
        roles = run.roles if isinstance(run.roles, list) else None
        user_rules = run.user_rules if isinstance(run.user_rules, list) else None
        seed_state = run.seed_state if isinstance(run.seed_state, dict) else None
        seed_goto = (run.seed_goto or "").strip() or None

        svc.set_status(db, run, "running")
        svc.add_event(db, run_id, type="run.started", message="Run started", data={})
        db.commit()

    state: RunState = {"run_id": str(run_id), "input": input_text, "mode": mode}
    if roles:
        state["roles"] = roles
    if user_rules:
        state["user_rules"] = user_rules

    initial_input: RunState | Command
    if seed_state and seed_goto:
        # Ensure the new run's identity is used.
        seed_state = dict(seed_state)
        seed_state["run_id"] = str(run_id)
        seed_state["input"] = input_text
        seed_state["mode"] = mode
        if roles:
            seed_state["roles"] = roles
        if user_rules:
            seed_state["user_rules"] = user_rules
        initial_input = Command(update=seed_state, goto=seed_goto)
    else:
        initial_input = state

    seen_outputs: dict[str, str] = {}
    delta_buf: dict[str, str] = {}
    delta_last_flush: dict[str, float] = {}
    paused_emitted = False

    def emit_delta(role: str, delta: str) -> None:
        r = (role or "assistant").strip() or "assistant"
        d = (delta or "")
        if not d:
            return
        delta_buf[r] = (delta_buf.get(r, "") + d)[-50_000:]
        now = time.monotonic()
        last = delta_last_flush.get(r, 0.0)
        if len(delta_buf[r]) < 256 and (now - last) < 0.20:
            return
        chunk = delta_buf[r]
        delta_buf[r] = ""
        delta_last_flush[r] = now
        with SessionLocal() as db:
            svc.add_event(db, run_id, type="agent.delta", message=r, data={"role": r, "delta": chunk})
            db.commit()

    try:
        token = LLM_STREAM_EMITTER.set(emit_delta)
        # Stream node updates so we can checkpoint at each node boundary.
        for update in WORKFLOW.stream(initial_input, stream_mode="updates"):
            # Handle pause/cancel controls between LangGraph node updates.
            while True:
                with SessionLocal() as db:
                    run_ctl = db.get(Run, run_id)
                    if run_ctl and run_ctl.status == "canceled":
                        svc.add_event(db, run_id, type="run.canceled", message="Run canceled", data={})
                        db.commit()
                        return
                    if not run_ctl or run_ctl.status != "paused":
                        if paused_emitted:
                            svc.add_event(db, run_id, type="run.resumed", message="Run resumed", data={})
                            db.commit()
                            paused_emitted = False
                        break
                    if not paused_emitted:
                        svc.add_event(db, run_id, type="run.paused", message="Run paused", data={})
                        db.commit()
                        paused_emitted = True
                time.sleep(0.4)
            if not isinstance(update, dict):
                continue
            for node, node_state in update.items():
                if not isinstance(node_state, dict):
                    continue
                state = node_state  # latest state at this node
                outputs = state.get("outputs")
                if isinstance(outputs, dict):
                    for role, text in outputs.items():
                        if not isinstance(role, str) or not isinstance(text, str):
                            continue
                        prev = seen_outputs.get(role)
                        if prev == text:
                            continue
                        seen_outputs[role] = text
                        with SessionLocal() as db:
                            svc.add_event(
                                db,
                                run_id,
                                type="agent.output",
                                message=role,
                                data={"role": role, "text": text},
                            )
                            db.commit()

                with SessionLocal() as db:
                    svc.add_checkpoint(db, run_id, node=str(node), state=dict(state))
                    svc.add_event(db, run_id, type="checkpoint.saved", message="Checkpoint saved", data={"node": node})
                    svc.add_event(db, run_id, type="node.completed", message=f"{node} completed", data={"node": node})
                    db.commit()

        # Flush remaining deltas, if any.
        for r, chunk in list(delta_buf.items()):
            if not chunk:
                continue
            with SessionLocal() as db:
                svc.add_event(db, run_id, type="agent.delta", message=r, data={"role": r, "delta": chunk})
                db.commit()
        delta_buf.clear()

        final = state.get("final") or {}
        files = []
        if isinstance(state.get("files"), list):
            files = state.get("files") or []
        elif isinstance(final, dict) and isinstance(final.get("files"), list):
            files = final.get("files") or []
        violations = _scan_rule_violations(files)
        if violations:
            with SessionLocal() as db:
                svc.add_event(
                    db,
                    run_id,
                    type="rules.violation",
                    message="global_rules",
                    data={"violations": violations},
                )
                db.commit()

        with SessionLocal() as db:
            run = db.get(Run, run_id)
            if run:
                if run.status == "canceled":
                    svc.add_event(db, run_id, type="run.canceled", message="Run canceled", data={})
                    db.commit()
                    return
                summary = (final.get("summary") or "").strip() or "Run completed"
                if violations:
                    summary = summary + "\n\n[Global rule violations]\n- " + "\n- ".join(violations)
                run.output_text = summary
                # Persist generated files as individual artifacts so the UI can show them as code tabs.
                if files:
                    manifest = []
                    for f in files:
                        if not isinstance(f, dict):
                            continue
                        path = _sanitize_name(str(f.get("path") or ""))
                        content = str(f.get("content") or "")
                        if not path:
                            continue
                        mime = _guess_mime(path)
                        svc.add_artifact(
                            db,
                            run_id,
                            name=path,
                            mime_type=mime,
                            content_text=content,
                        )
                        manifest.append({"path": path, "mime_type": mime, "bytes": len(content.encode("utf-8"))})
                    if manifest:
                        svc.add_artifact(
                            db,
                            run_id,
                            name="files_manifest.json",
                            mime_type="application/json",
                            content_json={"files": manifest},
                        )
                svc.add_artifact(
                    db,
                    run_id,
                    name="final_output.json",
                    mime_type="application/json",
                    content_json=final if isinstance(final, dict) else {"final": final},
                )
                svc.set_status(db, run, "succeeded")
                svc.add_event(db, run_id, type="run.succeeded", message="Run succeeded", data={})
                db.commit()
    except Exception as e:
        try:
            LLM_STREAM_EMITTER.reset(token)  # type: ignore[name-defined]
        except Exception:
            pass
        with SessionLocal() as db:
            run = db.get(Run, run_id)
            if run:
                run.error = str(e)
                svc.set_status(db, run, "failed")
                svc.add_event(db, run_id, type="run.failed", message="Run failed", data={"error": str(e)})
                db.commit()
    else:
        try:
            LLM_STREAM_EMITTER.reset(token)  # type: ignore[name-defined]
        except Exception:
            pass
