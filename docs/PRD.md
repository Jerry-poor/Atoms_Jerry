# PRD: Atoms_Jerry

Build a reproducible full-stack web product that implements the marketing UI described in the provided UI docx + screenshots, plus the mandatory backend multi-agent workflow execution capability (LangGraph) and OAuth (GitHub + Google).

Date reference: UI audit docs describe `atoms.dev` public UI "as of February 2026".

## Inputs (Source Of Truth)

- `docs/UI documentation task.docx` (structured UI: Page IDs, purpose, components, interactions, entry/exit)
- `docs/atoms_ui_audit_report.docx` (screenshots and narrative audit notes)
- `screenshots/` (extracted from the audit report)

## Scope Boundary (Non-Negotiable)

This project has three categories of scope. If these conflict, precedence is:

1. Mandatory requirements (LangGraph + GitHub/Google OAuth + full stack + tests)
2. UI documentation (Page IDs, interactions, labels)
3. Anything else is `UNKNOWN` and must be implemented minimally without inventing new product features

### Documented Scope (From UI Docs)

Public marketing pages and auth UI:

- Page_01_Home (`/`)
- Page_02_Pricing (`/pricing`)
- Page_03_Resources_Dropdown (header dropdown state)
- Page_04_Blog_Home (`/blog`)
- Page_05_Blog_Post (`/blog/[slug]`) (slug/content is `UNKNOWN`)
- Page_06_Use_Cases (`/use-cases`)
- Page_07_Use_Cases_App (`/use-cases/app`) (`UNKNOWN` if separate route vs state)
- Page_08_Videos (`/videos`)
- Page_09_Affiliate (`/affiliate`)
- Page_10_Explorer_Program (`/explorer-program`)
- Page_11_Help_Center (`/help-center`)
- Page_12_404 (Next.js not-found)
- Page_13_Login (`/login`)
- Page_14_SignUp (`/signup`)

Auth elements explicitly shown in UI docs:

- Google OAuth button on Login and Sign Up pages
- Email/password login fields on Login page
- Username/email/password/confirm fields on Sign Up page
- Links for password reset and Terms/Privacy (flows/content are `UNKNOWN`)

### Mandatory Scope (Not In UI Docs)

To satisfy hard requirements, we must add a minimal authenticated "App" area that exposes:

- A way to create a generic workflow “run”
- Run listing and details (status, logs/events, results/artifacts)
- Backend orchestration implemented using LangGraph
- Persistence in Postgres for run metadata, checkpoints/state snapshots, events, artifacts

This is a mandatory addition and must not introduce domain-specific business logic beyond “Run pipeline”.

### DOC CONFLICTS / GAPS

- DOC CONFLICT: UI docs show Google OAuth but do not mention GitHub OAuth. GitHub OAuth must be added.
- UNKNOWN: Password reset process is referenced but not specified (no Page ID, no flow details).
- UNKNOWN: Terms of Service and Privacy Policy pages/content are referenced but not specified.
- UNKNOWN: Blog content, slugs, and article data source are not specified.
- UNKNOWN: Any post-login product UI beyond authentication is not specified.

## Personas & Roles

- Public visitor: can view marketing pages.
- Authenticated user: can access protected app pages (minimal Runs area).

Authorization model (minimal):

- No roles beyond “authenticated” are required by the docs; implement single-role access control.

## Features & Modules

### Marketing Site (Documented)

- Shared layout: Header (logo + nav + resources dropdown) and Footer
- Pages per `docs/UI_MAP.md` with the visible components and interactions defined in the tables
- Navigation must match expected outcomes in UI_MAP interaction tables

Content fidelity rule:

- Text/labels explicitly stated in UI docs must match.
- Content not specified in docs is `UNKNOWN`; implement minimal placeholders without implying additional product capabilities.

### Authentication (Documented + Mandatory)

Required login mechanisms:

- OAuth: Google and GitHub
- Local: email/password login + email/password signup (because fields + submit actions are explicitly present)

Required auth behaviors:

- After OAuth login/signup, create or update a local user record in Postgres
- Support logout
- Protect only the “App/Runs” area by default (marketing remains public)

Test harness (mandatory for deterministic E2E):

- When `TEST_MODE=true`, provide a fake OAuth flow that simulates GitHub and Google users (not available in production mode).

### Workflow Runs (Mandatory Minimal Addition)

Provide a generic “Run pipeline” feature (no domain-specific logic):

- Create a run with a user-provided prompt/task string
- Execute a multi-agent workflow using LangGraph
- Persist run state snapshots/checkpoints, events timeline, and artifacts in Postgres
- Provide API endpoints for run lifecycle and front-end pages to list/view runs

## Page / Route Mapping

