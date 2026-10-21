# HR-AIAAS — Step-by-Step Implementation Guide

**Architecture:** Fully separated frontend and backend  
**Frontend:** Next.js, TypeScript, Tailwind CSS, shadcn/ui  
**Backend:** Python, uv, FastAPI, Strawberry GraphQL, SQLAlchemy, SQLite  
**Local AI:** Ollama  
**Target:** A local-first, AI-assisted HR recruitment platform

---

## 1. Final architecture

The frontend and backend must be independent applications. They must have separate repositories, dependency managers, environment files, test suites, build pipelines, and deployment processes.

```text
hr-aiaas/
├── hr-aiaas-backend/       # Independent Git repository
├── hr-aiaas-frontend/      # Independent Git repository
└── local-infra/            # Optional third private repository
```

Runtime communication:

```text
Browser
  |
  | http://localhost:3000
  v
Next.js frontend
  |
  | GraphQL over HTTP
  | REST only for files and health checks
  v
FastAPI backend: http://localhost:8000
  |-- /graphql
  |-- /api/v1/documents/upload
  |-- /api/v1/documents/{id}/download
  |-- /health/live
  `-- /health/ready
       |
       +--> SQLite database
       +--> private document storage
       `--> Ollama: http://127.0.0.1:11434
```

### Isolation rules

1. The frontend must never access SQLite, Ollama, CV storage, or Python modules directly.
2. The backend must never import frontend code or depend on Node.js packages.
3. The GraphQL schema is the application contract.
4. REST is reserved for binary file transfer and health endpoints.
5. The browser communicates only with the backend API.
6. Database entities must not be exposed directly as GraphQL types.
7. Secrets must never use the `NEXT_PUBLIC_` prefix.
8. The frontend and backend must start, test, build, and deploy independently.

---

## 2. Prerequisites

Install:

- Git
- Python 3.12
- uv
- Node.js 22 LTS or the version approved by your organization
- pnpm through Corepack
- Ollama
- A code editor such as VS Code

Verify the tools:

```bash
git --version
python --version
uv --version
node --version
corepack --version
pnpm --version
ollama --version
```

Recommended local ports:

```text
Frontend: 3000
Backend:  8000
Ollama:   11434
```

---

# Part I — Backend repository

## 3. Create the backend repository

```bash
mkdir hr-aiaas-backend
cd hr-aiaas-backend
git init
uv init --package
uv python pin 3.12
```

Create the main folders:

```bash
mkdir -p src/hr_aiaas
mkdir -p tests/unit tests/integration tests/contract
mkdir -p migrations/versions
mkdir -p storage/documents storage/exports storage/backups
mkdir -p scripts docs/adr
```

Target structure:

```text
hr-aiaas-backend/
├── .env.example
├── .gitignore
├── README.md
├── SECURITY.md
├── alembic.ini
├── pyproject.toml
├── uv.lock
├── migrations/
├── scripts/
├── storage/                 # Ignored by Git
├── tests/
└── src/hr_aiaas/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── api/
    │   ├── health.py
    │   └── documents.py
    ├── graphql/
    │   ├── context.py
    │   ├── schema.py
    │   ├── query.py
    │   ├── mutation.py
    │   ├── types/
    │   └── inputs/
    ├── auth/
    ├── candidates/
    ├── documents/
    ├── jobs/
    ├── matching/
    ├── search/
    ├── assistant/
    ├── ai/
    ├── audit/
    ├── db/
    └── shared/
```

Use vertical domain modules. Each module may contain its own models, repository, service, GraphQL mapping, and tests. Avoid one global `services.py` or `models.py` file.

---

## 4. Install backend dependencies

```bash
uv add fastapi "uvicorn[standard]" "strawberry-graphql[fastapi]"
uv add sqlalchemy alembic aiosqlite pydantic-settings
uv add python-multipart httpx
uv add pwdlib argon2-cffi pyjwt
uv add pypdf python-docx python-magic
uv add structlog
uv add --dev pytest pytest-asyncio pytest-cov hypothesis
uv add --dev ruff mypy pre-commit
```

On Windows, `python-magic-bin` may be needed instead of `python-magic`. Verify this for the target operating system before locking production dependencies.

Use `uv.lock` as the reproducible dependency lock and commit it.

---

## 5. Configure backend environment variables

Create `.env.example`:

```dotenv
APP_NAME=HR-AIAAS API
APP_ENV=development
APP_DEBUG=true
APP_HOST=127.0.0.1
APP_PORT=8000

DATABASE_URL=sqlite+aiosqlite:///./storage/hr_aiaas.db
DOCUMENT_STORAGE_PATH=./storage/documents
EXPORT_STORAGE_PATH=./storage/exports
BACKUP_STORAGE_PATH=./storage/backups

FRONTEND_ORIGIN=http://localhost:3000
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_CHAT_MODEL=replace-with-approved-model
OLLAMA_EMBEDDING_MODEL=replace-with-approved-embedding-model

SESSION_SECRET=replace-with-at-least-32-random-bytes
ACCESS_TOKEN_MINUTES=15
SESSION_IDLE_MINUTES=30
MAX_UPLOAD_MB=15
LOG_LEVEL=INFO
```

Generate a local secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the example locally:

```bash
cp .env.example .env
```

Never commit `.env`, the SQLite database, uploaded CVs, exports, backups, or logs.

Suggested `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
storage/*
!storage/.gitkeep
*.db
*.db-shm
*.db-wal
```

---

## 6. Create backend configuration

Create `src/hr_aiaas/config.py`:

```python
from functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HR-AIAAS API"
    app_env: str = "development"
    app_debug: bool = False
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    database_url: str
    document_storage_path: str
    export_storage_path: str
    backup_storage_path: str

    frontend_origin: str = "http://localhost:3000"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str
    ollama_embedding_model: str

    session_secret: SecretStr
    access_token_minutes: int = 15
    session_idle_minutes: int = 30
    max_upload_mb: int = 15
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Fail during startup if required values are missing. Do not silently fall back to unsafe production secrets.

---

## 7. Create the FastAPI application

Create `src/hr_aiaas/main.py`:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from hr_aiaas.api.health import router as health_router
from hr_aiaas.config import get_settings
from hr_aiaas.graphql.context import get_context
from hr_aiaas.graphql.schema import schema

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check folders, database, and required application resources here.
    yield
    # Close shared resources here.


app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)

graphql_router = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphql_ide="graphiql" if settings.app_env == "development" else None,
)

app.include_router(graphql_router, prefix="/graphql")
app.include_router(health_router)
```

