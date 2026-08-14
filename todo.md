# CareerVector — Execution Roadmap

Phased, incremental build plan. Check items off as completed. See `CLAUDE.md` for architecture rules and `README.md` for the project narrative.

## Phase 1 — Data Foundation & Simulated Vacancies

- [x] Scaffold repo: `pyproject.toml` (uv), `docker-compose.yml` (Postgres, Qdrant, Redis, API), `Dockerfile`, `.env.example`
- [x] Define Pydantic schemas for Vacancy, Candidate, Skill (standardized across Backend/Data/AI role types)
- [x] Define SQLAlchemy 2.0 async models + first Alembic migration
- [x] Build mock vacancy generator producing realistic Backend/Data/AI Engineering postings (`data/mock/vacancies.json`, `scripts/seed_mock_data.py`)
- [x] Implement abstract ingestion source interface (`ingestion/sources/base.py`) + `mock_source.py` implementation
- [x] Implement Prefect flow: ingest → dedup → clean → validate → persist (Postgres)
- [x] Generate embeddings for vacancies and persist to Qdrant
- [x] Unit tests for dedup/clean/validate pipeline stages

## Phase 2 — Candidate Onboarding & Parsing

- [x] `POST /api/v1/candidates` endpoint accepting resume/markdown/text upload
- [x] LLM-assisted parser (`parsing/resume_parser.py`) extracting structured candidate profile via the LLM provider abstraction with `response_model` structured output
- [x] Candidate persistence: Postgres (structured) + Qdrant (profile embedding)
- [x] Sample resume fixtures (varied formats) in `tests/fixtures/resumes/`
- [x] Unit + integration tests for the parsing pipeline

## Phase 3 — Hybrid Matching & Skill Gap Engine

- [x] Dense retrieval via Qdrant (candidate ↔ vacancy embeddings)
- [x] Sparse (BM25) retrieval component
- [x] Reciprocal Rank Fusion (RRF) combining dense + sparse results
- [x] Cross-encoder reranking stage on top-K fused results
- [x] Deterministic skill gap set-difference logic (`domain/skills/gap_analysis.py`) — must-have vs. nice-to-have, no LLM calls
- [x] `POST /api/v1/matching/match` endpoint
- [x] `POST /api/v1/matching/gap-analysis` endpoint
- [x] Retrieval accuracy tests against fixture data

## Phase 4 — Agentic Copilot & Roadmap Synthesis

- [x] LangGraph graph definition (`agents/graph.py`) wiring parser → gap-analyst → roadmap-synthesizer nodes
- [x] Parser agent node (structured extraction, reuses Phase 2 parsing where possible)
- [x] Gap-analyst agent node (semantic skill-equivalence judgment on top of the deterministic diff)
- [x] Roadmap-synthesizer agent node — extended output schema including: prioritized learning roadmap, tailored resume bullets, interview prep questions
- [x] Prompt templates in `agents/prompts/`
- [x] `POST /api/v1/copilot/roadmap` endpoint (non-streaming first)
- [x] Agent-level unit tests + one full-graph integration test (full-graph test lives under `tests/unit/agents/` — it uses a fake LLM and touches no real infra, so it doesn't fit the `integration` marker's documented meaning; see PROGRESS.md session 5 for the reasoning)

## Phase 5 — Evaluation Framework

- [ ] Ragas integration (`evals/metrics.py`) wrapping faithfulness, context precision, answer relevance
- [ ] Golden eval dataset: curated candidate/vacancy pairs with expected gap/roadmap characteristics
- [ ] Eval runner script (`evals/runner.py`) producing a scored report
- [ ] Regression thresholds documented and enforced by the runner (fail below threshold)

## Phase 6 — API Hardening & Real-Time Streaming

- [ ] Convert `/copilot/roadmap` to SSE streaming (`StreamingResponse`, token-by-token)
- [ ] Redis token-bucket rate limiting (slowapi or custom) applied to all public endpoints
- [ ] Structured error handling middleware (consistent error envelope, no stack traces leaked)
- [ ] structlog structured logging with request tracing
- [ ] `/healthz` endpoint
- [ ] `/metrics` endpoint (Prometheus client)
- [ ] Minimal static HTML/JS page demonstrating SSE streaming (`static/copilot-demo.html`)

## Phase 7 — Watchdog & Background Jobs

- [ ] Celery app setup (`watchdog/celery_app.py`) with Redis broker
- [ ] Celery beat schedule for periodic vacancy-source polling
- [ ] Diff logic: compare newly polled vacancies against last-seen state per candidate
- [ ] Notification mechanism for new high-match vacancies (SSE push or log-based for the portfolio build)
- [ ] Tests for the diff/notify task logic

## Phase 8 — Testing, CI/CD & Deployment Polish

- [ ] Full test suite across unit/integration/e2e with coverage targets set and measured
- [ ] GitHub Actions CI: lint (ruff), type-check (mypy), test, eval-smoke
- [ ] Finalize `docker-compose.yml` for a complete one-command local demo
- [ ] Finalize `README.md`: verify architecture diagram and tech stack table match the final implementation
- [ ] Record a demo walkthrough (screenshots or short clip) for the portfolio presentation
