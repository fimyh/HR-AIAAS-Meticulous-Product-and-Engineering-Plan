# HR-AIAAS — Meticulous Product and Engineering Plan

**Document status:** Initial architecture and delivery plan  
**Prepared:** 21 October 2026  
**Target:** Local-first AI-assisted HR recruitment platform  
**Primary stack:** Python + `uv`, FastAPI, Strawberry GraphQL, SQLite, Ollama, Next.js, TypeScript, Tailwind CSS, shadcn/ui

---

## 1. Executive summary

HR-AIAAS is a local-first recruitment assistant that ingests CVs, extracts and archives candidate information, supports structured and semantic profile search, explains candidate-to-job matches, and helps HR staff build shortlists.

The platform must treat AI as a **decision-support system**, not an autonomous hiring authority. Every score, recommendation, shortlist, or extracted fact must remain reviewable, traceable to evidence, and overridable by an authorized human. The system must never auto-reject a candidate solely because of an LLM output.

### Core design decisions

1. **Modular monolith first:** one Python backend, one Next.js frontend, one SQLite database, and one local Ollama service. This is simpler to operate and test than microservices.
2. **GraphQL for application data:** Strawberry GraphQL mounted on FastAPI at `/graphql`.
3. **Small REST surface where appropriate:** `/health`, authentication/session endpoints if needed, and file upload/download endpoints. Binary CV upload should not be forced through GraphQL.
4. **Local AI only:** Ollama hosts chat/extraction and embedding models on the same machine or trusted local network.
5. **Hybrid retrieval:** deterministic SQL filters + SQLite FTS5 keyword search + optional local vector similarity.
6. **Evidence-based ranking:** deterministic, job-specific scoring calculates the official score. The LLM extracts evidence and writes explanations but does not silently invent or control ranking weights.
7. **Human-in-the-loop:** high-value status and shortlist decisions require an authorized user action.
8. **Privacy and auditability by default:** least privilege, append-only audit records, configurable retention, secure deletion workflow, and no external model/API calls.

---

## 2. Product boundaries

### 2.1 Goals

- Reduce manual CV reading and data entry.
- Build a searchable local talent database.
- Generate structured candidate summaries with source evidence.
- Match profiles against explicit job requirements.
- Explain why a profile received a score.
- Save promising profiles into controlled talent pools.
- Give HR staff a professional, fast, accessible interface.
- Provide role-based access and a full audit trail.
- Keep candidate documents, extracted data, and model traffic local.

### 2.2 Non-goals for the first release

- Autonomous candidate rejection or hiring.
- Emotion, personality, honesty, facial, voice, or psychological inference.
- Inferring protected or sensitive attributes.
- Scraping external websites or social networks.
- Payroll, attendance, performance monitoring, or full HRIS functionality.
- Email/calendar automation.
- Multi-tenant SaaS hosting.
- Training or fine-tuning a foundation model on candidate CVs.
- Microservices, Kubernetes, or a separate vector database.

### 2.3 Success measures

- Median CV processing time on target hardware.
- Extraction accuracy by field against a manually labeled validation set.
- Search precision at 5 and recall at 20 for recruiter test queries.
- Percentage of AI claims linked to document evidence.
- Recruiter correction rate for extracted data.
- Agreement between displayed score and deterministic scoring rules.
- Zero unauthorized cross-role data access in security tests.
- Zero production calls to public AI services.
- Time saved per reviewed CV, measured in a pilot rather than assumed.

---

## 3. Risk and governance position

AI-assisted recruitment and candidate ranking can materially affect people. Treat this as a high-impact and potentially high-risk system from the start.

### Mandatory product rules

- AI outputs are recommendations, never final employment decisions.
- UI labels must say **AI-assisted**, show confidence, and expose supporting evidence.
- A low-confidence extraction must enter a review queue.
- No hidden scoring criteria. Each criterion, weight, contribution, and missing item must be visible.
- Do not use name, photo, age/date of birth, gender, nationality, marital status, address, disability, religion, ethnicity, or similar attributes in ranking.
- Do not use proxies for protected attributes unless a documented lawful requirement exists and legal/privacy owners approve it.
- Candidate ranking must be tied to a specific approved job scorecard.
- Historical hiring outcomes must not become labels for model training without a separate fairness and governance review.
- HR users can override suggestions, but overrides require a reason and are audited.
- The system must support correction, export, retention, deletion, and legal-hold workflows.
- Before a production pilot, obtain review from HR, information security, privacy/legal, and the relevant worker/employee representation process where applicable.

### Governance artifacts to maintain

- Intended-use and prohibited-use statement.
- Data inventory and processing map.
- Data protection impact assessment or equivalent privacy assessment.
- AI risk register.
- Model cards and model/license inventory.
- Dataset description for evaluation data.
- Scoring rubric approval history.
- Release approval checklist.
- Incident response procedure.
- User instructions and known-limitations page.
- Periodic bias, accuracy, and access-control review reports.

---

## 4. Users, roles, and permissions

Use permissions in the backend. The frontend may hide controls for usability, but it must never be the authorization boundary.

### 4.1 Suggested roles

#### System Administrator

- Manage users, roles, permissions, system configuration, model configuration, backup, and restore.
- Cannot view candidate documents by default. Grant candidate-data permission separately.

#### HR Administrator

- Manage HR users, retention policies, skill taxonomy, job templates, scoring rubrics, and talent pools.
- View audit events relevant to HR operations.

#### Recruiter

- Upload CVs, review extraction, search profiles, create jobs, run matches, add notes, and manage shortlists.

