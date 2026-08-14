# CareerVector

**AI-Powered Job Market & Skill Gap Intelligence Platform**

CareerVector bridges raw, dynamic job market vacancy data with candidate profiles by computing precise skill distance metrics, detecting market skill trends, generating step-by-step learning roadmaps, and providing real-time AI copilot capabilities — built as a flagship portfolio project demonstrating senior-level Backend, Data, and AI Engineering competency.

---

## Problem Statement

Technical job seekers (Backend, Data, AI Engineering) face three compounding problems:

1. **Blind application submissions.** Traditional ATS tools give a static, keyword-matching score for one document against one job posting, missing broader context and semantic equivalence.
2. **Dynamic skill drift.** Fast-evolving technologies mean job requirements shift rapidly. Candidates spend months on generic courses rather than targeting the specific micro-skills currently in demand.
3. **Reactive job hunting.** Candidates manually browse job boards, analyze requirements, and adapt their resumes — usually after hundreds of other applicants already have.

There is no accessible tool that combines **precise, explainable skill-gap measurement** with **personalized, ordered learning guidance**, delivered through an interface that feels real-time rather than a static report.

## Solution Overview

CareerVector closes that loop end-to-end:

- **Ingest** vacancy data through a decoupled pipeline (mock data today, pluggable live scrapers/streams later) into standardized, validated schemas.
- **Parse** unstructured candidate input (resumes, markdown, free text) into the same structured skill representation used for vacancies.
- **Match** candidate ↔ vacancy using hybrid retrieval — dense embeddings for semantic similarity, sparse keyword search for exact-term precision, reranked by a cross-encoder — then apply **deterministic set-difference logic** on top to separate must-have gaps from nice-to-have gaps, rather than returning an opaque score.
- **Synthesize** a step-by-step learning roadmap, tailored resume bullets, and an interview prep kit via a multi-agent LLM pipeline (parsing agent → gap-analysis agent → roadmap agent), continuously graded by an automated eval framework (faithfulness, context precision, answer relevance).
- **Serve** all of this through a resilient API with real-time streaming (SSE), rate limiting, structured errors, and health/metrics endpoints — built like something that would actually run in production.

The deterministic-logic-plus-LLM-plus-evals combination is the core differentiator: knowing where to use hard business logic (skill set-diff) versus where to use an LLM (synthesis, parsing) versus how to keep the LLM honest (evals) is exactly the judgment senior AI/backend/data roles hire for.

## Why This Exists

A sophisticated user can already paste a resume and a job description into an LLM chat and get a reasonable one-off gap analysis. CareerVector isn't competing on "can an LLM do this comparison" — it already can. It's built on everything a single chat session can't do:

- **One-to-market, not one-to-one.** Compares a candidate against an entire ingested vacancy corpus at once, producing aggregate signal ("73% of matching roles now require Kafka") that no one pastes 200 job descriptions into a chat window to get.
- **Deterministic, not vibes-based.** Every vacancy and candidate runs through the same structured skill taxonomy; a Python set-difference — not a re-prompted LLM — decides what's missing, so results are comparable and rankable across hundreds of listings.
- **Persistent context, not re-explained every time.** A candidate profile is parsed once and reused everywhere; updating one project instantly and correctly affects every future comparison.
- **Push, not pull.** A background watchdog surfaces new high-match opportunities without the candidate re-running anything.
- **Verified, not unverified.** An eval layer (Ragas faithfulness / context precision) grounds the roadmap and gap analysis in the candidate's real profile rather than the model's optimism.

## Core Capabilities

1. **Data Ingestion & Vacancy Foundation** — standardized schemas for technical roles, decoupled ingestion (mock today, live-source-ready), data quality pipelines (dedup, cleaning, schema validation).
2. **Candidate Profile Onboarding** — unstructured resume/text ingestion parsed into structured semantic profiles.
3. **Hybrid Matching & Skill Gap Engine** — dense + sparse retrieval with reranking, deterministic must-have/nice-to-have gap logic.
4. **Autonomous Agentic Copilot & Evals** — multi-agent orchestration (parsing, gap analysis, roadmap synthesis) with continuous LLM-quality evaluation.
5. **API & Real-Time Streaming Layer** — high-concurrency REST + SSE streaming, dynamic rate limiting, structured error handling, health/metrics.

## Architecture

