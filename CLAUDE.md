# CLAUDE.md

Architecture, coding rules, and execution instructions for CareerVector. Read this before making changes.

## Project Overview

CareerVector is an AI-powered Job Market & Skill Gap Intelligence Platform. It ingests vacancy and candidate data, computes skill gaps via hybrid retrieval plus deterministic set-difference logic, synthesizes learning roadmaps via a multi-agent LLM pipeline, and serves everything through a resilient, streaming FastAPI backend. Full problem statement and rationale: `README.md`.

## Locked Architecture Decisions

Do not swap any of these without discussing it first — each was chosen deliberately, not defaulted to.

| Layer | Technology | Why |
|---|---|---|
| API | FastAPI + Pydantic v2 (Python 3.12) | Async-native, typed contracts end-to-end |
| DB | PostgreSQL + SQLAlchemy 2.0 (async) + Alembic | Transactional system of record |
| Vector store | Qdrant | Native hybrid dense+sparse search in one query |
| Embeddings | sentence-transformers / BGE, local | Zero marginal cost |
| Reranking | Cross-encoder (sentence-transformers), local | Sharpens top-K precision before LLM agents see it |
| Cache/broker | Redis | Rate limiting, caching, SSE fan-out, Celery broker |
| Agent orchestration | LangGraph | Explicit, inspectable multi-agent state graph |
| Data pipeline orchestration | Prefect | Ingest → dedup → clean → validate, decoupled from agents |
| Background jobs | Celery + Redis beat | NOT Temporal — lighter footprint for scheduled polling |
| LLM provider | DeepSeek (OpenAI-compatible API), default `deepseek-chat`; Anthropic Claude supported as a swappable alternative via `LLMProvider` (`LLM_PROVIDER=anthropic`) | DeepSeek is far cheaper per token, which matters since this is a self-funded portfolio build; the existing `LLMProvider` abstraction made the swap a config change, not a rewrite, so Claude stays available |
| Evals | Ragas | Faithfulness, context precision, answer relevance |
| Streaming | SSE (`StreamingResponse`) | Simplest tool for one-directional token streaming |
| Packaging | uv | Fast, modern dependency management |

**Explicitly out of scope — documented in README's "Path to Production Scale", not implemented:** Kafka, Flink, Iceberg, Temporal.io, live distributed scraping. Do not add these dependencies. If a task seems to require them, it's out of scope for this project — extend the mock/pluggable interfaces instead.

## Coding Rules

- **Ports-and-adapters layering is load-bearing.** `domain/` must never import FastAPI, SQLAlchemy, Qdrant, or any framework/infra symbol directly. `api/` and `infra/` adapt outward to `domain/`, never the reverse. If a domain module needs persistence, define a protocol/interface in `domain/` and implement it in `infra/`.
- **Deterministic logic vs. LLM-generated logic must stay visibly separated.** Skill gap computation (`domain/skills/gap_analysis.py`) is plain Python set-difference — no LLM calls. LLM calls live only in `agents/` and `parsing/`. Do not let an agent "decide" something the deterministic layer should decide, and do not hardcode heuristics into an agent prompt that belong in `domain/`.
- **Pydantic models at every boundary.** Every API request/response, every agent input/output, and every ingestion record is a validated Pydantic model — no raw dicts crossing a layer boundary.
- **Async by default.** All I/O (DB, HTTP, LLM calls) is async. No blocking calls in request handlers.
- **No comments unless explaining non-obvious WHY.** Never restate what code does. Well-named identifiers carry the "what."
- **No premature abstraction.** Don't build for the Kafka/Flink/Temporal future — the pluggable interfaces already provide the extension point; don't speculatively generalize beyond them.
- **Follow the general engineering standards already in effect for this session:** strict type safety, minimal diffs, no unrequested refactors, no error handling for scenarios that can't happen.

## Repository Layout

```
careervector/
├── src/careervector/
│   ├── main.py                  # FastAPI entrypoint
│   ├── config.py                # pydantic-settings
│   ├── api/v1/                  # routers: vacancies, candidates, matching, copilot (SSE), health
│   ├── domain/                  # framework-agnostic business logic
│   │   ├── vacancies/  candidates/
│   │   ├── skills/               # taxonomy + deterministic gap set-diff
│   │   └── matching/             # hybrid retriever + reranker interface
│   ├── ingestion/
│   │   ├── sources/              # base.py (abstract source protocol) + mock_source.py
│   │   ├── pipelines/            # dedup, clean, validate
│   │   └── flows/                # Prefect flows
│   ├── parsing/                  # resume/markdown → structured candidate profile (LLM-assisted)
│   ├── agents/                   # LangGraph graph.py + nodes/ (parser, gap-analyst, roadmap) + prompts/
│   ├── watchdog/                 # Celery tasks + beat schedule for market monitoring
│   ├── evals/                    # ragas metrics + golden datasets + runner
│   ├── infra/
│   │   ├── db/                   # SQLAlchemy session + models
│   │   ├── vector_store/         # Qdrant client
│   │   ├── cache/                # Redis client
│   │   ├── llm/                  # provider abstraction (see below)
│   │   ├── embeddings/           # embedding model wrapper
│   │   ├── rate_limit.py  logging.py  metrics.py
│   └── core/                     # exceptions, security
├── tests/{unit,integration,e2e}/
├── scripts/seed_mock_data.py
└── data/mock/{vacancies.json, resumes/}
```