#### Hiring Manager

- View only assigned jobs and approved candidate summaries/shortlists.
- Cannot view raw CVs or private recruiter notes unless explicitly granted.

#### Reviewer / Compliance Auditor

- Read audit logs, model runs, scoring explanations, and evaluation reports.
- No mutation permissions.

#### Read-only Viewer

- View explicitly assigned records with redacted fields.

### 4.2 Permission examples

Use granular permission codes such as:

```text
candidate.read
candidate.read_sensitive
candidate.create
candidate.update
candidate.delete_request
candidate.export
candidate.merge
cv.upload
cv.download
cv.reprocess
job.create
job.update
job.scorecard.approve
match.run
match.view
shortlist.manage
talent_pool.manage
note.private.read
user.manage
role.manage
audit.read
model.configure
system.backup
system.restore
```

### 4.3 Authorization model

Combine:

- **RBAC:** role grants permission.
- **Resource scope:** user can access only assigned departments, jobs, or talent pools.
- **Field-level redaction:** sensitive fields omitted unless permission exists.
- **Resolver-level checks:** every GraphQL resolver calls the same policy service.
- **Audit:** log denied access attempts as well as sensitive successful actions.

---

## 5. Functional scope

### 5.1 Candidate and CV ingestion

Supported first-release formats:

- PDF with embedded text.
- DOCX.
- Optional later phase: scanned PDF/image through local OCR.

Ingestion flow:

1. User uploads a file through a dedicated upload endpoint.
2. Validate permission, extension, MIME signature, size, and safe filename.
3. Calculate SHA-256 for deduplication and integrity.
4. Store the original file outside the web root under an opaque generated ID.
5. Run malware scanning if available locally.
6. Extract text using a format-specific parser.
7. Normalize Unicode, whitespace, dates, phone numbers, URLs, and sections.
8. Detect language; preserve the original text.
9. Split text into traceable blocks containing page/section offsets.
10. Run prompt-injection and suspicious-content checks. Treat document text as untrusted data.
11. Extract structured data with a schema-constrained local LLM call.
12. Validate the result using Pydantic and deterministic validators.
13. Link every extracted field to one or more source blocks.
14. Calculate confidence at field and document level.
15. Create or suggest a candidate record; do not merge uncertain duplicates automatically.
16. Generate embeddings for approved searchable text.
17. Update FTS and vector indexes.
18. Place low-confidence or conflicting records in the review queue.
19. Record pipeline status, parser/model versions, timings, and errors.

### 5.2 Structured extraction schema

Extract only job-relevant information:

- Given and family name, kept for identification but excluded from ranking.
- Contact details, separately protected.
- Professional title and summary.
- Work experiences: employer, title, start/end date, description, derived duration.
- Education: institution, degree, field, dates.
- Skills with evidence, last-used date when explicit, and confidence.
- Certifications with issuer and date.
- Languages and stated proficiency.
- Projects and achievements.
- Location and work authorization only if legitimately required and approved.
- Source language.
- Parsing warnings and ambiguities.

Do not infer unstated information. Use `null`, `unknown`, or a warning instead.

### 5.3 Candidate search

Support three layers:

1. **Structured filters:** skills, experience range, title, education, certification, language, location, availability, talent pool, and profile status.
2. **Keyword search:** SQLite FTS5 across normalized profile text, experience, skills, and notes where permission allows.
3. **Semantic search:** local embeddings for natural-language requirements such as “backend engineer with Python API and HR systems experience.”

Hybrid ranking proposal:

```text
retrieval_score =
    0.40 * normalized_structured_match +
    0.35 * normalized_fts_bm25 +
    0.25 * normalized_vector_similarity
```

These retrieval weights are starting hypotheses. Validate them using recruiter-labeled relevance judgments. Keep retrieval relevance separate from the formal candidate/job score.

### 5.4 Job definitions and scorecards

A job record contains:

- Title, department, hiring manager, location, employment type, and status.
- Description and responsibilities.
- Required skills and minimum proficiency.
- Preferred skills.
- Minimum relevant experience.
- Required certifications or languages.
- Disqualifying constraints only when lawful and explicitly approved.
- Scoring criteria and weights.
- Scorecard version, author, reviewer, approval timestamp, and change history.

A job cannot run an official ranking until its scorecard is approved.

### 5.5 Candidate scoring

Use a deterministic scoring service, not an unconstrained LLM score.

Example categories:

```text
required_skills       35 points
relevant_experience   25 points
preferred_skills      15 points
education             10 points
certifications         5 points
language_requirements  5 points
role/domain evidence   5 points
TOTAL                 100 points
```

Rules:

- Weights are job-specific and must total 100.
- Missing data means “not demonstrated,” not “candidate lacks the capability.”
- Each awarded point references extracted evidence.
- Hard requirements must be few, explicit, and approved.
- Score bands are configurable. Example: `85–100 strong documented match`, `70–84 review`, `<70 insufficient documented evidence`.
- Never label a person as globally “low value.” Use **match quality for this job**.
- “High-value profile” should become **talent-pool candidate** or **priority follow-up**, requiring human confirmation.
- Recompute scores when a CV, extraction, taxonomy, job, or scorecard version changes.
- Store score inputs, output, rule version, and explanation so a past result can be reproduced.

### 5.6 Talent pools

- HR-created pools such as “Senior Python,” “Finance,” or “Future leadership.”
- Manual add/remove with reason.
- AI may suggest entry but may not add automatically in the initial release.
- Expiration/review date for every membership.
- Candidate consent or lawful-basis status tracked as required by the organization.