Do not use `allow_origins=["*"]` together with credentialed requests.

---

## 8. Add health endpoints

Create `src/hr_aiaas/api/health.py`:

```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready() -> dict[str, str]:
    # Later: test database and required local services.
    return {"status": "ready"}
```

Run the backend:

```bash
uv run uvicorn hr_aiaas.main:app --reload --host 127.0.0.1 --port 8000
```

Check:

```bash
curl http://127.0.0.1:8000/health/live
```

Expected result:

```json
{"status":"ok"}
```

---

## 9. Configure SQLite and migrations

Create:

- An async SQLAlchemy engine.
- An async session factory.
- A declarative base.
- A `get_db_session` dependency.

On every SQLite connection enable:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
```

Use WAL only after testing the target filesystem. Keep the database on a local disk, not an unreliable network share.

Initialize Alembic:

```bash
uv run alembic init migrations
```

Configure Alembic to import the SQLAlchemy metadata and read `DATABASE_URL` from application settings.

Initial migration order:

1. Users, roles, permissions, user-role, and role-permission tables.
2. Sessions and login events.
3. Candidates and candidate contact information.
4. Documents, versions, text blocks, and ingestion jobs.
5. Experience, education, skills, certifications, and languages.
6. Jobs, requirements, scorecards, and scorecard criteria.
7. Match runs, score contributions, shortlists, and review decisions.
8. Model registry, prompt versions, AI runs, and embeddings.
9. Audit, retention, deletion, and legal-hold records.
10. FTS5 virtual tables.

Create and apply a migration:

```bash
uv run alembic revision --autogenerate -m "create identity tables"
uv run alembic upgrade head
```

Never edit a migration that has already been applied to a shared environment. Add a new corrective migration.

---

## 10. Implement authentication and authorization first

Before candidate features, implement:

1. Local user login.
2. Argon2id password hashing.
3. Secure server-side session or short-lived access token with refresh-session control.
4. HttpOnly, Secure, SameSite cookie behavior.
5. CSRF protection for cookie-authenticated mutations.
6. Roles and granular permissions.
7. Department, job, or talent-pool resource scope.
8. Field-level redaction.
9. Audit events for successful and denied sensitive access.

Recommended roles:

- System Administrator
- HR Administrator
- Recruiter
- Hiring Manager
- Compliance Reviewer
- Read-only Viewer

Create one authorization entry point:

```python
await policy.require(
    actor=current_user,
    permission="candidate.read",
    resource=candidate,
)
```

Every GraphQL resolver and REST document endpoint must call the same policy service. Never rely on hidden frontend buttons for security.

---

## 11. Create the GraphQL foundation

Create `src/hr_aiaas/graphql/context.py`:

```python
from dataclasses import dataclass
from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext

from hr_aiaas.db.session import get_db_session


@dataclass
class GraphQLContext(BaseContext):
    request: Request
    response: Response
    db: AsyncSession
    current_user: object | None