## LLM Provider Abstraction

The `LLMProvider` protocol lives in `infra/llm/client.py`; all LLM calls go through it, never direct SDK/HTTP calls from `agents/` or `parsing/`. The interface exposes at minimum:

```python
class LLMProvider(Protocol):
    async def complete(self, *, system: str, messages: list[Message], response_model: type[T] | None = None) -> T | str: ...
    async def stream(self, *, system: str, messages: list[Message]) -> AsyncIterator[str]: ...
```

Concrete implementations live one-per-file beside `client.py`: `deepseek_provider.py` (`DeepSeekLLMProvider`, default, via `httpx` against DeepSeek's OpenAI-compatible `/chat/completions` endpoint — no separate OpenAI SDK dependency needed) and `anthropic_provider.py` (`AnthropicLLMProvider`, alternative, via the Anthropic SDK). `client.py`'s `get_llm_provider()` factory picks between them based on `Settings.llm_provider` (`LLM_PROVIDER` env var, `"deepseek"` or `"anthropic"`). Both implement structured output the same way conceptually — a single forced tool/function call matching the `response_model`'s JSON schema — just via each provider's own tool-calling wire format. To swap models within a provider (e.g. `claude-opus-5` for a showcase demo), change `anthropic_default_model`/`deepseek_default_model` in `config.py`. To add a new provider, implement `LLMProvider` again in its own file and add a branch to the factory — no call sites should change.

## Testing Conventions

- `pytest` markers: `unit`, `integration`, `e2e` — run subsets with `-m unit` etc.
- `unit`: pure `domain/` logic, no I/O, no mocks needed beyond simple fakes.
- `integration`: hits real Postgres/Qdrant/Redis via docker-compose, one layer at a time (e.g. repository tests).
- `e2e`: full API request → response through the running app.
- `factory_boy` for test fixtures (vacancies, candidates, skills) — one factory module per domain entity in `tests/factories/`.
- Eval suite (`evals/runner.py`) is separate from pytest — run via its own script, not part of the default test run (LLM calls cost money and are slower).

## Execution Instructions

```bash
# First-time setup
cp .env.example .env
docker compose up -d
uv sync
uv run alembic upgrade head
uv run python scripts/seed_mock_data.py

# Run the API
uv run uvicorn careervector.main:app --reload

# Run tests
uv run pytest -m unit
uv run pytest -m integration   # requires docker-compose services up
uv run pytest                  # everything except eval suite

# Run the eval suite (costs API tokens)
uv run python -m careervector.evals.runner

# Run the watchdog worker + beat scheduler (separate processes)
uv run celery -A careervector.watchdog.celery_app worker --loglevel=info
uv run celery -A careervector.watchdog.celery_app beat --loglevel=info
```

## Scope Boundaries

Do not introduce Kafka, Flink, Iceberg, Temporal.io, or live web scraping into this codebase. These are intentionally documented as a future scale path in `README.md` and are out of scope for the current build. If a task description implies needing one of them, treat it as a documentation update to the README's "Path to Production Scale" section, not an implementation task, unless the user explicitly overrides this scope in a future session.

## Session Workflow

This project is built iteratively across sessions, following this cadence:

- **Commit as work completes, not in one dump.** Make meaningful, scoped git commits as tasks in `todo.md` are finished, not one giant commit at the end of a session.
- **Commit messages carry no AI attribution.** No `Co-Authored-By: Claude` (or similar) trailers, and no mention of Claude/AI assistance in the commit message body.
- **Push to GitHub regularly** so the remote stays in sync with local progress — don't let unpushed commits pile up across sessions.
- **Before ending a session, discuss with the user first.** Summarize what was completed and propose what the next session should tackle; don't unilaterally decide the next step.
- **Update `todo.md` to reflect that discussion** — check off finished items (`[x]`), and adjust/reorder upcoming items if the discussion changed priorities — before committing and pushing that update. Unchecked items that are partially done must say so inline (what's done, what's left) — a future session has no memory of this chat and has to work from the file alone.
- **Append a session entry to `PROGRESS.md`** before ending a session — what was built, any decisions made, and any gotchas hit (broken tooling, flaky infra, wrong assumptions corrected) and how they were resolved. `todo.md` is the task list; `PROGRESS.md` is the narrative history — keep both current, they serve different purposes.
- **Keep this file current.** Whenever an architecture, stack, or scope decision changes, update the relevant section above in the same session, not as a follow-up — future sessions rely on this file being accurate, not on chat history.