### 5.7 HR assistant

Initial assistant capabilities:

- Answer questions about candidates the current user is authorized to view.
- Summarize a CV with citations to source sections.
- Compare selected candidates against an approved job scorecard.
- Explain a score and identify missing evidence.
- Translate or rewrite job-relevant summaries while preserving meaning.
- Build a search filter from a natural-language request, then show the generated filters before execution.
- Suggest interview questions tied to the role and documented experience, excluding sensitive topics.

Assistant limitations:

- Read-only in the first release.
- No direct database mutation tool.
- No arbitrary SQL.
- No autonomous emails, offers, rejections, or status changes.
- Every retrieval is authorization-filtered before content reaches the model.
- Show document citations and state when evidence is insufficient.

---

## 6. Proposed architecture

```text
[Browser]
   |
   | HTTPS on local network
   v
[Next.js App Router]
   |
   | GraphQL over HTTP
   | Upload/download REST endpoints
   v
[FastAPI Application]
   |-- Strawberry GraphQL schema
   |-- Authentication and authorization service
   |-- Candidate/job/search/scoring services
   |-- Document ingestion worker
   |-- AI orchestration gateway
   |-- Audit service
   |
   +--> [SQLite]
   |      |-- relational data
   |      |-- FTS5 indexes
   |      `-- vector extension or application-level vector search
   |
   +--> [Local file storage]
   |      `-- original CVs and controlled exports
   |
   `--> [Ollama on localhost/trusted LAN]
          |-- extraction/chat model
          `-- embedding model
```

### 6.1 Why a modular monolith

- One deployable backend and one transaction boundary.
- Easier local installation, backup, audit, and troubleshooting.
- Clear internal modules preserve a future migration path.
- SQLite fits controlled local concurrency and pilot scale.
- Avoid a queue broker initially; use a database-backed job table and a separate worker process.

### 6.2 Backend stack

- Python 3.12 or a version validated by all native dependencies.
- `uv` for Python/runtime/dependency management and lockfile.
- FastAPI as ASGI host.
- Strawberry GraphQL.
- Pydantic for settings and AI output validation.
- SQLAlchemy 2.x with Alembic migrations.
- `aiosqlite` only where async DB access is justified.
- `pypdf`/PyMuPDF for PDF text extraction after license review.
- `python-docx` or direct OOXML extraction for DOCX.
- `python-magic` or equivalent signature verification.
- Argon2id password hashing for local credentials.
- Structlog or standard structured JSON logging.
- Pytest, pytest-asyncio, Hypothesis, Ruff, and mypy/pyright.

### 6.3 Frontend stack

- Next.js App Router and TypeScript.
- Tailwind CSS and shadcn/ui.
- GraphQL Code Generator for typed documents and types.
- Apollo Client or urql. Choose one after a small cache/error-handling spike.
- React Hook Form + Zod for forms.
- next-themes for light/dark/system mode.
- WCAG-oriented accessible components, keyboard navigation, focus states, and contrast.

### 6.4 Local LLM stack

- Ollama as the initial model runtime because it provides a local HTTP API, embeddings, and structured outputs.
- One extraction/chat model selected through an evaluation bake-off.
- One multilingual embedding model selected through retrieval evaluation.
- Pin model identifiers/digests and record them with every AI run.
- Bind Ollama to localhost unless network access is explicitly required.
- Deny outbound internet access for the backend and Ollama in the production profile.
- Define hardware tiers rather than assuming one model fits every workstation.

Example tiers:

- **Developer:** small quantized model, CPU acceptable, reduced context.
- **Pilot:** 16–32 GB RAM and a supported GPU where available.
- **Production local server:** capacity determined by measured concurrent users, context size, and latency target.

Do not select the final model by popularity. Evaluate extraction accuracy, languages used by the company, hallucination rate, latency, memory, license, and security support.

---

## 7. Repository structure

```text
hr-aiaas/
├── README.md
├── SECURITY.md
├── CONTRIBUTING.md
├── .env.example
├── docker-compose.yml             # optional local orchestration
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── graphql/
│   ├── governance/
│   ├── operations/
│   └── threat-model/
├── apps/
│   ├── api/
│   │   ├── pyproject.toml
│   │   ├── uv.lock
│   │   ├── alembic.ini
│   │   ├── migrations/
│   │   ├── src/hr_aiaas/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── graphql/
│   │   │   ├── auth/
│   │   │   ├── candidates/
│   │   │   ├── documents/
│   │   │   ├── jobs/
│   │   │   ├── matching/
│   │   │   ├── search/
│   │   │   ├── assistant/
│   │   │   ├── audit/
│   │   │   ├── db/
│   │   │   └── shared/
│   │   └── tests/
│   ├── worker/
│   │   └── uses backend package and database job queue
│   └── web/
│       ├── app/
│       ├── components/
│       ├── features/
│       ├── graphql/
│       ├── lib/
│       ├── public/
│       └── tests/
├── packages/
│   ├── eslint-config/
│   └── ui/                        # only if shared components justify it
├── data/                          # ignored by Git
│   ├── db/
│   ├── documents/
│   ├── exports/
│   └── backups/
└── scripts/
    ├── dev.*
    ├── backup.*
    ├── restore.*
    └── verify_no_external_ai.*
```

Keep backend domain modules vertically organized. Avoid large generic `utils` and `services` folders.

---

## 8. Data model

Use UUIDv7 or generated opaque UUIDs for public IDs. Internal SQLite integer keys may be used for efficient joins, but never expose file paths or sequential identifiers unnecessarily.

### 8.1 Identity and access