async def get_context(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> GraphQLContext:
    current_user = None  # Replace with authenticated session resolution.
    return GraphQLContext(
        request=request,
        response=response,
        db=db,
        current_user=current_user,
    )
```

Create a minimal schema:

```python
import strawberry


@strawberry.type
class Health:
    status: str


@strawberry.type
class Query:
    @strawberry.field
    async def health(self) -> Health:
        return Health(status="ok")


schema = strawberry.Schema(query=Query)
```

Test it:

```graphql
query Health {
  health {
    status
  }
}
```

After authentication, add types and operations in this order:

1. `viewer`
2. Candidate list and candidate detail
3. Candidate create/update
4. Document/ingestion status
5. Jobs and scorecards
6. Search
7. Matching and shortlists
8. Assistant
9. Administration and audit

Use cursor pagination from the beginning. Do not expose unlimited candidate arrays.

---

## 12. Publish the frontend/backend contract

The frontend must generate types from a stable schema artifact, not from handwritten duplicate interfaces.

Add a backend script that exports `schema.graphql`:

```python
from pathlib import Path
from hr_aiaas.graphql.schema import schema

Path("schema.graphql").write_text(schema.as_str(), encoding="utf-8")
```

Run it:

```bash
uv run python scripts/export_graphql_schema.py
```

Recommended contract workflow:

1. Backend changes GraphQL types.
2. Backend exports `schema.graphql`.
3. Backend CI validates schema and detects breaking changes.
4. Publish the schema as a versioned CI artifact, internal package, or controlled file release.
5. Frontend CI downloads the approved schema.
6. Frontend regenerates TypeScript types.
7. Frontend build fails if operations no longer match the schema.

Do not copy backend Python models into the frontend repository.

---

## 13. Build secure document upload

Use REST for binary uploads:

```text
POST /api/v1/documents/upload
GET  /api/v1/documents/{document_id}/download
```

Upload sequence:

1. Authenticate the user.
2. Require `cv.upload`.
3. Enforce request and file size limits.
4. Validate extension and binary MIME signature.
5. Reject unsupported and malformed files.
6. Calculate SHA-256.
7. Generate an opaque storage ID.
8. Store outside the web root.
9. Create immutable document metadata.
10. Queue an ingestion job.
11. Return only `documentId`, `jobId`, and safe status.

Do not use the submitted filename as the disk filename. Preserve it only as sanitized metadata.

Initial accepted formats:

```text
application/pdf
application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

Add malware scanning when a local scanner is available. Run parsers under resource and time limits.

---

## 14. Implement the ingestion worker

Keep the worker in the backend repository because it shares domain code, but run it as a separate process:

```bash
uv run python -m hr_aiaas.worker
```

Suggested state machine:

```text
QUEUED
  -> VALIDATING
  -> PARSING
  -> NORMALIZING
  -> SECURITY_CHECK
  -> EXTRACTING
  -> VALIDATING_OUTPUT
  -> INDEXING
  -> NEEDS_REVIEW or COMPLETED
  -> FAILED_RETRYABLE or FAILED_FINAL
```

Worker requirements:

- Atomic job claim.
- Lease and heartbeat.
- Idempotency key.
- Maximum attempts.
- Bounded retries.
- Stage-specific timeout.
- Cancellation checks.
- Sanitized errors.
- Audit trail.
- Concurrency set to one initially for model-heavy work.

Start API and worker independently in two terminals.

---

## 15. Install and connect the local LLM

Start Ollama locally and install models only after an internal model evaluation and license check.

Backend model calls must pass through one `ModelGateway` interface:

```text
ModelGateway
├── health_check()
├── extract_cv(schema, document_blocks)
├── create_embeddings(texts)
└── generate_grounded_answer(context, question, schema)
```

Gateway responsibilities:

- Timeouts and bounded retry.
- Model availability.
- Structured JSON schema output.
- Pydantic validation.
- Prompt versioning.
- Model name and digest tracking.
- Context-size control.
- Concurrency limits.
- Metrics without raw CV text.

For extraction:

1. Treat CV content as untrusted data.
2. Clearly delimit it from trusted instructions.
3. Give the extraction model no tools.
4. Require a strict JSON schema.
5. Validate every response with Pydantic.
6. Require source-block references for extracted facts.
7. Never allow the LLM to write directly to candidate tables.
8. Send uncertain results to human review.

---

## 16. Implement candidate extraction and review

Create a Pydantic output contract with:

- Candidate identity fields
- Contact fields
- Professional summary
- Experience entries
- Education entries
- Skills
- Certifications
- Languages
- Projects and achievements
- Evidence references
- Field confidence
- Warnings

Rules:

- Do not infer unstated facts.
- Missing means `null` or `unknown`.
- Keep the original document immutable.
- Store extracted facts separately from reviewed facts.
- A recruiter confirmation creates a reviewed version.
- Every correction records actor, timestamp, old value, new value, and reason.

GraphQL operations:

```graphql
query IngestionJob($id: ID!)
mutation ConfirmExtractedFact($input: ConfirmFactInput!)
mutation CorrectExtractedFact($input: CorrectFactInput!)
mutation MergeCandidates($input: MergeCandidatesInput!)
```

---

## 17. Implement search

Build search in three steps.

### Step 17.1 — Structured filters

Support:

- Skill
- Minimum relevant experience
- Current or past title
- Education
- Certification
- Language
- Location, only if approved
- Candidate status
- Talent pool

### Step 17.2 — SQLite FTS5

Index only approved searchable fields. Keep private notes separate because they require different permissions.

Search results must include:

- Matched fields
- Highlighted evidence snippets
- Result score type
- Candidate access validation

### Step 17.3 — Semantic search

Generate local embeddings and version them by:

- Embedding model
- Model digest
- Source record version
- Normalization version
- Vector dimension

Evaluate `sqlite-vec` before committing to it. For a small pilot, application-level cosine similarity across a filtered candidate set is an acceptable temporary fallback.

Never compare vectors produced by different embedding models.

---

## 18. Implement deterministic candidate-to-job scoring

The LLM must not produce the official score.

Flow:

1. HR creates a job.
2. HR creates explicit requirements.
3. Authorized reviewer approves a versioned scorecard.
4. The backend scoring engine reads reviewed candidate facts.
5. It computes each criterion deterministically.
6. Each contribution links to evidence.
7. The total, missing evidence, and rule version are stored.
8. A recruiter reviews the result and decides whether to shortlist.

Example scorecard:

```text
Required skills:        35
Relevant experience:    25
Preferred skills:       15
Education:              10
Certifications:          5
Language requirements:   5
Domain evidence:         5
Total:                  100
```

Do not score name, photo, age, gender, nationality, marital status, address, disability, religion, ethnicity, or similar sensitive characteristics.

Replace “high-value person” with a job-specific classification such as `strong documented match`. Talent-pool inclusion must require human confirmation.

---

## 19. Implement the HR assistant last

Initial capabilities:

- Summarize an authorized candidate with citations.
- Explain a deterministic score.
- Compare selected candidates against one approved scorecard.
- Convert a natural-language request into visible search filters.
- Suggest evidence-based interview questions.

Restrictions:

- Read-only.
- No arbitrary SQL.
- No direct mutations.
- No email, rejection, offer, or hiring action.
- Retrieve only after authorization filters are applied.
- Show citations and missing-evidence warnings.
- Audit sensitive assistant access.

---

# Part II — Frontend repository

## 20. Create the separate frontend repository

Open a different terminal outside the backend directory:

```bash
cd ..
corepack enable
pnpm create next-app@latest hr-aiaas-frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*"

cd hr-aiaas-frontend
git init
```

Install UI and client dependencies:

```bash
pnpm dlx shadcn@latest init
pnpm add @apollo/client graphql
pnpm add react-hook-form zod @hookform/resolvers
pnpm add next-themes lucide-react
pnpm add -D @graphql-codegen/cli
pnpm add -D @graphql-codegen/client-preset
pnpm add -D @graphql-codegen/introspection
pnpm add -D vitest @testing-library/react @testing-library/jest-dom
pnpm add -D @playwright/test @axe-core/playwright
```

Target structure:

```text
hr-aiaas-frontend/
├── .env.example
├── .gitignore
├── codegen.ts
├── next.config.ts
├── package.json
├── pnpm-lock.yaml
├── public/
├── tests/
└── src/
    ├── app/
    │   ├── (auth)/
    │   ├── (dashboard)/
    │   │   ├── candidates/
    │   │   ├── jobs/
    │   │   ├── search/
    │   │   ├── assistant/
    │   │   ├── ingestion/
    │   │   ├── audit/
    │   │   └── administration/
    │   ├── layout.tsx
    │   └── globals.css
    ├── components/
    │   ├── ui/
    │   ├── layout/
    │   └── shared/
    ├── features/
    │   ├── auth/
    │   ├── candidates/
    │   ├── documents/
    │   ├── jobs/
    │   ├── matching/
    │   ├── search/
    │   └── assistant/
    ├── graphql/
    │   ├── generated/
    │   ├── operations/
    │   └── schema.graphql
    └── lib/
        ├── apollo/
        ├── auth/
        ├── env.ts
        └── permissions.ts
```

---

## 21. Configure frontend environment

Create `.env.example`:

```dotenv
NEXT_PUBLIC_APP_NAME=HR-AIAAS
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_GRAPHQL_URL=http://127.0.0.1:8000/graphql
```

Copy it:

```bash
cp .env.example .env.local
```

Only public endpoint configuration belongs in `NEXT_PUBLIC_*`. Database paths, model settings, session secrets, private keys, and storage paths belong only in the backend.

Add runtime validation in `src/lib/env.ts`:

```typescript
import { z } from "zod";

const schema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url(),
  NEXT_PUBLIC_GRAPHQL_URL: z.string().url(),
});

export const env = schema.parse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_GRAPHQL_URL: process.env.NEXT_PUBLIC_GRAPHQL_URL,
});
```

---

## 22. Configure GraphQL code generation

The frontend receives `schema.graphql` through the contract workflow. Store the approved artifact in `src/graphql/schema.graphql` for local generation.

Create `codegen.ts`:

```typescript
import type { CodegenConfig } from "@graphql-codegen/cli";

const config: CodegenConfig = {
  schema: "src/graphql/schema.graphql",
  documents: ["src/**/*.{ts,tsx}"],
  generates: {
    "src/graphql/generated/": {
      preset: "client",
    },
  },
  ignoreNoDocuments: true,
};

export default config;
```

Add scripts to `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "codegen": "graphql-codegen --config codegen.ts",
    "test": "vitest run",
    "test:e2e": "playwright test"
  }
}
```

Generate types:

```bash
pnpm codegen
```

Generated files must never be manually edited.

---

## 23. Configure Apollo Client

Create one client factory using `NEXT_PUBLIC_GRAPHQL_URL`.

Required behavior:

- Send credentials when using secure cookies.
- Send CSRF token on mutations if the backend requires it.
- Use normalized caching carefully for candidate records.
- Clear cache on logout.
- Do not persist sensitive candidate data to browser localStorage.
- Map GraphQL errors into safe user messages.
- Attach a correlation/request ID if used by the backend.

Example browser client:

```typescript
import { ApolloClient, HttpLink, InMemoryCache } from "@apollo/client";
import { env } from "@/lib/env";

export const apolloClient = new ApolloClient({
  link: new HttpLink({
    uri: env.NEXT_PUBLIC_GRAPHQL_URL,
    credentials: "include",
  }),
  cache: new InMemoryCache(),
});
```

For server components, create a request-scoped client. Do not share one global server-side cache between users.

---

## 24. Add light and dark themes

Use `next-themes` with `ThemeProvider` in the root layout.

Requirements:

- `light`, `dark`, and `system` modes.
- No flash of the wrong theme.
- Accessible contrast.
- No score/status communicated only through color.
- Respect reduced-motion preferences.

Suggested visual direction:

- Neutral gray/slate base.
- One restrained blue or teal accent.
- Clear borders and hierarchy.
- Rounded but professional components.
- Compact tables with an optional comfortable density.

---

## 25. Build the frontend shell

Build these components first:

1. App sidebar.
2. Top bar.
3. Breadcrumbs.
4. User menu.
5. Theme switcher.
6. Permission-aware navigation.
7. Loading skeleton.
8. Empty state.
9. Error state with correlation ID.
10. Access-denied page.

Navigation:

```text
Dashboard
Candidates
Review queue
Talent pools
Jobs
Search
HR Assistant
Ingestion
Audit
Administration
```

Frontend permissions improve usability, but backend authorization remains decisive.

---

## 26. Build frontend features in vertical slices

### Slice 1 — Authentication

- Login page.
- Session bootstrap using `viewer`.
- Logout.
- Unauthorized and expired-session behavior.
- Permission-aware navigation.

### Slice 2 — Candidate list

- Cursor pagination.
- Filters and sorting.
- Column controls.
- Loading, empty, error, and denied states.
- Candidate detail navigation.

### Slice 3 — Upload and ingestion

- Drag/drop and normal file selection.
- Client-side format/size hints, while backend remains authoritative.
- Upload progress.
- Ingestion-stage polling.
- Failure and retry presentation.

### Slice 4 — Extraction review

- Source document viewer.
- Extracted fields beside evidence.
- Confidence indicator.
- Confirm, correct, or mark unknown.
- Unsaved-change guard.

### Slice 5 — Jobs and scorecards

- Job editor.
- Requirements editor.
- Scorecard weights totaling 100.
- Approval state.
- Immutable prior versions.

### Slice 6 — Matching and shortlist

- Candidate/job match list.
- Criterion contributions.
- Evidence drawer.
- Missing-evidence labels.
- Manual shortlist with reason.

### Slice 7 — Search

- Structured filter builder.
- Keyword search.
- Natural-language semantic search.
- Explanation of why each result matched.
- Saved searches.

### Slice 8 — Assistant

- Read-only conversation UI.
- Safe prompt suggestions.
- Scope banner.
- Citation chips.
- Clear uncertainty and error states.

### Slice 9 — Administration

- User, role, and permission management.
- Skill taxonomy.
- Model health, not raw sensitive prompts.
- Retention settings.
- Backup status.

---

## 27. Implement file upload from the isolated frontend

The frontend sends multipart data directly to the backend REST endpoint:

```typescript
const formData = new FormData();
formData.append("file", file);

const response = await fetch(
  `${env.NEXT_PUBLIC_API_URL}/api/v1/documents/upload`,
  {
    method: "POST",
    credentials: "include",
    body: formData,
  },
);

if (!response.ok) {
  throw new Error("The CV could not be uploaded.");
}

const result = await response.json();
```

Do not manually set the multipart `Content-Type`; the browser adds the boundary.

After upload:

1. Save the returned `jobId` in component state.
2. Query GraphQL for job status.
3. Poll with a bounded interval or use a subscription later.
4. Stop polling on `COMPLETED`, `NEEDS_REVIEW`, or final failure.
5. Navigate to the review page when needed.

---

# Part III — Running both isolated applications

## 28. Start local services

### Terminal 1 — Ollama

```bash
ollama serve
```

### Terminal 2 — Backend API

```bash
cd hr-aiaas-backend
uv sync
uv run alembic upgrade head
uv run uvicorn hr_aiaas.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 3 — Backend worker

```bash
cd hr-aiaas-backend
uv run python -m hr_aiaas.worker
```

### Terminal 4 — Frontend

```bash
cd hr-aiaas-frontend
pnpm install
pnpm codegen
pnpm dev
```

Open:

```text
Frontend: http://localhost:3000
Backend health: http://127.0.0.1:8000/health/live
GraphQL IDE in development: http://127.0.0.1:8000/graphql
Ollama: http://127.0.0.1:11434
```

---

## 29. Optional local infrastructure repository

Create `hr-aiaas-local-infra` only when the team needs shared operational files.

```text
hr-aiaas-local-infra/
├── .env.example
├── compose.yaml
├── reverse-proxy/
├── scripts/
│   ├── backup.*
│   ├── restore.*
│   └── verify-egress.*
└── docs/
    ├── installation.md
    ├── operations.md
    └── recovery.md
```

Responsibilities:

- Start frontend, API, worker, and optionally Ollama.
- Configure a reverse proxy and local TLS.
- Mount persistent database/document volumes.
- Define health checks.
- Define encrypted backup and restore procedures.

Do not store business logic in the infrastructure repository.

---

## 30. CI/CD isolation

### Backend pipeline

Run:

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest --cov=hr_aiaas
uv run alembic upgrade head
uv run python scripts/export_graphql_schema.py
```

Also:

- Scan dependencies.
- Generate an SBOM.
- Validate migrations on an empty database.
- Test backup/restore scripts.
- Publish `schema.graphql` as a versioned artifact.

### Frontend pipeline

Run:

```bash
pnpm install --frozen-lockfile
pnpm codegen
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm test:e2e
```

Also:

- Download the approved backend schema artifact.
- Run accessibility checks.
- Scan dependencies.
- Fail on GraphQL contract incompatibility.

### Contract rule

A breaking backend schema change must not be released until the frontend has a compatible release. Prefer additive schema evolution and deprecate fields before removal.

---

## 31. Security checklist before a pilot

- [ ] Backend allows only the exact trusted frontend origins.
- [ ] Production GraphQL IDE is disabled.
- [ ] Query depth, complexity, alias, and rate limits are active.
- [ ] Every resolver and file endpoint has authorization tests.
- [ ] Sensitive fields use field-level authorization.
- [ ] Cookies are HttpOnly, Secure, and appropriately SameSite.
- [ ] CSRF defenses are tested.
- [ ] Passwords use Argon2id.
- [ ] CVs are outside the web root under opaque names.
- [ ] Upload type, signature, and size checks are enforced.
- [ ] Parsers have CPU, memory, and timeout limits.
- [ ] CV content is treated as untrusted prompt data.
- [ ] The extraction model has no tools.
- [ ] LLM output is schema-validated.
- [ ] Official scoring is deterministic and evidence-based.
- [ ] Protected or sensitive characteristics are excluded from ranking.
- [ ] Raw CV content is absent from ordinary logs.
- [ ] Database, documents, and backups are encrypted at rest.
- [ ] Egress rules prevent external AI calls.
- [ ] Deletion removes derived data, embeddings, and search index rows.
- [ ] Backup restoration has been tested.
- [ ] Human review and override are available and audited.
- [ ] Privacy, HR, security, and legal reviews are complete.

---

## 32. Recommended implementation sequence

Do not develop all backend endpoints and then all frontend pages. Build complete vertical slices while preserving repository isolation.

### Milestone 1 — Foundation

1. Create both repositories.
2. Configure quality tools and CI.
3. Start FastAPI and Next.js independently.
4. Add health checks.
5. Add the GraphQL schema export/code-generation workflow.
6. Verify frontend-to-backend GraphQL communication.

**Done when:** the frontend displays backend health using a generated GraphQL operation.

### Milestone 2 — Security foundation

1. Create identity tables.
2. Implement login and logout.
3. Resolve `viewer` in GraphQL.
4. Add RBAC and resource scope.
5. Add audit events.
6. Build login and protected shell in the frontend.

**Done when:** each role sees only authorized navigation and backend data.

### Milestone 3 — CV upload without AI

1. Create document metadata and ingestion job tables.
2. Add secure upload endpoint.
3. Store documents safely.
4. Parse text-based PDF and DOCX.
5. Build upload/progress UI.
6. Add failure handling.

**Done when:** an authorized recruiter uploads and parses a CV with a full audit trail.

### Milestone 4 — AI extraction and human review

1. Create local model gateway.
2. Create versioned extraction schema and prompt.
3. Extract facts with evidence.
4. Validate outputs.
5. Build review/correction UI.
6. Establish an evaluation dataset and release threshold.

**Done when:** reviewed structured data is created without unsupported silent claims.

### Milestone 5 — Search

1. Add structured search.
2. Add FTS5.
3. Evaluate embeddings and vector storage.
4. Add semantic search if approved.
5. Build result explanation.

**Done when:** recruiters find known relevant profiles within agreed quality and latency targets.

### Milestone 6 — Job matching

1. Create jobs and requirements.
2. Create versioned scorecards.
3. Add approval workflow.
4. Implement deterministic scoring.
5. Display evidence and contributions.
6. Add human-managed shortlists.

**Done when:** every displayed point can be reproduced from approved rules and reviewed facts.

### Milestone 7 — HR assistant

1. Add authorization-first retrieval.
2. Add grounded summarization.
3. Add score explanation.
4. Add controlled comparison.
5. Add natural-language search-filter generation.
6. Red-team the assistant.

**Done when:** it remains read-only, evidence-grounded, and permission-safe.

### Milestone 8 — Hardening and pilot

1. Accessibility and performance testing.
2. Adversarial file and prompt testing.
3. Backup/restore drill.
4. Retention/deletion drill.
5. No-egress verification.
6. Operational documentation and user training.
7. Limited pilot with monitored feedback.

**Done when:** business, privacy, security, and HR owners approve the controlled pilot.

---

## 33. First development sprint

A practical first sprint backlog:

### Backend

- [ ] Initialize `uv` project and lock dependencies.
- [ ] Add settings validation.
- [ ] Add FastAPI application and CORS allowlist.
- [ ] Add `/health/live` and `/health/ready`.
- [ ] Configure SQLAlchemy, SQLite, and Alembic.
- [ ] Add minimal Strawberry schema.
- [ ] Add schema export script.
- [ ] Add Ruff, mypy, pytest, and CI.

### Frontend

- [ ] Initialize Next.js and pnpm lockfile.
- [ ] Configure shadcn/ui and themes.
- [ ] Add environment validation.
- [ ] Configure Apollo Client.
- [ ] Configure GraphQL Code Generator.
- [ ] Build the shell, loading, error, and denied states.
- [ ] Display backend health.
- [ ] Add ESLint, TypeScript check, Vitest, Playwright, and CI.

### Contract and operations

- [ ] Publish/download `schema.graphql` between pipelines.
- [ ] Document local startup.
- [ ] Verify no backend secret appears in the browser bundle.
- [ ] Verify repositories can build independently.

---

## 34. Definition of done for every feature

A feature is complete only when:

- Backend authorization and resource scope are enforced.
- Audit requirements are implemented.
- GraphQL contract is exported and frontend types regenerate successfully.
- Frontend has loading, empty, error, denied, and success states.
- Unit and integration tests pass.
- Important journeys have end-to-end tests.
- Accessibility is checked.
- No sensitive data is written to logs or browser persistence.
- Database migration and recovery implications are documented.
- AI output has validation, evidence, failure behavior, and evaluation coverage.
- Both repositories build independently.

---

## 35. Immediate next action

Begin with **Milestone 1** only:

```text
1. Create the backend repository.
2. Create the frontend repository.
3. Start FastAPI on port 8000.
4. Start Next.js on port 3000.
5. Add one GraphQL health query.
6. Export the backend schema.
7. Generate frontend types.
8. Display “Backend status: OK” in the frontend.
9. Add independent CI pipelines.
10. Commit both repositories separately.
```

This establishes the isolation boundary before candidate data, files, authentication, or AI make the architecture harder to change.

---

# Part IV — Docker Compose setup

## 36. Compose workspace layout

Keep the frontend and backend as independent repositories, but place them under one local workspace so Compose can build each repository with its own Dockerfile:

```text
hr-aiaas-workspace/
├── compose.yaml
├── .env.compose.example
├── hr-aiaas-backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── ...
└── hr-aiaas-frontend/
    ├── Dockerfile
    ├── .dockerignore
    └── ...
```

Compose is orchestration only. It does not remove repository isolation:

- Each application owns its Dockerfile and dependencies.
- The backend owns the database schema and migrations.
- The frontend consumes only HTTP/GraphQL contracts.
- SQLite files, CV documents, exports, backups, and Ollama models use named volumes.
- Only the frontend, backend, and optionally Ollama are published to localhost.
- The internal service names are `backend`, `worker`, `migrate`, and `ollama`.

## 37. Backend Dockerfile

Create `hr-aiaas-backend/Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/
WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home /app app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations
RUN mkdir -p /app/storage/documents /app/storage/exports /app/storage/backups \
    && chown -R app:app /app/storage

USER app
EXPOSE 8000

CMD ["uvicorn", "hr_aiaas.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Pin the `uv` image to the version approved by the project and update it through dependency maintenance. Do not use floating tags for controlled deployments.

## 38. Backend Docker ignore file

Create `hr-aiaas-backend/.dockerignore`:

```dockerignore
.git
.github
.env
.venv
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
.coverage
htmlcov
storage
*.db
*.db-shm
*.db-wal
tests
.vscode
.idea
```

## 39. Frontend Dockerfile

Enable standalone output in `hr-aiaas-frontend/next.config.ts`:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
```

Create `hr-aiaas-frontend/Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1.7
FROM node:22-alpine AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
WORKDIR /app

FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile

FROM base AS builder
ARG NEXT_PUBLIC_APP_NAME=HR-AIAAS
ARG NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
ARG NEXT_PUBLIC_GRAPHQL_URL=http://127.0.0.1:8000/graphql
ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME \
    NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_GRAPHQL_URL=$NEXT_PUBLIC_GRAPHQL_URL \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

FROM node:22-alpine AS runner
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000
WORKDIR /app
RUN addgroup --system --gid 10001 nodejs \
    && adduser --system --uid 10001 nextjs
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

`NEXT_PUBLIC_*` values are embedded during the Next.js build. Rebuild the frontend image when those public URLs change. Never place secrets in these variables.

## 40. Frontend Docker ignore file

Create `hr-aiaas-frontend/.dockerignore`:

```dockerignore
.git
.github
.env
.env.local
node_modules
.next
coverage
playwright-report
test-results
.vscode
.idea
```

## 41. Compose environment file

Create `.env.compose.example` beside `compose.yaml`:

```dotenv
COMPOSE_PROJECT_NAME=hr-aiaas

BACKEND_PORT=8000
FRONTEND_PORT=3000
OLLAMA_PORT=11434

APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=INFO
SESSION_SECRET=replace-with-at-least-32-random-bytes
ACCESS_TOKEN_MINUTES=15
SESSION_IDLE_MINUTES=30
MAX_UPLOAD_MB=15

OLLAMA_IMAGE=ollama/ollama:latest
OLLAMA_CHAT_MODEL=replace-with-approved-model
OLLAMA_EMBEDDING_MODEL=replace-with-approved-embedding-model

NEXT_PUBLIC_APP_NAME=HR-AIAAS
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_GRAPHQL_URL=http://127.0.0.1:8000/graphql
```

For an internal release, replace floating image tags with approved immutable tags or digests. Copy the example and generate a secret:

```bash
cp .env.compose.example .env.compose
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Insert the generated value into `SESSION_SECRET`. Do not commit `.env.compose`.

## 42. Compose file

Create `compose.yaml` in the workspace root:

```yaml
name: ${COMPOSE_PROJECT_NAME:-hr-aiaas}

services:
  ollama:
    image: ${OLLAMA_IMAGE:-ollama/ollama:latest}
    restart: unless-stopped
    environment:
      OLLAMA_HOST: 0.0.0.0:11434
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "127.0.0.1:${OLLAMA_PORT:-11434}:11434"
    networks:
      - ai_internal
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 20s

  model-init:
    image: ${OLLAMA_IMAGE:-ollama/ollama:latest}
    restart: "no"
    environment:
      OLLAMA_HOST: http://ollama:11434
      OLLAMA_CHAT_MODEL: ${OLLAMA_CHAT_MODEL}
      OLLAMA_EMBEDDING_MODEL: ${OLLAMA_EMBEDDING_MODEL}
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - ai_internal
    depends_on:
      ollama:
        condition: service_healthy
    entrypoint: ["/bin/sh", "-c"]
    command:
      - |
        set -eu
        ollama pull "$${OLLAMA_CHAT_MODEL}"
        if [ "$${OLLAMA_EMBEDDING_MODEL}" != "$${OLLAMA_CHAT_MODEL}" ]; then
          ollama pull "$${OLLAMA_EMBEDDING_MODEL}"
        fi

  migrate:
    build:
      context: ./hr-aiaas-backend
      dockerfile: Dockerfile
    restart: "no"
    env_file:
      - .env.compose
    environment:
      DATABASE_URL: sqlite+aiosqlite:////app/storage/hr_aiaas.db
      DOCUMENT_STORAGE_PATH: /app/storage/documents
      EXPORT_STORAGE_PATH: /app/storage/exports
      BACKUP_STORAGE_PATH: /app/storage/backups
      FRONTEND_ORIGIN: http://localhost:${FRONTEND_PORT:-3000}
      OLLAMA_BASE_URL: http://ollama:11434
    volumes:
      - backend_storage:/app/storage
    networks:
      - app_internal
    command: ["alembic", "upgrade", "head"]

  backend:
    build:
      context: ./hr-aiaas-backend
      dockerfile: Dockerfile
    restart: unless-stopped
    init: true
    env_file:
      - .env.compose
    environment:
      DATABASE_URL: sqlite+aiosqlite:////app/storage/hr_aiaas.db
      DOCUMENT_STORAGE_PATH: /app/storage/documents
      EXPORT_STORAGE_PATH: /app/storage/exports
      BACKUP_STORAGE_PATH: /app/storage/backups
      FRONTEND_ORIGIN: http://localhost:${FRONTEND_PORT:-3000}
      OLLAMA_BASE_URL: http://ollama:11434
    volumes:
      - backend_storage:/app/storage
    ports:
      - "127.0.0.1:${BACKEND_PORT:-8000}:8000"
    networks:
      - public_edge
      - app_internal
      - ai_internal
    depends_on:
      migrate:
        condition: service_completed_successfully
      model-init:
        condition: service_completed_successfully
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=3)"
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 20s
    stop_grace_period: 30s

  worker:
    build:
      context: ./hr-aiaas-backend
      dockerfile: Dockerfile
    restart: unless-stopped
    init: true
    env_file:
      - .env.compose
    environment:
      DATABASE_URL: sqlite+aiosqlite:////app/storage/hr_aiaas.db
      DOCUMENT_STORAGE_PATH: /app/storage/documents
      EXPORT_STORAGE_PATH: /app/storage/exports
      BACKUP_STORAGE_PATH: /app/storage/backups
      FRONTEND_ORIGIN: http://localhost:${FRONTEND_PORT:-3000}
      OLLAMA_BASE_URL: http://ollama:11434
    volumes:
      - backend_storage:/app/storage
    networks:
      - app_internal
      - ai_internal
    depends_on:
      migrate:
        condition: service_completed_successfully
      model-init:
        condition: service_completed_successfully
    command: ["python", "-m", "hr_aiaas.worker"]
    stop_grace_period: 60s

  frontend:
    build:
      context: ./hr-aiaas-frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_APP_NAME: ${NEXT_PUBLIC_APP_NAME:-HR-AIAAS}
        NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://127.0.0.1:8000}
        NEXT_PUBLIC_GRAPHQL_URL: ${NEXT_PUBLIC_GRAPHQL_URL:-http://127.0.0.1:8000/graphql}
    restart: unless-stopped
    init: true
    environment:
      NODE_ENV: production
      HOSTNAME: 0.0.0.0
      PORT: 3000
    ports:
      - "127.0.0.1:${FRONTEND_PORT:-3000}:3000"
    networks:
      - public_edge
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test:
        - CMD
        - node
        - -e
        - "fetch('http://127.0.0.1:3000').then(r => { if (!r.ok) process.exit(1) }).catch(() => process.exit(1))"
      interval: 15s
      timeout: 5s
      retries: 10
      start_period: 20s

networks:
  public_edge:
    driver: bridge
  app_internal:
    driver: bridge
    internal: true
  ai_internal:
    driver: bridge
    internal: true

volumes:
  backend_storage:
  ollama_data:
```

Compose starts dependencies in order, but readiness requires health checks and long-form `depends_on` conditions. The file therefore waits for Ollama readiness, successful model initialization, successful migrations, and backend health before starting dependent services.

The `model-init` service intentionally runs once and exits. On later starts, Ollama reuses the persistent model volume, and pulling an already-present model should verify/reuse it rather than losing it with the container.

## 43. Validate and start the stack

From `hr-aiaas-workspace`:

```bash
# Validate interpolation and Compose structure.
docker compose --env-file .env.compose config --quiet

# Build the independent application images.
docker compose --env-file .env.compose build

# Start all services.
docker compose --env-file .env.compose up -d

# Inspect status and health.
docker compose --env-file .env.compose ps

# Follow startup logs.
docker compose --env-file .env.compose logs -f ollama model-init migrate backend worker frontend
```

Open:

```text
Frontend: http://127.0.0.1:3000
Backend health: http://127.0.0.1:8000/health/ready
GraphQL: http://127.0.0.1:8000/graphql
Ollama API: http://127.0.0.1:11434
```

Check the services:

```bash
curl http://127.0.0.1:8000/health/ready
curl http://127.0.0.1:11434/api/tags
```

## 44. Common Compose operations

```bash
# Stop containers but retain data volumes.
docker compose --env-file .env.compose stop

# Start stopped containers.
docker compose --env-file .env.compose start

# Rebuild only the backend and worker.
docker compose --env-file .env.compose build backend worker
docker compose --env-file .env.compose up -d backend worker

# Rebuild the frontend after changing NEXT_PUBLIC values.
docker compose --env-file .env.compose build --no-cache frontend
docker compose --env-file .env.compose up -d frontend

# Re-run migrations explicitly.
docker compose --env-file .env.compose run --rm migrate

# Open a backend shell.
docker compose --env-file .env.compose exec backend sh

# Check available Ollama models.
docker compose --env-file .env.compose exec ollama ollama list

# Stop and remove containers/networks while retaining volumes.
docker compose --env-file .env.compose down

# DANGER: remove containers and all local application/model volumes.
docker compose --env-file .env.compose down --volumes
```

Do not use `down --volumes` on an environment containing real candidate data unless an approved, verified backup exists and destruction is intentional.

## 45. NVIDIA GPU override

The base Compose file is CPU-compatible. For an NVIDIA host, create `compose.gpu.yaml`:

```yaml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

Start with both files:

```bash
docker compose \
  --env-file .env.compose \
  -f compose.yaml \
  -f compose.gpu.yaml \
  up -d
```

The host must have a supported NVIDIA driver and NVIDIA Container Toolkit. Validate GPU visibility before relying on acceleration:

```bash
docker compose exec ollama ollama ps
docker compose logs ollama
```

Keep CPU mode as the portable default. Maintain separate reviewed overrides for AMD/ROCm or platform-specific acceleration rather than putting every hardware path into one Compose file.

## 46. Development override

Production-like Compose images should not mount source code. If containerized hot reload is desired, create `compose.dev.yaml` and use it only for development:

```yaml
services:
  backend:
    build:
      context: ./hr-aiaas-backend
    environment:
      APP_ENV: development
      APP_DEBUG: "true"
    volumes:
      - ./hr-aiaas-backend/src:/app/src:ro
      - ./hr-aiaas-backend/migrations:/app/migrations:ro
      - backend_storage:/app/storage
    command:
      - uvicorn
      - hr_aiaas.main:app
      - --host
      - 0.0.0.0
      - --port
      - "8000"
      - --reload

  worker:
    environment:
      APP_ENV: development
      APP_DEBUG: "true"
    volumes:
      - ./hr-aiaas-backend/src:/app/src:ro
      - backend_storage:/app/storage

  frontend:
    build:
      context: ./hr-aiaas-frontend
      target: deps
    working_dir: /app
    environment:
      NODE_ENV: development
      NEXT_TELEMETRY_DISABLED: "1"
      NEXT_PUBLIC_API_URL: http://127.0.0.1:8000
      NEXT_PUBLIC_GRAPHQL_URL: http://127.0.0.1:8000/graphql
    volumes:
      - ./hr-aiaas-frontend:/app
      - frontend_node_modules:/app/node_modules
      - frontend_next:/app/.next
    command: ["pnpm", "dev", "--hostname", "0.0.0.0"]

volumes:
  frontend_node_modules:
  frontend_next:
```

Run it with:

```bash
docker compose \
  --env-file .env.compose \
  -f compose.yaml \
  -f compose.dev.yaml \
  up --build
```

Native development remains simpler for debugging. Use this override when the team specifically wants a container-only environment.

## 47. SQLite operational rules in Compose

Because the API and worker share one SQLite database:

1. Mount the same `backend_storage` volume into `migrate`, `backend`, and `worker`.
2. Run migrations through the one-shot `migrate` service before API/worker startup.
3. Enable foreign keys, WAL mode, and a busy timeout in backend connection configuration.
4. Keep worker concurrency at one initially.
5. Keep the SQLite file on a local Docker volume, not a network filesystem.
6. Do not scale `backend` or `worker` horizontally without a measured concurrency test and database architecture review.
7. Stop write services or use SQLite’s supported online-backup API when creating a consistent backup.

## 48. Backup and restore

The Compose volume contains both the SQLite database and private documents. A correct backup must capture them consistently.

Recommended backup workflow:

```bash
# 1. Pause new user activity and stop write services.
docker compose --env-file .env.compose stop frontend backend worker

# 2. Run the project's versioned backup command in a temporary backend container.
docker compose --env-file .env.compose run --rm \
  backend python -m hr_aiaas.operations.backup

# 3. Copy/export the encrypted backup according to the operations runbook.

# 4. Restart services.
docker compose --env-file .env.compose up -d backend worker frontend
```

Do not rely on copying an actively written `.db` file. Implement and test application-level backup/restore commands before the pilot. Backups must be encrypted, access-controlled, retained according to policy, and periodically restored in a test environment.

## 49. Compose security hardening before production

Before deployment to a shared local server:

- Bind published ports to `127.0.0.1` unless a reviewed reverse proxy is used.
- Put local TLS and authentication controls at the reverse proxy.
- Pin Docker images by approved version or digest.
- Scan images and generate an SBOM.
- Run application containers as non-root users.
- Add read-only root filesystems and temporary filesystems after validating required write paths.
- Set CPU and memory limits based on load tests.
- Prevent direct browser access to Ollama in the production network design.
- Apply host firewall/egress rules. Compose `internal` networks isolate container routing but are not a complete host egress policy.
- Store secrets through the organization’s approved secret mechanism rather than committed environment files.
- Protect Docker daemon access. Docker control effectively grants high privilege on the host.
- Verify backup encryption and restoration.
- Confirm that logs do not contain CV content, contact details, prompts, tokens, or session secrets.

## 50. Compose acceptance test

The setup is complete when all checks pass:

```bash
# Configuration is valid.
docker compose --env-file .env.compose config --quiet

# Services reach expected state.
docker compose --env-file .env.compose ps

# API readiness works.
curl --fail http://127.0.0.1:8000/health/ready

# Ollama responds and required models are present.
curl --fail http://127.0.0.1:11434/api/tags
docker compose --env-file .env.compose exec ollama ollama list

# Frontend responds.
curl --fail http://127.0.0.1:3000

# Backend migrations are current.
docker compose --env-file .env.compose run --rm backend alembic current

# Independent images can be rebuilt.
docker compose --env-file .env.compose build backend worker frontend
```

Then execute one end-to-end test:

1. Sign in as a recruiter.
2. Upload a non-sensitive test CV.
3. Confirm the worker processes it.
4. Confirm the local model performs extraction.
5. Review extracted evidence in the frontend.
6. Restart the Compose stack.
7. Confirm the candidate, document, and Ollama models persist.
8. Confirm an unauthorized role cannot access the same CV.