Documented pages are mapped in `docs/UI_MAP.md`.

Mandatory addition (not in UI docs):

- `/app` (redirect to `/app/runs`) (protected)
- `/app/runs` (protected): list runs + “Create run” UI
- `/app/runs/[id]` (protected): run details: status, events timeline, artifacts

## User Flows

### Pre-Login (Documented)

1. User lands on `/`
2. User navigates via header/footer to pricing/resources/blog/use-cases/videos/affiliate/explorer/help
3. User clicks Log in or Sign up

### Signup / Login (Documented + Mandatory)

Signup:

1. `/signup`
2. Either: OAuth signup (Google documented; GitHub mandatory addition) OR submit username/email/password/confirm
3. On success: user becomes authenticated and is redirected to the post-login entry route (`/app`) (UI docs say “dashboard”, but dashboard UI is `UNKNOWN`)

Login:

1. `/login`
2. Either: OAuth login (Google documented; GitHub mandatory addition) OR submit email/password
3. On success: redirect to `/app`

Logout:

1. User clicks Logout from protected area header/menu
2. Session is invalidated; redirect to `/`

### Post-Login (Mandatory Minimal Addition; UI is `UNKNOWN`)

1. Visit `/app/runs`
2. Create a run by entering a prompt and submitting
3. Observe status changes and events timeline
4. Open run detail page and view artifacts/output

## Technical Architecture

### Monorepo Layout (Required)

- `apps/web`: Next.js (React + TS), TailwindCSS, shadcn/ui, TanStack Query, Zod
- `apps/api`: FastAPI, SQLAlchemy 2.x, Alembic, LangGraph, Pydantic
- `packages/shared`: shared schemas/types (Zod + Pydantic parity) as needed

### High-Level System Diagram

```mermaid
flowchart LR
  browser[Browser] --> web[Next.js Web (apps/web)]
  web --> api[FastAPI API (apps/api)]
  api --> db[(PostgreSQL)]
  worker[Worker Process\n(LangGraph runner)] --> db
  api --> workerQueue[(DB-backed run queue)]
```

Notes:

- Local dev uses docker-compose for Postgres.
- API and worker run using the conda environment `Atoms_Jerry`.

### Backend Clean Architecture Boundaries (Target)

Inside `apps/api`, use layered boundaries:

- `app/api`: FastAPI routers (HTTP layer)
- `app/schemas`: Pydantic DTOs (request/response)
- `app/domain`: core types/enums (RunStatus, Provider, etc.)
- `app/services`: business logic (auth, runs, orchestration)
- `app/db`: SQLAlchemy models + session management + migrations
- `app/langgraph`: workflow graph definition and runner utilities

## Data Model (Draft)

All tables live in Postgres and are created via Alembic migrations.

### users

- `id` (uuid, pk)
- `email` (text, unique, nullable; required for local auth; OAuth providers may supply)
- `username` (text, unique, nullable; required by signup form in UI docs)
- `password_hash` (text, nullable)
- `created_at` (timestamptz)
- `updated_at` (timestamptz)

### oauth_accounts

- `id` (uuid, pk)
- `user_id` (uuid, fk -> users.id, not null)
- `provider` (text enum: `google`, `github`)
- `provider_account_id` (text, not null)
- `provider_email` (text, nullable)
- `created_at` (timestamptz)
- unique constraint on (`provider`, `provider_account_id`)

### sessions (DB-backed cookie session)

- `id` (uuid, pk)
- `user_id` (uuid, fk -> users.id, not null)
- `created_at` (timestamptz)
- `expires_at` (timestamptz)
- `revoked_at` (timestamptz, nullable)
- index on (`user_id`, `expires_at`)

### runs

- `id` (uuid, pk)
- `user_id` (uuid, fk -> users.id, not null)
- `status` (text enum: `queued`, `running`, `succeeded`, `failed`, `canceled`)
- `input` (text, not null)
- `output_text` (text, nullable)
- `error` (text, nullable)
- `created_at` (timestamptz)
- `started_at` (timestamptz, nullable)
- `finished_at` (timestamptz, nullable)

### run_events (timeline / logs)

- `id` (uuid, pk)
- `run_id` (uuid, fk -> runs.id, not null)
- `seq` (int, monotonic per run)
- `type` (text; e.g. `run.created`, `node.started`, `node.completed`, `checkpoint.saved`, `error`)
- `message` (text)
- `data` (jsonb, nullable)
- `created_at` (timestamptz)
- unique constraint on (`run_id`, `seq`)

### run_checkpoints (state snapshots)

- `id` (uuid, pk)
- `run_id` (uuid, fk -> runs.id, not null)
- `seq` (int, monotonic per run)
- `node` (text)
- `state` (jsonb) (full serialized workflow state)
- `created_at` (timestamptz)
- unique constraint on (`run_id`, `seq`)