- `users`
- `roles`
- `permissions`
- `user_roles`
- `role_permissions`
- `resource_assignments`
- `sessions`
- `password_reset_tokens`
- `login_events`

### 8.2 Candidate domain

- `candidates`
- `candidate_contacts`
- `candidate_preferences`
- `experiences`
- `education_records`
- `skills`
- `candidate_skills`
- `certifications`
- `candidate_certifications`
- `languages`
- `candidate_languages`
- `projects`
- `candidate_notes`
- `candidate_tags`
- `candidate_tag_links`
- `talent_pools`
- `talent_pool_memberships`
- `candidate_consents_or_basis`

### 8.3 Document domain

- `documents`: metadata, hash, size, MIME, path token, state.
- `document_versions`: immutable versions.
- `document_text_blocks`: page, section, offsets, normalized text.
- `extraction_runs`: parser/model/prompt/schema versions and timings.
- `extracted_facts`: field, value, confidence, review status.
- `fact_evidence`: links facts to source blocks and offsets.
- `ingestion_jobs`: queued/running/succeeded/failed/retry state.
- `ingestion_errors`: sanitized diagnostic details.

### 8.4 Job and matching domain

- `jobs`
- `job_requirements`
- `scorecards`
- `scorecard_versions`
- `scorecard_criteria`
- `match_runs`
- `candidate_job_scores`
- `score_contributions`
- `shortlists`
- `shortlist_entries`
- `review_decisions`

### 8.5 AI and search domain

- `model_registry`
- `prompt_templates`
- `prompt_versions`
- `ai_runs`
- `ai_run_inputs`: metadata/references, not unnecessary duplicated PII.
- `ai_run_outputs`
- `embedding_records`
- FTS5 virtual tables for allowed searchable content.
- Vector table if `sqlite-vec` passes the architecture spike.

### 8.6 Operations and governance

- `audit_events`
- `retention_rules`
- `deletion_requests`
- `legal_holds`
- `exports`
- `system_settings`
- `feature_flags`

### 8.7 Important constraints

- Unique document SHA-256 with a controlled duplicate-resolution flow.
- Foreign keys enabled.
- Check constraints for confidence and scores.
- Soft delete for operational hiding, followed by an accountable purge workflow.
- Immutable versions for documents, scorecards, prompts, and model configurations.
- Transactionally update relational data and enqueue reindexing/recalculation jobs.
- Store UTC timestamps; render in the user’s locale/time zone.

---

## 9. GraphQL design

### 9.1 Principles

- Schema-first product contract even if implemented code-first.
- Cursor pagination for all collections.
- Explicit filter and sort input types.
- Mutation payloads return the object, user-safe errors, and a correlation ID.
- Use DataLoader to avoid N+1 queries.
- Async resolvers; move blocking parsing/model calls to the worker.
- Disable introspection and GraphQL IDE in hardened production unless an admin setting enables them.
- Add query depth, complexity, alias, batch, and request-size limits.
- Persisted/allowlisted operations for production clients when practical.
- Never expose internal stack traces.

### 9.2 Primary queries

```graphql
viewer
candidate(id: ID!): Candidate
candidates(filter: CandidateFilter, sort: CandidateSort, first: Int, after: String): CandidateConnection
candidateSearch(input: CandidateSearchInput!): CandidateSearchConnection
job(id: ID!): Job
jobs(filter: JobFilter, first: Int, after: String): JobConnection
jobMatches(jobId: ID!, scorecardVersionId: ID!, first: Int, after: String): MatchConnection
talentPool(id: ID!): TalentPool
talentPools(first: Int, after: String): TalentPoolConnection
ingestionJob(id: ID!): IngestionJob
auditEvents(filter: AuditFilter, first: Int, after: String): AuditEventConnection
assistantConversation(id: ID!): AssistantConversation
```

### 9.3 Primary mutations

```graphql
createCandidate(input: CreateCandidateInput!): CandidatePayload
updateCandidate(input: UpdateCandidateInput!): CandidatePayload
confirmExtractedFact(input: ConfirmFactInput!): FactPayload
correctExtractedFact(input: CorrectFactInput!): FactPayload
mergeCandidates(input: MergeCandidatesInput!): MergePayload
createJob(input: CreateJobInput!): JobPayload
updateJob(input: UpdateJobInput!): JobPayload
createScorecardVersion(input: CreateScorecardInput!): ScorecardPayload
approveScorecardVersion(id: ID!): ScorecardPayload
runJobMatching(input: RunMatchingInput!): MatchingRunPayload
addToTalentPool(input: TalentPoolMemberInput!): TalentPoolPayload
removeFromTalentPool(input: TalentPoolMemberInput!): TalentPoolPayload
createShortlist(input: CreateShortlistInput!): ShortlistPayload
recordReviewDecision(input: ReviewDecisionInput!): ReviewDecisionPayload
requestCandidateDeletion(input: DeletionRequestInput!): DeletionPayload
sendAssistantMessage(input: AssistantMessageInput!): AssistantMessagePayload
```

### 9.4 File transfer strategy

Use REST endpoints:

```text
POST /api/documents/upload
GET  /api/documents/{id}/download
GET  /health/live
GET  /health/ready
```

The upload endpoint returns a document ID and ingestion job ID. GraphQL tracks status and retrieves results. This avoids GraphQL multipart complexity and keeps size/streaming controls straightforward.

### 9.5 Error model

User-safe codes:

