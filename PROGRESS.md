# CareerVector — Progress Log

Narrative session history. `todo.md` tracks what's left; this file tracks what happened and why, so a new session (or you, skimming later) doesn't have to reconstruct it from chat transcripts.

---

## Session 1 — 2026-08-15

**Completed:**
- Connected the local repo to GitHub: authenticated `gh` CLI, created `https://github.com/Msinkus/CareerVector` (public), pushed the initial docs commit.
- Scaffolded the repo per `CLAUDE.md`'s layout: `pyproject.toml` (uv-managed deps — FastAPI, SQLAlchemy async, Qdrant, LangGraph, Prefect, Celery, Ragas, Anthropic SDK), `docker-compose.yml` (Postgres/Qdrant/Redis/API), `Dockerfile`, `.env.example`, `.gitignore`, and the full `src/careervector/` ports-and-adapters package tree.
- Installed `uv` via Homebrew; confirmed `uv sync` resolves and installs the full dependency set cleanly (226 packages).
- Built the core domain models (`src/careervector/domain/`): `Skill`/`SkillRequirement` (must-have vs. nice-to-have), `Vacancy`, `Candidate` — all Pydantic, framework-agnostic per the layering rule. Added `pydantic-settings`-based `config.py`.
- Built the persistence layer (`src/careervector/infra/db/`): SQLAlchemy 2.0 async ORM models mirroring the domain models, async engine/session factory, and Alembic scaffolding wired to `Base.metadata` and `Settings.database_url`.

**Decisions / gotchas:**
- `gh auth login` succeeded as account `Msinkus`, but the first `git push` got a 403 — macOS `osxkeychain` had a stale credential for a different account (`Batyrkhan314`) that git tried first. Fixed with `gh auth setup-git`, which makes gh's credential helper take precedence for `github.com`. Worth remembering if push auth fails after a fresh `gh auth login`.
- `pydantic.EmailStr` requires the `email-validator` package, which isn't pulled in by `pydantic` alone — added it explicitly to `pyproject.toml`.
- Used `datetime.now(UTC)` instead of the deprecated `datetime.utcnow()` in default factories (flagged by IDE diagnostics).
- Docker (Rancher Desktop) wasn't running at first; started it with `rdctl start` and polled `docker info` until ready. The `postgres:16-alpine` image pull then hit an intermittent registry timeout on the first attempt — retried and it succeeded. If this recurs, it's transient registry flakiness, not a config problem.
- `uv run <cmd>` is the reliable way to run project code — `source .venv/bin/activate` did not actually put the venv first on `PATH` in this shell (likely another tool, e.g. pyenv or the Spark setup on this machine, overriding it). Prefer `uv run` over manual venv activation here.

**Left unfinished:**
- First Alembic migration not yet generated — needs a live Postgres. `docker compose up -d postgres` was in progress (image pulled, container starting) when the session paused.

**Next session should:**
- Start Postgres, run `alembic revision --autogenerate -m "initial schema"`, verify `alembic upgrade head` applies cleanly.
- Continue Phase 1: mock vacancy generator + `scripts/seed_mock_data.py`, ingestion source interface, Prefect dedup/clean/validate flow, vacancy embeddings into Qdrant, unit tests for the pipeline stages.

---

## Session 2 — 2026-08-15

**Completed — finished all of Phase 1:**
- Generated the first Alembic migration and applied it; all five tables (`candidates`, `skills`, `vacancies`, `candidate_skills`, `vacancy_skill_requirements`) exist and were verified via `\dt`.
- Built `scripts/seed_mock_data.py`: a deterministic (seeded) generator producing 36 realistic vacancies evenly spread across Backend/Data/AI Engineering × Junior/Mid/Senior/Staff, drawn from a 43-skill taxonomy with role-appropriate must-have/nice-to-have pools. Writes `data/mock/vacancies.json` and idempotently seeds Postgres (skills upserted, vacancies replaced).
- Added `ingestion/sources/base.py` (`VacancySource` structural protocol) and `mock_source.py` (reads the JSON fixture, yields validated `Vacancy` objects) — the seam a future real source would implement without changing call sites.
- Added the Prefect ingestion flow (`ingestion/flows/vacancy_ingestion.py`): ingest → dedup → clean → validate → persist → embed. `dedup`/`clean`/`validate` are pure functions in `ingestion/pipelines/` with unit tests; `persist` is `infra/db/repositories/vacancy_repository.upsert_vacancies` (upsert by id, so reruns converge instead of duplicating); `embed` generates BGE embeddings and upserts into Qdrant.
- Added `infra/embeddings/model.py` (`EmbeddingModel` wrapping local sentence-transformers, inference offloaded to a thread via `asyncio.to_thread`) and `infra/vector_store/` (`qdrant_client.py` thin async wrapper, `vacancy_index.py` builds a title+company+description+skills composite per vacancy and upserts to the `vacancies` collection, cosine distance).
- Verified the full pipeline end-to-end against live Postgres and Qdrant: flow run is idempotent (rerunning leaves 36 rows/points, not 72), and a semantic query for "LLM-powered agents with LangChain and PyTorch" correctly ranked AI Engineering postings highest.
- All new code passes `ruff check`, `ruff format`, and `mypy --strict`; 11 unit tests pass (`pytest -m unit`).

**Decisions / gotchas:**
- **Postgres port conflict**: a native Postgres.app instance on this Mac was already bound to host port 5432 (`launchctl list | grep postgres` showed `com.postgresapp.Postgres2LoginHelper`), silently shadowing the Docker container's `5432:5432` port mapping — `docker compose ps` showed the container healthy, but `psql`/`alembic` connecting to `localhost:5432` were actually hitting Postgres.app and getting `password authentication failed`. Fixed by remapping the compose file to `${POSTGRES_PORT:-5433}:5432` and updating `.env`/`.env.example`/`config.py`'s default accordingly. Container-to-container traffic (api → `postgres:5432` inside the Docker network) is unaffected — only the host-side port changed. If a future session hits `password authentication failed` against a container that `docker compose ps` shows as healthy, check for a competing local Postgres install before assuming the credentials are wrong.
- **Timezone-naive vs. aware timestamp columns**: the first migration generated `TIMESTAMP WITHOUT TIME ZONE` columns (SQLAlchemy's plain `DateTime` default) for `posted_at`/`ingested_at`/`created_at`, but the domain models use `datetime.now(UTC)` (timezone-aware) throughout. asyncpg rejected binding an aware datetime into a naive column (`can't subtract offset-naive and offset-aware datetimes`). Fixed by using `DateTime(timezone=True)` in the ORM models and generating a follow-up migration. Worth remembering: any future timestamp column must use `DateTime(timezone=True)` from the start, since the project's convention is UTC-aware datetimes everywhere.
- `uv sync` alone did not install the `dev` extras (pytest, mypy, ruff, factory-boy); needed `uv sync --extra dev` before tests could run at all in this session.
- Design choice: persistence for the ingestion flow lives in `infra/db/repositories/vacancy_repository.py` (upsert-by-id), not inlined in `ingestion/pipelines/`, keeping the pipeline stages pure/I/O-free and matching the ports-and-adapters split even though `ingestion/` itself isn't `domain/`.

**Left unfinished:** nothing in Phase 1 — all items checked off in `todo.md`.

**Next session should:** start Phase 2 — Candidate Onboarding & Parsing: `POST /api/v1/candidates` upload endpoint, LLM-assisted resume parser via the `LLMProvider` abstraction, candidate persistence (Postgres + Qdrant), sample resume fixtures, and parsing pipeline tests.
