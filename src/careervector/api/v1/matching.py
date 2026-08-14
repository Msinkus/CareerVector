from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from careervector.config import get_settings
from careervector.domain.matching.hybrid_retriever import HybridRetriever
from careervector.domain.matching.text import candidate_match_text, vacancy_match_text
from careervector.domain.skills.gap_analysis import SkillGapReport, compute_skill_gap
from careervector.domain.skills.models import SkillImportance
from careervector.domain.vacancies.models import RoleType, SeniorityLevel, Vacancy
from careervector.infra.db.repositories.candidate_repository import get_candidate_by_id
from careervector.infra.db.repositories.vacancy_repository import (
    get_vacancy_by_id,
    list_vacancies,
)
from careervector.infra.db.session import get_session
from careervector.infra.embeddings.model import EmbeddingModel, get_embedding_model
from careervector.infra.matching.dense_retriever import QdrantDenseRetriever
from careervector.infra.matching.reranker import CrossEncoderReranker, get_reranker
from careervector.infra.matching.sparse_retriever import BM25VacancyRetriever

router = APIRouter(prefix="/matching", tags=["matching"])


class MatchRequest(BaseModel):
    candidate_id: UUID
    retrieve_top_k: int = 50
    top_k: int = 10


class VacancyMatchResponse(BaseModel):
    vacancy_id: str
    title: str
    company: str
    role_type: RoleType
    seniority: SeniorityLevel
    match_score: float

    @classmethod
    def from_domain(cls, vacancy: Vacancy, score: float) -> "VacancyMatchResponse":
        return cls(
            vacancy_id=str(vacancy.id),
            title=vacancy.title,
            company=vacancy.company,
            role_type=vacancy.role_type,
            seniority=vacancy.seniority,
            match_score=score,
        )


@router.post("/match", response_model=list[VacancyMatchResponse])
async def match_vacancies(
    request: MatchRequest,
    session: AsyncSession = Depends(get_session),
    embedding_model: EmbeddingModel = Depends(get_embedding_model),
    reranker: CrossEncoderReranker = Depends(get_reranker),
) -> list[VacancyMatchResponse]:
    candidate = await get_candidate_by_id(request.candidate_id, session)
    if candidate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found.")

    vacancies = await list_vacancies(session)
    if not vacancies:
        return []
    vacancy_by_id = {str(vacancy.id): vacancy for vacancy in vacancies}

    query_text = candidate_match_text(candidate)
    query_embedding = (await embedding_model.embed([query_text]))[0]

    hybrid = HybridRetriever(
        dense=QdrantDenseRetriever(get_settings().qdrant_collection_vacancies),
        sparse=BM25VacancyRetriever(
            [(str(vacancy.id), vacancy_match_text(vacancy)) for vacancy in vacancies]
        ),
    )
    fused = await hybrid.retrieve(query_embedding, query_text, top_k=request.retrieve_top_k)

    rerank_input = [
        (item.id, vacancy_match_text(vacancy_by_id[item.id]))
        for item in fused
        if item.id in vacancy_by_id
    ]
    reranked = await reranker.rerank(query_text, rerank_input, top_k=request.top_k)

    return [
        VacancyMatchResponse.from_domain(vacancy_by_id[item.id], item.score) for item in reranked
    ]


class GapAnalysisRequest(BaseModel):
    candidate_id: UUID
    vacancy_id: UUID


class SkillGapItemResponse(BaseModel):
    skill_id: str
    skill_name: str
    importance: SkillImportance
    min_years_experience: int | None


class SkillGapReportResponse(BaseModel):
    candidate_id: str
    vacancy_id: str
    matched_skills: list[str]
    missing_must_have: list[SkillGapItemResponse]
    missing_nice_to_have: list[SkillGapItemResponse]
    must_have_match_ratio: float

    @classmethod
    def from_domain(cls, report: SkillGapReport) -> "SkillGapReportResponse":
        return cls(
            candidate_id=str(report.candidate_id),
            vacancy_id=str(report.vacancy_id),
            matched_skills=[skill.name for skill in report.matched_skills],
            missing_must_have=[
                SkillGapItemResponse(
                    skill_id=req.skill.id,
                    skill_name=req.skill.name,
                    importance=req.importance,
                    min_years_experience=req.min_years_experience,
                )
                for req in report.missing_must_have
            ],
            missing_nice_to_have=[
                SkillGapItemResponse(
                    skill_id=req.skill.id,
                    skill_name=req.skill.name,
                    importance=req.importance,
                    min_years_experience=req.min_years_experience,
                )
                for req in report.missing_nice_to_have
            ],
            must_have_match_ratio=report.must_have_match_ratio,
        )


@router.post("/gap-analysis", response_model=SkillGapReportResponse)
async def gap_analysis(
    request: GapAnalysisRequest,
    session: AsyncSession = Depends(get_session),
) -> SkillGapReportResponse:
    candidate = await get_candidate_by_id(request.candidate_id, session)
    if candidate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found.")

    vacancy = await get_vacancy_by_id(request.vacancy_id, session)
    if vacancy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vacancy not found.")

    report = compute_skill_gap(candidate, vacancy)
    return SkillGapReportResponse.from_domain(report)