```text
UNAUTHENTICATED
FORBIDDEN
NOT_FOUND
VALIDATION_ERROR
CONFLICT
FILE_REJECTED
INGESTION_FAILED
MODEL_UNAVAILABLE
RATE_LIMITED
INTERNAL_ERROR
```

Every error includes a correlation ID. Sensitive diagnostics remain in protected local logs.

---

## 10. AI orchestration design

### 10.1 Gateway abstraction

All model calls pass through one `ModelGateway` interface. Business modules never call Ollama directly.

Responsibilities:

- Model selection and availability checks.
- Timeouts, bounded retries, concurrency limits, and circuit breaker.
- Structured-output schema submission.
- Token/context budgeting.
- Prompt versioning.
- Input/output redaction for logs.
- Metrics and audit metadata.
- Model digest recording.
- No-network policy enforcement.

### 10.2 Extraction workflow

- Send only the necessary CV blocks.
- Delimit untrusted document content clearly.
- System instruction says document content is data, not instructions.
- Require a JSON schema derived from the Pydantic extraction model.
- Validate types, date order, duration, duplicates, and evidence offsets.
- Reject unsupported fields or facts without evidence.
- Run deterministic post-processing.
- Route failures and uncertainty to human review.

### 10.3 RAG workflow for the assistant

1. Authenticate the user.
2. Resolve permissions and resource scope.
3. Classify the request into an allowed assistant capability.
4. Build structured filters.
5. Retrieve only authorized records.
6. Select the minimum evidence needed.
7. Generate an answer with source references.
8. Apply output validation and sensitive-field filtering.
9. Return answer, citations, limitations, and correlation ID.
10. Audit the action without logging full sensitive prompts by default.

### 10.4 Prompt management

Every prompt has:

- ID and semantic version.
- Purpose and owner.
- Input/output schema version.
- Model compatibility.
- Test cases.
- Approved status.
- Change reason and reviewer.
- Rollback pointer.

Prompts belong in version-controlled files, not inline strings scattered across resolvers.

### 10.5 Model evaluation gate

Prepare a de-identified or synthetic labeled test set representing actual CV formats and languages. Evaluate candidates on:

- Exact/normalized field accuracy.
- Unsupported claim rate.
- Evidence correctness.
- JSON/schema validity.
- Multilingual accuracy.
- Scanned/noisy document robustness.
- Prompt-injection resistance.
- Latency and memory.
- License suitability.
- Consistency across repeated runs.

No model enters production only because sample outputs “look good.” Define thresholds before evaluation.

---

## 11. Search and retrieval implementation

### 11.1 FTS5

Create an external-content FTS5 index over specifically allowed fields. Use `unicode61` initially, evaluate diacritics and multilingual tokenization, and use BM25 for keyword ranking. Private notes should use a separate index and permission path.

### 11.2 Semantic vectors

Run an architecture spike for `sqlite-vec` because it is pre-1.0. Acceptance criteria:

- Reproducible installation on target Windows/Linux machines.
- Correct loading with the Python SQLite build.
- Backup and restore validation.
- Delete behavior and data-remanence review.
- Performance over expected profile volume.
- Stable dimension and model-version handling.
- License and security review.

Fallback for an initial small pilot: store normalized embeddings as BLOBs and calculate cosine similarity in the application for a constrained candidate set. Avoid pretending this scales indefinitely.

### 11.3 Reindexing

Embeddings and indexes must be versioned by:

- Source record version.
- Normalization version.
- Embedding model and digest.
- Vector dimension.
- Creation timestamp.

A model change creates a background reindex job. Never mix vectors from different embedding models in one comparison.

---

## 12. Security and privacy plan

### 12.1 Threat model priorities

- Unauthorized employee access to candidate PII.
- CV files containing malware or parser exploits.
- Indirect prompt injection embedded in CV text, metadata, images, or hidden layers.
- GraphQL denial of service and over-fetching.
- Broken object-level/field-level authorization.
- Data leakage through logs, exports, backups, model prompts, or cached UI state.
- Score manipulation through CV keyword stuffing or hidden instructions.
- Dependency and model supply-chain compromise.
- Theft of the host or backup media.

### 12.2 Required controls

- TLS even on a local network.
- Local authentication with Argon2id; enterprise SSO can be a later integration.
- Secure, HttpOnly, SameSite cookies and CSRF protection where applicable.
- Short sessions, idle timeout, account lockout/backoff, and admin MFA if feasible locally.
- Central authorization service called from every resolver and download endpoint.
- File-size limits, MIME signature checks, sanitized names, isolated storage, and malware scanning.
- Run parsers and OCR in a restricted process/container with CPU, memory, and time limits.
- Never execute macros, embedded files, links, or CV-provided instructions.
- Restrict model tools; the extraction model gets no tools.
- Parameterized database queries.
- GraphQL query cost/depth limits and per-user rate limits.
- Strict Content Security Policy and no third-party analytics/scripts in production.
- Avoid browser localStorage for tokens or sensitive candidate content.
- Redact PII from logs and error traces.
- Append-only audit semantics with tamper-evident hash chaining if required.
- Encrypted disk/volume for database, documents, and backups.
- Backup encryption, restore testing, and controlled key custody.
- Dependency lockfiles, SBOM, vulnerability scanning, and verified model files/digests.
- Egress firewall rules proving the local-only promise.

### 12.3 Prompt-injection controls

- Treat extracted CV text as hostile content.
- Separate trusted instructions from untrusted data with structured prompts.
- Do not let model output call tools or mutate data.
- Validate all output against an allowlisted schema.
- Strip/flag hidden Unicode, suspicious white-on-white text, metadata anomalies, and repeated manipulation phrases, while preserving the original for audit.
- Use deterministic scoring so instructions in a CV cannot set a score.
- Compare visible rendering with extracted text for suspicious hidden content where feasible.
- Red-team with malicious resumes.
- Show warnings to reviewers without claiming detection is perfect.

