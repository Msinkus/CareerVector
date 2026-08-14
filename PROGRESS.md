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
