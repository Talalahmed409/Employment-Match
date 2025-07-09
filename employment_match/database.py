#!/usr/bin/env python3
"""
Database models and configuration for Employment Match system
"""

import os
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://employment_user:password123@localhost:5432/employment_match")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

class Company(Base):
    """Company/Employer model"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    industry = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    google_id = Column(String(255), nullable=True, unique=True, index=True)  # Google OAuth ID
    is_google_user = Column(Boolean, default=False)  # Flag for Google OAuth users
    
    # Relationships
    job_postings = relationship("JobPosting", back_populates="company", cascade="all, delete-orphan")

class Candidate(Base):
    """Job seeker model"""
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    current_title = Column(String(255), nullable=True)
    years_experience = Column(Integer, nullable=True)
    cv_file_path = Column(String(500), nullable=True)
    cv_text = Column(Text, nullable=True)
    extracted_skills = Column(JSON, nullable=True)  # Store standardized skills
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    google_id = Column(String(255), nullable=True, unique=True, index=True)  # Google OAuth ID
    is_google_user = Column(Boolean, default=False)  # Flag for Google OAuth users
    
    # Relationships
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")

class JobPosting(Base):
    """Job posting model"""
    __tablename__ = "job_postings"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    employment_type = Column(String(50), nullable=True)  # full-time, part-time, contract, etc.
    experience_level = Column(String(50), nullable=True)  # entry, mid, senior, etc.
    extracted_skills = Column(JSON, nullable=True)  # Store standardized skills
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    company = relationship("Company", back_populates="job_postings")
    applications = relationship("Application", back_populates="job_posting", cascade="all, delete-orphan")

class Application(Base):
    """Job application model"""
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    cover_letter = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, reviewed, shortlisted, rejected, hired
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("companies.id"), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="applications")
    job_posting = relationship("JobPosting", back_populates="applications")
    skill_match = relationship("SkillMatch", back_populates="application", uselist=False, cascade="all, delete-orphan")

class SkillMatch(Base):
    """Skill matching results for applications"""
    __tablename__ = "skill_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    match_score = Column(Float, nullable=False)  # Overall match percentage
    matched_skills = Column(JSON, nullable=True)  # List of matched skills with details
    missing_skills = Column(JSON, nullable=True)  # List of missing skills
    extra_skills = Column(JSON, nullable=True)  # List of extra skills
    cv_skills = Column(JSON, nullable=True)  # Skills extracted from CV
    job_skills = Column(JSON, nullable=True)  # Skills extracted from job posting
    similarity_threshold = Column(Float, nullable=True)  # Threshold used for matching
    fuzzy_threshold = Column(Integer, nullable=True)  # Fuzzy threshold used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    application = relationship("Application", back_populates="skill_match")

# Database dependency
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

# Drop all tables (for testing/reset)
def drop_tables():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine) 