### 12.4 Retention and deletion

- Define retention by record type and recruitment purpose.
- Add periodic retention jobs that generate reviewable purge plans.
- Legal hold stops purge with recorded authority.
- Deletion cascades through source files, derived text, embeddings, FTS rows, caches, exports, and non-required AI outputs.
- Backups require an expiry schedule and documented restore-then-delete handling.
- Audit logs should retain minimized event metadata, not copied CV text.

---

## 13. User experience plan

### 13.1 Navigation

```text
Dashboard
Candidates
  - All candidates
  - Review queue
  - Talent pools
Jobs
  - Open jobs
  - Scorecards
  - Shortlists
Search
HR Assistant
Ingestion
Audit (authorized users)
Administration
  - Users and roles
  - Skills taxonomy
  - Models and prompts
  - Retention
  - Backup and system status
```

### 13.2 Key screens

#### Dashboard

- CVs awaiting review.
- Failed ingestion jobs.
- Active jobs and pending shortlists.
- Expiring talent-pool memberships.
- Model or backup health alerts.
- No vanity metrics that encourage rapid rejection.

#### Candidate list

- Fast filters, saved searches, pagination, column controls, and accessible table/list modes.
- Clearly distinguish verified, AI-extracted, and missing fields.
- Bulk actions limited and confirmation-protected.

#### Candidate profile

- Overview, experience, skills, education, documents, match history, notes, and audit timeline.
- Source-evidence drawer opens the relevant page/section.
- Inline correction creates a new reviewed fact version.
- Sensitive fields are grouped and permission-gated.

#### Review queue

- Original document beside extracted facts.
- Confidence and warnings.
- Confirm, correct, mark unknown, or request reprocessing.
- Keyboard-first workflow.

#### Job and matching

- Scorecard editor with weight total validation.
- Side-by-side contribution breakdown.
- Transparent “missing evidence” labels.
- Shortlist action requires a human reason.

#### Assistant

- Suggested safe prompts.
- Citation chips link to records and document evidence.
- Scope banner explains which records are being searched.
- Clear “AI can make mistakes” notice without overwhelming the workflow.

### 13.3 Visual behavior

- Professional neutral palette with one restrained accent color.
- Light, dark, and system themes.
- Avoid color as the only meaning for scores or status.
- Skeletons for normal loading, progress stages for ingestion, and actionable error states.
- Confirm irreversible or privacy-sensitive actions.
- Responsive desktop-first design; mobile supports review and search but not dense scorecard editing initially.

---

## 14. Background jobs and resilience

Use a SQLite-backed `ingestion_jobs` table with a separate worker process.

### State machine

```text
QUEUED -> VALIDATING -> PARSING -> NORMALIZING -> EXTRACTING
      -> VALIDATING_OUTPUT -> INDEXING -> NEEDS_REVIEW | COMPLETED
      -> FAILED_RETRYABLE | FAILED_FINAL | CANCELLED
```

Requirements:

- Atomic job claim with lease/heartbeat.
- Idempotency key based on document version and pipeline version.
- Bounded exponential backoff.
- Maximum attempts.
- Cancellation checks between stages.
- Dead-letter/final failure view.
- Resume/reprocess from a controlled stage.
- User-safe failure message plus protected diagnostics.
- Concurrency default of one model-heavy job until measured.

---

## 15. Testing strategy

### 15.1 Backend

- Unit tests for domain rules and scoring.
- Property tests for score bounds, weight totals, and date normalization.
- Resolver authorization tests for every query and mutation.
- Database migration up/down and fresh-install tests.
- Parser tests with a maintained CV fixture corpus.
- Contract tests for Ollama responses and schema failures.
- GraphQL complexity and malformed-operation tests.
- Upload adversarial tests: double extension, zip bomb, corrupted PDF, oversized file, macro-containing DOCX.

### 15.2 Frontend

- Component tests for access states, forms, score explanations, and theme behavior.
- Generated GraphQL type checking in CI.
- Playwright end-to-end tests for recruiter and admin journeys.
- Accessibility checks with axe plus manual keyboard/screen-reader testing.
- Visual regression for main pages in light and dark themes.

### 15.3 AI quality

- Golden extraction dataset.
- Evidence-grounding tests.
- Hallucination/unsupported-claim tests.
- Multilingual test set matching expected CV languages.
- Prompt-injection suite including hidden document instructions.
- Retrieval benchmark with relevance labels.
- Candidate ordering stability tests.
- Fairness review using lawful, controlled evaluation methods and expert oversight.

### 15.4 Operational

- Backup/restore drill.
- Database corruption recovery rehearsal.
- Ollama unavailable/slow/out-of-memory scenarios.
- Disk-full and permission-failure tests.
- Egress test proving no public AI traffic.
- Load tests based on anticipated concurrent HR users and CV volume.

---

## 16. Observability and audit

### Metrics

- Requests, latency, error rate, and GraphQL operation cost.
- Upload count/size and rejected files.
- Job queue depth, stage duration, retries, and failures.
- Model latency, timeout, schema-valid response rate, and resource use.
- Search latency and zero-result rate.
- Extraction review/correction rate.
- Backup age and last successful restore test.

### Logs

- Structured JSON.
- Correlation ID across frontend request, GraphQL resolver, worker job, and model call.
- No raw CV text, contact details, model prompt bodies, session secrets, or passwords.
- Configurable levels and retention.

