from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index, JSON,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    url = Column(String)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    location = Column(String)
    remote_type = Column(String)
    employment_type = Column(String)
    description_raw = Column(Text)
    description_clean = Column(Text)
    date_posted = Column(DateTime)
    date_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    comp_min = Column(Float)
    comp_max = Column(Float)
    comp_currency = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external_id"),
        Index("ix_jobs_url", "url"),
    )


class CanonicalJob(Base):
    __tablename__ = "canonical_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    location = Column(String)
    remote_type = Column(String)
    description_clean = Column(Text)
    apply_url_best = Column(String)
    comp_min = Column(Float)
    comp_max = Column(Float)
    comp_currency = Column(String, default="USD")
    fingerprint = Column(String, unique=True, nullable=False)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    variants = relationship("JobVariant", back_populates="canonical_job")
    features = relationship("JobFeature", back_populates="canonical_job", uselist=False)
    scores = relationship("JobScore", back_populates="canonical_job")
    action = relationship("JobAction", back_populates="canonical_job", uselist=False)


class JobVariant(Base):
    __tablename__ = "job_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_job_id = Column(Integer, ForeignKey("canonical_jobs.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    source = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    url = Column(String)
    date_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    canonical_job = relationship("CanonicalJob", back_populates="variants")


class JobFeature(Base):
    __tablename__ = "job_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_job_id = Column(Integer, ForeignKey("canonical_jobs.id"), unique=True, nullable=False)
    tech_tags = Column(ARRAY(Text), default=list)
    seniority = Column(String)
    remote_flag = Column(String)
    extracted_json = Column(JSON)

    canonical_job = relationship("CanonicalJob", back_populates="features")


class JobEmbedding(Base):
    __tablename__ = "job_embeddings"

    canonical_job_id = Column(Integer, ForeignKey("canonical_jobs.id"), primary_key=True)
    embedding = Column(Vector(1536))


class ProfileVersion(Base):
    __tablename__ = "profile_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class JobScore(Base):
    __tablename__ = "job_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_job_id = Column(Integer, ForeignKey("canonical_jobs.id"), nullable=False)
    profile_version_id = Column(Integer, ForeignKey("profile_versions.id"), nullable=False)
    score_total = Column(Float, nullable=False)
    score_breakdown_json = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    canonical_job = relationship("CanonicalJob", back_populates="scores")


class JobAction(Base):
    __tablename__ = "job_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_job_id = Column(Integer, ForeignKey("canonical_jobs.id"), unique=True, nullable=False)
    status = Column(String, default="NEW")
    notes = Column(Text)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    canonical_job = relationship("CanonicalJob", back_populates="action")