### run_artifacts

- `id` (uuid, pk)
- `run_id` (uuid, fk -> runs.id, not null)
- `name` (text) (e.g. `final_output.json`)
- `mime_type` (text)
- `content` (bytea or text/jsonb; choose one and document in implementation)
- `created_at` (timestamptz)

## API Contract (Draft)

API base: `/api`

Auth:

- `GET /api/auth/oauth/{provider}/start`
- `GET /api/auth/oauth/{provider}/callback`
- `POST /api/auth/login` (email/password)
- `POST /api/auth/signup` (username/email/password)
- `POST /api/auth/logout`
- `GET /api/auth/me`

Runs (mandatory endpoints):

- `POST /api/runs` (create run)
- `GET /api/runs` (list runs)
- `GET /api/runs/{id}` (run details)
- `GET /api/runs/{id}/events` (timeline/logs)
- `GET /api/runs/{id}/artifacts` (outputs)

Errors (standard):

- `401 Unauthorized` (missing/invalid session)
- `403 Forbidden` (resource not owned by user)
- `404 Not Found`
- `422 Unprocessable Entity` (validation)
- `500 Internal Server Error` (unexpected)

### JSON Shapes (Examples)

Unless otherwise specified, responses are JSON and may include `Set-Cookie` headers for session management.

Error shape (example):

```json
{
  "detail": "Unauthorized",
  "code": "auth_unauthorized"
}
```

`POST /api/auth/signup`

Request:

```json
{
  "username": "jerry",
  "email": "jerry@example.com",
  "password": "correct horse battery staple"
}
```

Response (200):

```json
{
  "user": {
    "id": "uuid",
    "email": "jerry@example.com",
    "username": "jerry"
  }
}
```

`POST /api/auth/login`

Request:

```json
{
  "email": "jerry@example.com",
  "password": "correct horse battery staple"
}
```

Response (200): same as signup response.

`GET /api/auth/me`

Response (200):

```json
{
  "user": {
    "id": "uuid",
    "email": "jerry@example.com",
    "username": "jerry"
  }
}
```

`POST /api/runs`

Request:

```json
{
  "input": "Create a brief plan and a short summary."
}
```

Response (201):

```json
{
  "run": {
    "id": "uuid",
    "status": "queued",
    "input": "Create a brief plan and a short summary.",
    "created_at": "2026-02-09T00:00:00Z"
  }
}
```

`GET /api/runs/{id}`

Response (200):

```json
{
  "run": {
    "id": "uuid",
    "status": "succeeded",
    "input": "Create a brief plan and a short summary.",
    "output_text": "final text output (optional)",
    "error": null
  }
}
```

`GET /api/runs/{id}/events`

Response (200):

```json
{
  "events": [
    {
      "seq": 1,
      "type": "run.created",
      "message": "Run created",
      "data": {},
      "created_at": "2026-02-09T00:00:00Z"
    }
  ]
}
```

`GET /api/runs/{id}/artifacts`

Response (200):

```json
{
  "artifacts": [
    {
      "id": "uuid",
      "name": "final_output.json",
      "mime_type": "application/json"
    }
  ]
}
```

This contract will be fully specified in `docs/API_CONTRACT.md` in Step 2, and must remain consistent with the OpenAPI schema exposed by FastAPI.

## Auth Model (Detailed)

### Strategy

Use a DB-backed session cookie:

- API sets `atoms_session` httpOnly cookie containing a session UUID
- Each authenticated request loads session from DB and resolves `current_user`
- Logout revokes session and clears cookie

Rationale:

- Deterministic and easy to revoke for logout
- Works well with OAuth callbacks (redirect + set cookie)
- Simplifies E2E test harness (can set session via test-only endpoints)

### OAuth Providers

Providers: Google and GitHub.

Implementation requirements:

- Use OAuth2 authorization code flow
- On callback, fetch provider profile:
  - stable provider user id
  - email when available
- Upsert local `users` and `oauth_accounts`
- Create session and redirect to `WEB_APP_URL/app`

Callback URLs (local dev):

- `http://localhost:8000/api/auth/oauth/google/callback`
- `http://localhost:8000/api/auth/oauth/github/callback`

### Local Email/Password

Signup:

- Validate username/email uniqueness
- Hash password (bcrypt)
- Create user + session

Login:

- Verify password hash
- Create new session

Password reset:

- `UNKNOWN`: UI docs say “Opens password reset process”, but no details.
- Minimal implementation: a page to request reset and a success message without sending email in dev; document as `UNKNOWN` and non-functional unless an email provider is configured.