### Audit events

Capture actor, action, resource type/ID, timestamp, outcome, reason, originating session/device metadata, and relevant version IDs. Audit:

- Candidate/document views and downloads.
- Create/update/merge/delete/export actions.
- Scorecard approval and match execution.
- Shortlist and talent-pool changes.
- Permission and model configuration changes.
- Backup/restore and retention actions.
- Sensitive assistant queries.

---

## 17. Delivery roadmap

The durations below are planning ranges for a small focused team, not commitments. Run governance and evaluation work in parallel rather than postponing them to the end.

### Phase 0 — Discovery and safeguards (1–2 weeks)

Deliverables:

- Approved product scope and prohibited uses.
- User journeys and initial permission matrix.
- Data inventory and retention assumptions.
- Threat model and privacy/AI impact-assessment kickoff.
- Expected data volume, concurrency, languages, file types, and target hardware.
- Model shortlist and evaluation plan.
- Architecture decision records for GraphQL, SQLite, Ollama, and file storage.

Exit criteria:

- Stakeholders approve the MVP boundary.
- No unresolved assumption about autonomous decisions or sensitive attributes.

### Phase 1 — Foundation (1–2 weeks)

Deliverables:

- Monorepo and local developer setup.
- Backend initialized with `uv`, FastAPI, Strawberry, SQLAlchemy, Alembic, lint/type/test tools.
- Next.js, Tailwind, shadcn/ui, themes, base layout, and GraphQL code generation.
- SQLite configuration, migrations, health endpoints, structured logging, and correlation IDs.
- CI for formatting, linting, type checks, tests, dependency audit, and frontend build.

Exit criteria:

- One command starts web, API, worker, and Ollama dependencies.
- CI is green on a clean checkout.

### Phase 2 — Identity, RBAC, and audit (1–2 weeks)

Deliverables:

- Local user authentication.
- Role/permission administration.
- Policy service and resolver guards.
- Audit event service and protected audit UI.
- Test matrix proving denied and allowed access.

Exit criteria:

- No candidate feature is merged without authorization tests.

### Phase 3 — Candidate and document core (2–3 weeks)

Deliverables:

- Candidate CRUD and profile UI.
- Secure PDF/DOCX upload and storage.
- Document metadata, job queue, worker, parser, and progress UI.
- Deduplication and manual duplicate resolution.
- Review queue skeleton.

Exit criteria:

- Files are securely ingested without AI.
- Backup/restore includes database and documents.

### Phase 4 — Local AI extraction (2–4 weeks)

Deliverables:

- Ollama gateway and model registry.
- Versioned structured extraction prompt/schema.
- Evidence links and confidence model.
- Human fact review/correction flow.
- Evaluation harness and baseline report.
- Prompt-injection defenses and adversarial test corpus.

Exit criteria:

- Extraction meets predeclared quality thresholds.
- Unsupported claims and low confidence are visible and reviewable.

### Phase 5 — Search and talent pools (2–3 weeks)

Deliverables:

- Structured search filters.
- FTS5 keyword search.
- Embedding generation and semantic-search spike.
- Hybrid result explanation.
- Saved searches and talent pools.

Exit criteria:

- Search benchmark meets agreed relevance/latency targets.
- User scope is enforced before retrieval and model use.

### Phase 6 — Jobs and deterministic matching (2–3 weeks)

Deliverables:

- Job and requirement management.
- Versioned scorecard builder and approval.
- Deterministic scoring engine.
- Evidence-backed contribution view.
- Shortlists and human decisions.
- Recalculation on source/rule changes.

Exit criteria:

- Every point is reproducible and explainable.
- No protected/sensitive field influences score.

### Phase 7 — HR assistant (2–3 weeks)

Deliverables:

- Authorization-aware RAG assistant.
- Candidate summary, comparison, score explanation, and search-filter generation.
- Source citations and insufficiency handling.
- Assistant-specific red-team and privacy tests.

Exit criteria:

- Assistant is read-only.
- It cannot retrieve or reveal records beyond user scope.

### Phase 8 — Hardening and pilot (2–4 weeks)

Deliverables:

- Accessibility, performance, security, and recovery testing.
- GraphQL cost controls and rate limits.
- Encrypted backup/restore runbook.
- Admin and recruiter training.
- Governance package and release checklist.
- Limited pilot with monitoring and feedback loop.

Exit criteria:

- Security/privacy/HR owners approve the pilot.
- Rollback, incident, and manual fallback procedures are tested.

### Phase 9 — Post-pilot improvements

Potential items:

- Local OCR for scanned documents.
- Enterprise identity integration.
- More languages.
- Advanced duplicate resolution.
- Controlled export templates.
- Improved retrieval/reranking after evaluation.
- Move to PostgreSQL only if measured write concurrency, scale, or availability requires it.

---

## 18. MVP prioritization

### Must have

- Authentication, RBAC, resource scope, and audit.
- Candidate profile management.
- Secure PDF/DOCX upload.
- Local extraction with evidence and review.
- Structured filters and FTS5 search.
- Jobs, approved scorecards, deterministic scoring, and explanation.
- Human-managed talent pools and shortlists.
- Light/dark/system themes.
- Backup, restore, retention, and deletion workflows.
- AI evaluation and prompt-injection testing.

### Should have

- Semantic search.
- Read-only HR assistant.
- Saved searches.
- Candidate comparison.
- Admin model/prompt health screen.

### Could have

- OCR.
- SSO.
- Multilingual UI.
- Advanced vector indexing.
- Notification center.