```
[ Mock Vacancy Source ] ---> [ Prefect: dedup/clean/validate ] ---> [ PostgreSQL + Qdrant ]
        (pluggable to a live scraper/stream later without rearchitecting)
                                                                          |
[ Candidate Resume ] ---> [ LLM Parser ] ---> [ FastAPI Backend ] <------+
                                                    |
                                                    +---> [ Hybrid Retriever: Qdrant dense+sparse -> cross-encoder rerank ]
                                                    |
                                                    +---> [ LangGraph Agents: Parse -> Gap-Analyze -> Roadmap-Synthesize ]
                                                    |
                                                    +---> [ Celery + Redis beat: Watchdog polling ]
                                                    |
                                                    +---> [ SSE streaming to client ]
```

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| API framework | FastAPI + Pydantic v2 (Python 3.12) | Async-native, typed contracts end-to-end, auto OpenAPI docs |
| Structured DB | PostgreSQL + SQLAlchemy 2.0 (async) + Alembic | Transactional system of record for candidates/vacancies/skills |
| Vector store | Qdrant | Native hybrid (dense+sparse) search in one query — the core matching engine |
| Embeddings | sentence-transformers / BGE (local) | Zero marginal cost; swappable for a hosted embeddings API later |
| Reranking | Cross-encoder (sentence-transformers, local) | Sharpens top-K precision before results reach the LLM agents |
| Cache / rate limit / broker | Redis | Token-bucket rate limiting, hot-query caching, SSE fan-out, Celery broker |
| Agent orchestration | LangGraph | Explicit, inspectable multi-agent state graph |
| Data pipeline orchestration | Prefect | Orchestrates ingest → dedup → clean → validate, decoupled from agent logic |
| Background jobs / watchdog | Celery + Redis (beat scheduling) | Lightweight periodic polling/diffing/alerting — no Temporal, avoids a second stateful cluster for what is fundamentally scheduled polling |
| LLM provider | Anthropic Claude (`claude-sonnet-5` default) via provider abstraction | Structured output support, 1M context, prompt caching, tool-use API fits LangGraph directly |
| Evals | Ragas | Faithfulness / context precision / answer relevance as first-class scorers |
| Streaming | SSE (FastAPI `StreamingResponse`) | Token-by-token copilot output, simplest tool for one-directional streaming |
| Resilience | slowapi/Redis rate limiting, structlog, Prometheus client | `/healthz`, `/metrics`, structured logs |
| Testing | pytest, pytest-asyncio, httpx, factory_boy | Standard async-Python test stack |
| Packaging | uv | Fast, modern dependency management |
| Containerization | Docker + docker-compose | One-command local stack: Postgres, Qdrant, Redis, API |

## Quickstart

```bash
cp .env.example .env
docker compose up -d
uv sync
uv run alembic upgrade head
uv run python scripts/seed_mock_data.py
uv run uvicorn careervector.main:app --reload
```

API docs at `http://localhost:8000/docs`. SSE demo page at `http://localhost:8000/static/copilot-demo.html`.

## Skills Demonstrated

**Data Engineering** — ETL pipeline orchestration (Prefect), data quality (dedup, schema validation), structured + vector dual persistence, resilient scheduled ingestion.

**AI Engineering** — stateful multi-agent workflows (LangGraph), hybrid retrieval + reranking, structured output / guardrails via Pydantic, continuous LLM evaluation (Ragas).

**Backend Engineering** — async API design (FastAPI), background task orchestration (Celery), real-time streaming (SSE), distributed caching and rate limiting (Redis), observability (structlog, Prometheus).

## Path to Production Scale

The following are deliberately **documented, not built**, to keep this project buildable and demoable rather than stalled on infrastructure plumbing a mock-data portfolio project can't meaningfully exercise:

- **Apache Kafka** — would replace the mock ingestion source's polling with a durable, high-throughput event stream buffering scraped listings before processing.
- **Apache Flink** — would run real-time deduplication (e.g. Locality-Sensitive Hashing) and cleaning over the Kafka stream, replacing the batch Prefect pipeline for live traffic.
- **Apache Iceberg** (on S3/MinIO) — would store historical vacancy data as an open table format for time-travel queries and hiring-trend analytics.
- **Temporal.io** — would replace Celery + Redis beat if the watchdog grew into long-running, stateful, multi-step workflows needing durable execution guarantees beyond periodic polling.
- **Distributed scraping (Playwright/Scrapy)** — would replace the mock/pluggable ingestion source with live job-board scraping, subject to each site's terms of service.

The ingestion layer already sits behind an abstract source interface (`src/careervector/ingestion/sources/base.py`) specifically so any of the above can be dropped in later without touching the domain or API layers.

## License

TBD.
