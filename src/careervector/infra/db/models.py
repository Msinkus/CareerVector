from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from careervector.domain.skills.models import ProficiencyLevel, SkillCategory, SkillImportance
from careervector.domain.vacancies.models import RoleType, SeniorityLevel
from careervector.infra.db.base import Base


class SkillORM(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    category: Mapped[SkillCategory] = mapped_column(SAEnum(SkillCategory), nullable=False)


class VacancyORM(Base):
    __tablename__ = "vacancies"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(nullable=False)
    company: Mapped[str] = mapped_column(nullable=False)
    role_type: Mapped[RoleType] = mapped_column(SAEnum(RoleType), nullable=False)
    seniority: Mapped[SeniorityLevel] = mapped_column(SAEnum(SeniorityLevel), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(nullable=True)
    remote: Mapped[bool] = mapped_column(default=False)
    source: Mapped[str] = mapped_column(nullable=False)
    source_url: Mapped[str | None] = mapped_column(nullable=True)
    posted_at: Mapped[datetime] = mapped_column(nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    skill_requirements: Mapped[list["VacancySkillRequirementORM"]] = relationship(
        back_populates="vacancy", cascade="all, delete-orphan"
    )


class VacancySkillRequirementORM(Base):
    __tablename__ = "vacancy_skill_requirements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    vacancy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), nullable=False)
    importance: Mapped[SkillImportance] = mapped_column(SAEnum(SkillImportance), nullable=False)
    min_years_experience: Mapped[int | None] = mapped_column(nullable=True)

    vacancy: Mapped[VacancyORM] = relationship(back_populates="skill_requirements")
    skill: Mapped[SkillORM] = relationship()


class CandidateORM(Base):
    __tablename__ = "candidates"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str | None] = mapped_column(nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_role_type: Mapped[RoleType | None] = mapped_column(SAEnum(RoleType), nullable=True)
    raw_resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    skills: Mapped[list["CandidateSkillORM"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )


class CandidateSkillORM(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    candidate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), nullable=False)
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    proficiency: Mapped[ProficiencyLevel | None] = mapped_column(
        SAEnum(ProficiencyLevel), nullable=True
    )

    candidate: Mapped[CandidateORM] = relationship(back_populates="skills")
    skill: Mapped[SkillORM] = relationship()