### TEST_MODE OAuth Harness (Mandatory For E2E)

When `TEST_MODE=true`:

- Add deterministic endpoints to simulate OAuth for GitHub and Google.
- These endpoints MUST NOT be enabled when `TEST_MODE!=true`.

Required behaviors for tests:

- Clicking “Log in with Google” and “Log in with GitHub” can complete in a deterministic way without external network calls.

## LangGraph Design (Mandatory)

### Workflow Summary

Because UI docs do not specify workflow business logic, implement a generic multi-agent run:

- Planner/Router: creates a small plan from the run input
- Worker: executes steps using a tool-calling abstraction (placeholder tools)
- Reviewer/Validator: checks output and produces final artifact

### State Schema (Draft)

State is JSON-serializable and stored at checkpoints:

- `run_id: str`
- `input: str`
- `plan: list[str]`
- `step_index: int`
- `results: list[dict]`
- `final: dict | None`
- `errors: list[str]`

### Graph (Mermaid)

```mermaid
flowchart TD
  start([start]) --> planner[Planner/Router]
  planner --> worker[Worker]
  worker --> decide{more steps?}
  decide -- yes --> worker
  decide -- no --> reviewer[Reviewer/Validator]
  reviewer --> end([end])
```

### Nodes

- Planner/Router:
  - Input: `state.input`
  - Output: `state.plan` (deterministic plan steps)
  - Emits events: `node.started`, `node.completed`, checkpoint saved

- Worker:
  - Executes `state.plan[state.step_index]` via tool abstraction
  - Appends a result entry, increments `step_index`
  - Emits per-step events and checkpoint

- Reviewer/Validator:
  - Validates results (basic deterministic checks)
  - Creates final JSON output, stores as artifact
  - Marks run succeeded

### Persistence

For each run:

- `runs` stores current status and final output/error
- `run_events` stores event timeline
- `run_checkpoints` stores serialized state snapshots for each node boundary
- `run_artifacts` stores final output JSON + optional intermediate artifacts

### Error Handling & Retries

- Node exceptions:
  - Record `run_events` of type `error`
  - Mark run as `failed` and persist error message
- Retries:
  - Minimal deterministic retry policy: retry a failed tool execution up to `N=1` with backoff; record attempts in events

## Non-Functional Requirements

### Reproducibility

- Conda environment name MUST be `Atoms_Jerry` with `environment.yml` committed
- A deterministic local run path is required (see README + ACCEPTANCE_CHECKLIST)

### Observability

- Structured JSON logs in backend
- Persist event timeline for each run in DB

### Security Notes (Minimal)

- httpOnly session cookies
- CSRF: minimal defense by using same-site cookies for API calls in the browser; document exact setting
- Password hashing: bcrypt
- Rate limiting: minimal (optional) for login endpoints to prevent brute force (document if implemented)

## Testing Strategy (Required)

### Backend Unit Tests (pytest + httpx TestClient)

Auth:

- Signup creates user and session
- Login with correct password succeeds; wrong password fails
- OAuth callback handler upserts user and creates session (mocked provider fetch)
- Logout revokes session

Runs:

- Creating a run persists `runs` row with `queued`/`running` status
- Graph execution persists events, checkpoints, artifacts
- Permissions: user cannot access another user’s runs

### E2E Tests (Playwright, Mandatory)

Run in `TEST_MODE=true`:

- Login with Google (fake OAuth) -> redirected to protected area
- Logout -> redirected to public home and protected pages blocked
- Login with GitHub (fake OAuth) -> works
- Create a run -> run appears in list -> open details -> shows events -> shows artifacts

## Acceptance Criteria (Must Pass)

- UI pages from UI docs exist and match component/interactions tables in `docs/UI_MAP.md`
- OAuth login works for both Google and GitHub
- Local email/password signup and login work (because present in UI docs)
- Logout works
- Backend uses LangGraph for run orchestration
- Run persistence: run metadata + events + checkpoints + artifacts stored in Postgres
- Unit tests pass (`pytest`)
- E2E tests pass (`playwright`)
- One-command local run path exists and is documented

## Local Runbook (Draft; Will Be Finalized In README)

Target local commands (subject to implementation details):

- Start Postgres:
  - `docker compose up -d db`
- Create env:
  - `conda env create -f environment.yml`
  - `conda activate Atoms_Jerry`
- Run migrations:
  - `alembic upgrade head`
- Start API + worker:
  - `uvicorn app.main:app --reload --port 8000`
  - `python -m app.worker`
- Start web:
  - `cd apps/web && pnpm install && pnpm dev`
- Run tests:
  - `cd apps/api && pytest`
  - `cd apps/web && pnpm test:e2e` (Playwright)
