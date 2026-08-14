from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from careervector.domain.candidates.models import Candidate
from careervector.domain.vacancies.models import RoleType
from careervector.infra.db.repositories.candidate_repository import create_candidate
from careervector.infra.db.repositories.skill_repository import list_skills
from careervector.infra.db.session import get_session
from careervector.infra.embeddings.model import EmbeddingModel, get_embedding_model
from careervector.infra.llm.client import LLMProvider, get_llm_provider
from careervector.infra.vector_store.candidate_index import index_candidate
from careervector.parsing.resume_parser import parse_resume

router = APIRouter(prefix="/candidates", tags=["candidates"])


class CandidateSkillResponse(BaseModel):
    skill_id: str
    skill_name: str
    years_experience: float | None
    proficiency: str | None


class CandidateResponse(BaseModel):
    id: str
    full_name: str
    email: str | None
    summary: str | None
    skills: list[CandidateSkillResponse]
    total_years_experience: float | None
    target_role_type: RoleType | None

    @classmethod
    def from_domain(cls, candidate: Candidate) -> "CandidateResponse":
        return cls(
            id=str(candidate.id),
            full_name=candidate.full_name,
            email=candidate.email,
            summary=candidate.summary,
            skills=[
                CandidateSkillResponse(
                    skill_id=cs.skill.id,
                    skill_name=cs.skill.name,
                    years_experience=cs.years_experience,
                    proficiency=cs.proficiency.value if cs.proficiency else None,
                )
                for cs in candidate.skills
            ],
            total_years_experience=candidate.total_years_experience,
            target_role_type=candidate.target_role_type,
        )


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def upload_candidate(
    resume: UploadFile,
    session: AsyncSession = Depends(get_session),
    llm: LLMProvider = Depends(get_llm_provider),
    embedding_model: EmbeddingModel = Depends(get_embedding_model),
) -> CandidateResponse:
    raw_bytes = await resume.read()
    if not raw_bytes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Uploaded resume is empty.")
    raw_text = raw_bytes.decode("utf-8", errors="ignore")

    known_skills = await list_skills(session)
    candidate = await parse_resume(raw_text, known_skills, llm)

    await create_candidate(candidate, session)
    await index_candidate(candidate, embedding_model)

    return CandidateResponse.from_domain(candidate)