### Will not have in MVP

- Automatic rejection.
- Public SaaS tenancy.
- External AI APIs.
- Social-media scraping.
- Personality/emotion inference.
- Automated emails or offers.

---

## 19. Definition of done

A feature is done only when:

- Acceptance criteria are met.
- Backend authorization is implemented and tested.
- Audit requirements are implemented.
- Empty/loading/error/denied states exist.
- GraphQL schema and generated client types are updated.
- Unit/integration/E2E tests pass.
- Accessibility has been checked.
- Logs do not expose sensitive data.
- Migrations and rollback/recovery implications are documented.
- AI features include evaluation cases, evidence handling, and failure behavior.
- Documentation and runbooks are updated.
- Security/privacy implications have been reviewed at the agreed level.

---

## 20. Initial engineering backlog

### Epic A — Architecture and repository

- Create ADR-001 modular monolith.
- Create ADR-002 Strawberry GraphQL on FastAPI.
- Create ADR-003 SQLite constraints and migration path.
- Create ADR-004 local Ollama runtime.
- Create ADR-005 secure file storage.
- Scaffold API, web, worker, docs, and scripts.
- Add quality gates and CI.

### Epic B — Identity and authorization

- Implement users, roles, permissions, sessions, and password policy.
- Implement policy service and GraphQL context.
- Add resource assignments and field redaction.
- Build role administration UI.
- Add authorization test matrix.

### Epic C — Ingestion

- Create upload endpoint and file validator.
- Store files under opaque IDs.
- Implement PDF/DOCX parsing.
- Add job state machine and worker lease.
- Add hash-based duplicate detection.
- Build ingestion status and failure UI.

### Epic D — Extraction and review

- Define Pydantic extraction contracts.
- Implement Ollama gateway.
- Add prompt/model registry and versioning.
- Link facts to evidence.
- Build review/correction workflow.
- Create evaluation dataset and reports.
- Add malicious CV test suite.

### Epic E — Search

- Add structured filter DSL and GraphQL inputs.
- Implement FTS5 schema and indexing triggers/jobs.
- Evaluate embedding models.
- Spike `sqlite-vec` and fallback.
- Implement hybrid ranking and explanation.
- Add saved searches.

### Epic F — Jobs and matching

- Implement jobs and requirements.
- Implement scorecard versions and approval.
- Build deterministic scoring engine.
- Store contribution/evidence records.
- Build comparison and shortlist screens.
- Add recalculation jobs.

### Epic G — Assistant

- Implement allowed-intent router.
- Add authorization-first retrieval.
- Add grounded response/citation contract.
- Build conversation UI.
- Add assistant audit and red-team tests.

### Epic H — Operations

- Add encrypted backup script and manifest.
- Add restore verification command.
- Add retention/deletion jobs.
- Add system/model health page.
- Add release checklist and incident runbook.

---

## 21. Decisions to make before implementation

1. Expected number of candidates, documents, concurrent users, and daily uploads.
2. Target operating system and hardware, especially RAM/GPU.
3. Required CV and UI languages.
4. Whether deployment is one workstation or a local server accessed by several HR users.
5. Authentication source: local accounts or corporate identity.
6. Approved retention periods and deletion authority.
7. Whether scanned documents are common enough to put OCR in the MVP.
8. Exact job scorecard governance and approvers.
9. Which fields hiring managers may see.
10. Whether vector search is required for MVP or may follow FTS5.
11. Backup location, encryption keys, restore objective, and maximum tolerable data loss.
12. Legal/privacy classification and organizational approval workflow.

Record answers as ADRs or governance decisions. Do not leave them only in chat or meeting notes.

---

## 22. Recommended first vertical slice

Build one end-to-end workflow before broadening scope:

1. Recruiter signs in.
2. Recruiter uploads one text-based PDF CV.
3. Worker securely parses it.
4. Local model returns schema-constrained fields.
5. Recruiter reviews and corrects extracted facts with evidence.
6. Candidate becomes searchable through structured filters and FTS5.
7. Recruiter creates a job with an approved three-criterion scorecard.
8. Deterministic engine calculates a transparent match.
9. Recruiter manually adds the candidate to a shortlist.
10. Auditor verifies the complete event trail.

This slice validates the hardest boundaries: files, AI, evidence, authorization, scoring, search, human review, and audit.

---

## 23. Reference documentation

- uv documentation: <https://docs.astral.sh/uv/>
- FastAPI GraphQL guidance: <https://fastapi.tiangolo.com/how-to/graphql/>
- Strawberry FastAPI integration: <https://strawberry.rocks/docs/integrations/fastapi>
- Next.js App Router: <https://nextjs.org/docs/app>
- Ollama structured outputs: <https://docs.ollama.com/capabilities/structured-outputs>
- Ollama embeddings: <https://docs.ollama.com/capabilities/embeddings>
- SQLite FTS5: <https://sqlite.org/fts5.html>
- sqlite-vec: <https://github.com/asg017/sqlite-vec>
- OWASP prompt injection guidance: <https://genai.owasp.org/llmrisk/llm01-prompt-injection/>
- European Commission AI Act employment examples: <https://ai-act-service-desk.ec.europa.eu/en/employment-0>

---

## 24. Final recommendation

Start with a secure modular monolith and a narrow, measurable recruitment workflow. Make extraction evidence-based, search hybrid, scoring deterministic, and all consequential actions human-controlled. The most important engineering outcome is not merely “the model works.” It is that authorized HR users can understand, correct, reproduce, and safely govern everything the model contributes.
