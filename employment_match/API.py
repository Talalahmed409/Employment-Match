#!/usr/bin/env python3
"""
FastAPI application for Employment Match - Job Application and Skill Matching System
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import tempfile
import shutil
import sys
from datetime import datetime, timedelta

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, EmailStr
import uvicorn
from sqlalchemy.orm import Session
from sqlalchemy import func

# Import our existing modules
from employment_match.extract_skills import extract_skills, load_esco_skills, load_embedder
from employment_match.extract_cv_skills import extract_cv_skills, extract_cv_skills_from_text
from employment_match.match_skills import match_skills as match_skills_func
import employment_match.generate_embeddings

# Import database and auth modules
from employment_match.database import get_db, create_tables, Company, Candidate, JobPosting, Application, SkillMatch
from employment_match.auth import (
    get_password_hash, create_access_token, authenticate_company, authenticate_candidate,
    get_current_company, get_current_candidate, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
)
from employment_match.google_auth import authenticate_google_user

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Employment Match API",
    description="AI-powered job application and skill matching system",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models for request/response
class JobDescriptionRequest(BaseModel):
    job_description: str = Field(..., description="Job description text to extract skills from")
    similarity_threshold: Optional[float] = Field(0.6, description="Threshold for embedding-based matching (0.0-1.0)")
    fuzzy_threshold: Optional[int] = Field(90, description="Threshold for fuzzy matching (0-100)")

class CVTextRequest(BaseModel):
    cv_text: str = Field(..., description="CV text to extract skills from")
    similarity_threshold: Optional[float] = Field(0.4, description="Threshold for embedding-based matching (0.0-1.0)")
    fuzzy_threshold: Optional[int] = Field(90, description="Threshold for fuzzy matching (0-100)")

class SkillMatchRequest(BaseModel):
    cv_skills: List[str] = Field(..., description="List of skills from CV")
    job_skills: List[str] = Field(..., description="List of skills from job description")
    similarity_threshold: Optional[float] = Field(0.3, description="Threshold for embedding-based matching (0.0-1.0)")
    fuzzy_threshold: Optional[int] = Field(80, description="Threshold for fuzzy matching (0-100)")

class SkillsResponse(BaseModel):
    standardized: List[str] = Field(..., description="Standardized skills mapped to ESCO taxonomy")
    raw: List[str] = Field(..., description="Raw skills as extracted from input")

class MatchResponse(BaseModel):
    match_score: float = Field(..., description="Overall match score (0-100)")
    matched_skills: List[Dict[str, Any]] = Field(..., description="List of matched skills with details")
    missing_skills: List[str] = Field(..., description="Skills required but not found in CV")
    extra_skills: List[str] = Field(..., description="Skills in CV but not required for job")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    esco_skills_loaded: bool = Field(..., description="Whether ESCO skills are loaded")
    embeddings_loaded: bool = Field(..., description="Whether embeddings are loaded")
    gemini_configured: bool = Field(..., description="Whether Gemini API is configured")

# New Pydantic models for job application system
class CompanyRegister(BaseModel):
    name: str = Field(..., description="Company name")
    email: EmailStr = Field(..., description="Company email")
    password: str = Field(..., description="Password")
    description: Optional[str] = Field(None, description="Company description")
    website: Optional[str] = Field(None, description="Company website")
    location: Optional[str] = Field(None, description="Company location")
    industry: Optional[str] = Field(None, description="Company industry")

class CompanyLogin(BaseModel):
    email: EmailStr = Field(..., description="Company email")
    password: str = Field(..., description="Password")

class CandidateRegister(BaseModel):
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Location")
    current_title: Optional[str] = Field(None, description="Current job title")
    years_experience: Optional[int] = Field(None, description="Years of experience")

class CandidateLogin(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")

class GoogleAuthRequest(BaseModel):
    token: str = Field(..., description="Google ID token from frontend")
    user_type: str = Field(..., description="User type (company or candidate)")

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type")
    user_type: str = Field(..., description="User type (company or candidate)")
    user_id: int = Field(..., description="User ID")

class JobPostingCreate(BaseModel):
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description")
    requirements: Optional[str] = Field(None, description="Job requirements")
    location: Optional[str] = Field(None, description="Job location")
    salary_min: Optional[int] = Field(None, description="Minimum salary")
    salary_max: Optional[int] = Field(None, description="Maximum salary")
    employment_type: Optional[str] = Field(None, description="Employment type")
    experience_level: Optional[str] = Field(None, description="Experience level")

class JobPostingResponse(BaseModel):
    id: int = Field(..., description="Job posting ID")
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description")
    requirements: Optional[str] = Field(None, description="Job requirements")
    location: Optional[str] = Field(None, description="Job location")
    salary_min: Optional[int] = Field(None, description="Minimum salary")
    salary_max: Optional[int] = Field(None, description="Maximum salary")
    employment_type: Optional[str] = Field(None, description="Employment type")
    experience_level: Optional[str] = Field(None, description="Experience level")
    company_name: str = Field(..., description="Company name")
    created_at: datetime = Field(..., description="Creation date")
    is_active: bool = Field(..., description="Whether job is active")

class ApplicationCreate(BaseModel):
    cover_letter: Optional[str] = Field(None, description="Cover letter")

class ApplicationResponse(BaseModel):
    id: int = Field(..., description="Application ID")
    job_title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    status: str = Field(..., description="Application status")
    applied_at: datetime = Field(..., description="Application date")
    match_score: Optional[float] = Field(None, description="Skill match score")

class ApplicationDetailResponse(BaseModel):
    id: int = Field(..., description="Application ID")
    candidate_name: str = Field(..., description="Candidate name")
    candidate_email: str = Field(..., description="Candidate email")
    job_title: str = Field(..., description="Job title")
    cover_letter: Optional[str] = Field(None, description="Cover letter")
    status: str = Field(..., description="Application status")
    applied_at: datetime = Field(..., description="Application date")
    match_score: Optional[float] = Field(None, description="Skill match score")
    matched_skills: Optional[List[Dict[str, Any]]] = Field(None, description="Matched skills")
    missing_skills: Optional[List[str]] = Field(None, description="Missing skills")
    extra_skills: Optional[List[str]] = Field(None, description="Extra skills")

# New Pydantic models for user profile responses
class CompanyProfileResponse(BaseModel):
    id: int = Field(..., description="Company ID")
    name: str = Field(..., description="Company name")
    email: str = Field(..., description="Company email")
    description: Optional[str] = Field(None, description="Company description")
    website: Optional[str] = Field(None, description="Company website")
    location: Optional[str] = Field(None, description="Company location")
    industry: Optional[str] = Field(None, description="Company industry")
    created_at: datetime = Field(..., description="Account creation date")

class CandidateProfileResponse(BaseModel):
    id: int = Field(..., description="Candidate ID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Location")
    current_title: Optional[str] = Field(None, description="Current job title")
    years_experience: Optional[int] = Field(None, description="Years of experience")
    cv_file_path: Optional[str] = Field(None, description="Path to uploaded CV file")
    extracted_skills: Optional[Dict[str, Any]] = Field(None, description="Extracted skills from CV")
    created_at: datetime = Field(..., description="Account creation date")

# Global variables for loaded models and data
esco_skills = None
embedder = None
sentence_transformer_model = None

@app.on_event("startup")
async def startup_event():
    """Initialize basic setup on startup"""
    global esco_skills, embedder, sentence_transformer_model
    
    # Initialize as None - will load lazily when needed
    esco_skills = None
    embedder = None
    sentence_transformer_model = None
    
    # Create database tables
    create_tables()
    
    logger.info("Startup completed - models will be loaded on first request")

def load_models_if_needed():
    """Load models if they haven't been loaded yet"""
    global esco_skills, embedder, sentence_transformer_model
    
    if esco_skills is None:
        try:
            esco_skills = load_esco_skills("data/esco_skills.json")
            logger.info(f"Loaded {len(esco_skills)} ESCO skills")
        except Exception as e:
            logger.error(f"Error loading ESCO skills: {e}")
            esco_skills = []
    
    if embedder is None:
        try:
            embedder = load_embedder()
            logger.info("Loaded embedder models")
        except Exception as e:
            logger.error(f"Error loading embedder: {e}")
            embedder = None
    
    if sentence_transformer_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            sentence_transformer_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("Loaded sentence transformer model")
        except Exception as e:
            logger.error(f"Error loading sentence transformer: {e}")
            sentence_transformer_model = None

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        esco_skills_loaded=esco_skills is not None and len(esco_skills) > 0,
        embeddings_loaded=os.path.exists("data/esco_embeddings.npy"),
        gemini_configured=bool(os.getenv("GEMINI_API_KEY"))
    )

# Authentication endpoints
@app.post("/register/company", response_model=Token)
async def register_company(company_data: CompanyRegister, db: Session = Depends(get_db)):
    """Register a new company"""
    # Check if email already exists
    existing_company = db.query(Company).filter(Company.email == company_data.email).first()
    if existing_company:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new company
    hashed_password = get_password_hash(company_data.password)
    company = Company(
        name=company_data.name,
        email=company_data.email,
        password_hash=hashed_password,
        description=company_data.description,
        website=company_data.website,
        location=company_data.location,
        industry=company_data.industry
    )
    
    db.add(company)
    db.commit()
    db.refresh(company)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(company.id), "user_type": "company"},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_type="company",
        user_id=int(str(company.id))
    )

@app.post("/register/candidate", response_model=Token)
async def register_candidate(candidate_data: CandidateRegister, db: Session = Depends(get_db)):
    """Register a new candidate"""
    # Check if email already exists
    existing_candidate = db.query(Candidate).filter(Candidate.email == candidate_data.email).first()
    if existing_candidate:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new candidate
    hashed_password = get_password_hash(candidate_data.password)
    candidate = Candidate(
        first_name=candidate_data.first_name,
        last_name=candidate_data.last_name,
        email=candidate_data.email,
        password_hash=hashed_password,
        phone=candidate_data.phone,
        location=candidate_data.location,
        current_title=candidate_data.current_title,
        years_experience=candidate_data.years_experience
    )
    
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(candidate.id), "user_type": "candidate"},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_type="candidate",
        user_id=int(str(candidate.id))
    )

@app.post("/login/company", response_model=Token)
async def login_company(login_data: CompanyLogin, db: Session = Depends(get_db)):
    """Login for company"""
    company = authenticate_company(db, login_data.email, login_data.password)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(company.id), "user_type": "company"},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_type="company",
        user_id=int(str(company.id))
    )

@app.post("/login/candidate", response_model=Token)
async def login_candidate(login_data: CandidateLogin, db: Session = Depends(get_db)):
    """Login for candidate"""
    candidate = authenticate_candidate(db, login_data.email, login_data.password)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(candidate.id), "user_type": "candidate"},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_type="candidate",
        user_id=int(str(candidate.id))
    )

# Google OAuth endpoints
@app.post("/auth/google", response_model=Token)
async def google_auth(auth_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate user with Google OAuth"""
    if auth_data.user_type not in ["company", "candidate"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_type. Must be 'company' or 'candidate'"
        )
    
    # Authenticate with Google
    user = authenticate_google_user(db, auth_data.token, auth_data.user_type)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "user_type": auth_data.user_type},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_type=auth_data.user_type,
        user_id=int(str(user.id))
    )

# User profile endpoints
@app.get("/profile/company", response_model=CompanyProfileResponse)
async def get_company_profile(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Get current company's profile information"""
    return CompanyProfileResponse(
        id=int(str(current_company.id)),
        name=str(current_company.name),
        email=str(current_company.email),
        description=str(current_company.description) if current_company.description is not None else None,
        website=str(current_company.website) if current_company.website is not None else None,
        location=str(current_company.location) if current_company.location is not None else None,
        industry=str(current_company.industry) if current_company.industry is not None else None,
        created_at=current_company.created_at
    )

@app.get("/profile/candidate", response_model=CandidateProfileResponse)
async def get_candidate_profile(
    current_candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Get current candidate's profile information"""
    return CandidateProfileResponse(
        id=int(str(current_candidate.id)),
        first_name=str(current_candidate.first_name),
        last_name=str(current_candidate.last_name),
        email=str(current_candidate.email),
        phone=str(current_candidate.phone) if current_candidate.phone is not None else None,
        location=str(current_candidate.location) if current_candidate.location is not None else None,
        current_title=str(current_candidate.current_title) if current_candidate.current_title is not None else None,
        years_experience=int(str(current_candidate.years_experience)) if current_candidate.years_experience is not None else None,
        cv_file_path=str(current_candidate.cv_file_path) if current_candidate.cv_file_path is not None else None,
        extracted_skills=current_candidate.extracted_skills,
        created_at=current_candidate.created_at
    )

@app.get("/profile/me")
async def get_my_profile(
    current_user: Union[Company, Candidate] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile (works for both companies and candidates)"""
    if isinstance(current_user, Company):
        return CompanyProfileResponse(
            id=int(str(current_user.id)),
            name=str(current_user.name),
            email=str(current_user.email),
            description=str(current_user.description) if current_user.description is not None else None,
            website=str(current_user.website) if current_user.website is not None else None,
            location=str(current_user.location) if current_user.location is not None else None,
            industry=str(current_user.industry) if current_user.industry is not None else None,
            created_at=current_user.created_at
        )
    else:  # Candidate
        return CandidateProfileResponse(
            id=int(str(current_user.id)),
            first_name=str(current_user.first_name),
            last_name=str(current_user.last_name),
            email=str(current_user.email),
            phone=str(current_user.phone) if current_user.phone is not None else None,
            location=str(current_user.location) if current_user.location is not None else None,
            current_title=str(current_user.current_title) if current_user.current_title is not None else None,
            years_experience=int(str(current_user.years_experience)) if current_user.years_experience is not None else None,
            cv_file_path=str(current_user.cv_file_path) if current_user.cv_file_path is not None else None,
            extracted_skills=current_user.extracted_skills,
            created_at=current_user.created_at
        )

# Job posting endpoints
@app.post("/jobs", response_model=JobPostingResponse)
async def create_job_posting(
    job_data: JobPostingCreate,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Create a new job posting"""
    # Extract skills from job description
    load_models_if_needed()
    
    if esco_skills and embedder:
        try:
            skills_result = extract_skills(job_data.description, esco_skills, embedder)
            extracted_skills = skills_result
        except Exception as e:
            logger.error(f"Error extracting skills from job posting: {e}")
            extracted_skills = {"standardized": [], "raw": []}
    else:
        extracted_skills = {"standardized": [], "raw": []}
    
    # Create job posting
    job_posting = JobPosting(
        company_id=current_company.id,
        title=job_data.title,
        description=job_data.description,
        requirements=job_data.requirements,
        location=job_data.location,
        salary_min=job_data.salary_min,
        salary_max=job_data.salary_max,
        employment_type=job_data.employment_type,
        experience_level=job_data.experience_level,
        extracted_skills=extracted_skills
    )
    
    db.add(job_posting)
    db.commit()
    db.refresh(job_posting)
    
    return JobPostingResponse(
        id=int(job_posting.id),
        title=str(job_posting.title),
        description=str(job_posting.description),
        requirements=job_posting.requirements,
        location=job_posting.location,
        salary_min=job_posting.salary_min,
        salary_max=job_posting.salary_max,
        employment_type=job_posting.employment_type,
        experience_level=job_posting.experience_level,
        company_name=str(current_company.name),
        created_at=job_posting.created_at,
        is_active=bool(job_posting.is_active)
    )

@app.get("/jobs", response_model=List[JobPostingResponse])
async def get_job_postings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all active job postings"""
    job_postings = db.query(JobPosting).filter(JobPosting.is_active == True).offset(skip).limit(limit).all()
    
    result = []
    for job in job_postings:
        company = db.query(Company).filter(Company.id == job.company_id).first()
        result.append(JobPostingResponse(
            id=int(job.id),
            title=str(job.title),
            description=str(job.description),
            requirements=job.requirements,
            location=job.location,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            company_name=str(company.name) if company else "Unknown",
            created_at=job.created_at,
            is_active=bool(job.is_active)
        ))
    
    return result

@app.get("/jobs/{job_id}", response_model=JobPostingResponse)
async def get_job_posting(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job posting"""
    job_posting = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job_posting:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    company = db.query(Company).filter(Company.id == job_posting.company_id).first()
    return JobPostingResponse(
        id=int(job_posting.id),
        title=str(job_posting.title),
        description=str(job_posting.description),
        requirements=job_posting.requirements,
        location=job_posting.location,
        salary_min=job_posting.salary_min,
        salary_max=job_posting.salary_max,
        employment_type=job_posting.employment_type,
        experience_level=job_posting.experience_level,
        company_name=str(company.name) if company else "Unknown",
        created_at=job_posting.created_at,
        is_active=bool(job_posting.is_active)
    )

# Application endpoints
@app.post("/jobs/{job_id}/apply", response_model=ApplicationResponse)
async def apply_to_job(
    job_id: int,
    application_data: ApplicationCreate,
    current_candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Apply to a job posting"""
    # Check if job posting exists and is active
    job_posting = db.query(JobPosting).filter(JobPosting.id == job_id, JobPosting.is_active == True).first()
    if not job_posting:
        raise HTTPException(status_code=404, detail="Job posting not found or inactive")
    
    # Check if already applied
    existing_application = db.query(Application).filter(
        Application.candidate_id == current_candidate.id,
        Application.job_posting_id == job_id
    ).first()
    if existing_application:
        raise HTTPException(status_code=400, detail="Already applied to this job")
    
    # Create application
    application = Application(
        candidate_id=current_candidate.id,
        job_posting_id=job_id,
        cover_letter=application_data.cover_letter
    )
    
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Perform skill matching
    load_models_if_needed()
    
    if sentence_transformer_model and current_candidate.extracted_skills and job_posting.extracted_skills:
        try:
            cv_skills = current_candidate.extracted_skills.get("raw", [])
            job_skills = job_posting.extracted_skills.get("raw", [])
            
            if cv_skills and job_skills:
                match_result = match_skills_func(cv_skills, job_skills, sentence_transformer_model)
                
                # Save skill match result
                skill_match = SkillMatch(
                    application_id=application.id,
                    match_score=match_result["match_score"],
                    matched_skills=match_result["matched_skills"],
                    missing_skills=match_result["missing_skills"],
                    extra_skills=match_result["extra_skills"],
                    cv_skills=cv_skills,
                    job_skills=job_skills
                )
                
                db.add(skill_match)
                db.commit()
                
                match_score = match_result["match_score"]
            else:
                match_score = None
        except Exception as e:
            logger.error(f"Error performing skill matching: {e}")
            match_score = None
    else:
        match_score = None
    
    company = db.query(Company).filter(Company.id == job_posting.company_id).first()
    
    return ApplicationResponse(
        id=application.id,
        job_title=job_posting.title,
        company_name=company.name if company else "Unknown",
        status=application.status,
        applied_at=application.applied_at,
        match_score=match_score
    )

@app.get("/applications/my", response_model=List[ApplicationResponse])
async def get_my_applications(
    current_candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Get candidate's applications"""
    applications = db.query(Application).filter(Application.candidate_id == current_candidate.id).all()
    
    result = []
    for app in applications:
        job_posting = db.query(JobPosting).filter(JobPosting.id == app.job_posting_id).first()
        company = db.query(Company).filter(Company.id == job_posting.company_id).first() if job_posting else None
        
        # Get match score
        skill_match = db.query(SkillMatch).filter(SkillMatch.application_id == app.id).first()
        match_score = skill_match.match_score if skill_match else None
        
        result.append(ApplicationResponse(
            id=app.id,
            job_title=job_posting.title if job_posting else "Unknown",
            company_name=company.name if company else "Unknown",
            status=app.status,
            applied_at=app.applied_at,
            match_score=match_score
        ))
    
    return result

@app.get("/applications/company", response_model=List[ApplicationDetailResponse])
async def get_company_applications(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Get applications for company's job postings"""
    # Get all job postings by this company
    job_postings = db.query(JobPosting).filter(JobPosting.company_id == current_company.id).all()
    job_ids = [job.id for job in job_postings]
    
    # Get applications for these jobs
    applications = db.query(Application).filter(Application.job_posting_id.in_(job_ids)).all()
    
    result = []
    for app in applications:
        candidate = db.query(Candidate).filter(Candidate.id == app.candidate_id).first()
        job_posting = db.query(JobPosting).filter(JobPosting.id == app.job_posting_id).first()
        skill_match = db.query(SkillMatch).filter(SkillMatch.application_id == app.id).first()
        
        result.append(ApplicationDetailResponse(
            id=app.id,
            candidate_name=f"{candidate.first_name} {candidate.last_name}" if candidate else "Unknown",
            candidate_email=candidate.email if candidate else "Unknown",
            job_title=job_posting.title if job_posting else "Unknown",
            cover_letter=app.cover_letter,
            status=app.status,
            applied_at=app.applied_at,
            match_score=skill_match.match_score if skill_match else None,
            matched_skills=skill_match.matched_skills if skill_match else None,
            missing_skills=skill_match.missing_skills if skill_match else None,
            extra_skills=skill_match.extra_skills if skill_match else None
        ))
    
    return result

@app.put("/applications/{application_id}/status")
async def update_application_status(
    application_id: int,
    status: str = Form(..., description="New status"),
    notes: Optional[str] = Form(None, description="Notes"),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Update application status (company only)"""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if this application is for a job posted by the current company
    job_posting = db.query(JobPosting).filter(JobPosting.id == application.job_posting_id).first()
    if not job_posting or job_posting.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this application")
    
    application.status = status
    application.notes = notes
    application.reviewed_at = datetime.utcnow()
    application.reviewed_by = current_company.id
    
    db.commit()
    
    return {"message": "Application status updated successfully"}

@app.get("/jobs/{job_id}/top-candidates", response_model=List[ApplicationDetailResponse])
async def get_top_candidates_for_job(
    job_id: int,
    limit: int = 10,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Get top candidates by match score for a specific job posting (company only)"""
    # Check if job posting exists and belongs to the company
    job_posting = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job_posting:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    if job_posting.company_id != current_company.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job's applications")
    
    # Get applications for this job with skill matches, ordered by match score
    applications = db.query(Application, SkillMatch).join(
        SkillMatch, Application.id == SkillMatch.application_id, isouter=True
    ).filter(
        Application.job_posting_id == job_id
    ).order_by(
        SkillMatch.match_score.desc().nullslast()
    ).limit(limit).all()
    
    result = []
    for app, skill_match in applications:
        candidate = db.query(Candidate).filter(Candidate.id == app.candidate_id).first()
        
        result.append(ApplicationDetailResponse(
            id=app.id,
            candidate_name=f"{candidate.first_name} {candidate.last_name}" if candidate else "Unknown",
            candidate_email=candidate.email if candidate else "Unknown",
            job_title=job_posting.title,
            cover_letter=app.cover_letter,
            status=app.status,
            applied_at=app.applied_at,
            match_score=skill_match.match_score if skill_match else None,
            matched_skills=skill_match.matched_skills if skill_match else None,
            missing_skills=skill_match.missing_skills if skill_match else None,
            extra_skills=skill_match.extra_skills if skill_match else None
        ))
    
    return result

# CV upload and skill extraction endpoints
@app.post("/upload-cv")
async def upload_cv(
    file: UploadFile = File(..., description="CV PDF file"),
    current_candidate: Candidate = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Upload and process CV for skill extraction"""
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    load_models_if_needed()
    
    if not esco_skills or not embedder:
        raise HTTPException(status_code=500, detail="Models not properly loaded")
    
    # Save uploaded file
    upload_dir = Path("uploads/cvs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"cv_{current_candidate.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Extract skills from CV
        skills = extract_cv_skills(str(file_path), esco_skills, embedder)
        
        # Update candidate's CV information
        current_candidate.cv_file_path = str(file_path)
        current_candidate.extracted_skills = skills
        db.commit()
        
        return {
            "message": "CV uploaded and processed successfully",
            "skills": skills
        }
        
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Error processing CV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Keep existing skill extraction endpoints for backward compatibility
@app.post("/extract-job-skills", response_model=SkillsResponse)
async def extract_job_skills(request: JobDescriptionRequest):
    """Extract skills from job description"""
    try:
        load_models_if_needed()
        
        if not esco_skills or not embedder:
            raise HTTPException(status_code=500, detail="Models not properly loaded")
        
        # Temporarily update thresholds
        from employment_match.extract_skills import SIMILARITY_THRESHOLD, FUZZY_THRESHOLD
        original_sim_threshold = SIMILARITY_THRESHOLD
        original_fuzzy_threshold = FUZZY_THRESHOLD
        
        # Update thresholds if provided
        if request.similarity_threshold is not None:
            import employment_match.extract_skills as skills_module
            skills_module.SIMILARITY_THRESHOLD = request.similarity_threshold
        if request.fuzzy_threshold is not None:
            import employment_match.extract_skills as skills_module
            skills_module.FUZZY_THRESHOLD = request.fuzzy_threshold
        
        try:
            skills = extract_skills(request.job_description, esco_skills, embedder)
        finally:
            # Restore original thresholds
            import employment_match.extract_skills as skills_module
            skills_module.SIMILARITY_THRESHOLD = original_sim_threshold
            skills_module.FUZZY_THRESHOLD = original_fuzzy_threshold
        
        return SkillsResponse(**skills)
        
    except Exception as e:
        logger.error(f"Error extracting job skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract-cv-skills-text", response_model=SkillsResponse)
async def extract_cv_skills_text(request: CVTextRequest):
    """Extract skills from CV text"""
    try:
        load_models_if_needed()
        
        if not esco_skills or not embedder or not sentence_transformer_model:
            raise HTTPException(status_code=500, detail="Models not properly loaded")
        
        # Temporarily update thresholds
        from employment_match.extract_cv_skills import SIMILARITY_THRESHOLD, FUZZY_THRESHOLD
        original_sim_threshold = SIMILARITY_THRESHOLD
        original_fuzzy_threshold = FUZZY_THRESHOLD
        
        # Update thresholds if provided
        if request.similarity_threshold is not None:
            import employment_match.extract_cv_skills as cv_module
            cv_module.SIMILARITY_THRESHOLD = request.similarity_threshold
        if request.fuzzy_threshold is not None:
            import employment_match.extract_cv_skills as cv_module
            cv_module.FUZZY_THRESHOLD = request.fuzzy_threshold
        
        try:
            skills = extract_cv_skills_from_text(request.cv_text, esco_skills, embedder)
        finally:
            # Restore original thresholds
            import employment_match.extract_cv_skills as cv_module
            cv_module.SIMILARITY_THRESHOLD = original_sim_threshold
            cv_module.FUZZY_THRESHOLD = original_fuzzy_threshold
        
        return SkillsResponse(**skills)
        
    except Exception as e:
        logger.error(f"Error extracting CV skills from text: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/match-skills", response_model=MatchResponse)
async def match_skills(request: SkillMatchRequest):
    """Match CV skills against job skills"""
    try:
        load_models_if_needed()
        
        if not sentence_transformer_model:
            raise HTTPException(status_code=500, detail="Sentence transformer model not loaded")
        
        # Temporarily update thresholds
        from employment_match.match_skills import SIMILARITY_THRESHOLD, FUZZY_THRESHOLD
        original_sim_threshold = SIMILARITY_THRESHOLD
        original_fuzzy_threshold = FUZZY_THRESHOLD
        
        # Update thresholds if provided
        if request.similarity_threshold is not None:
            import employment_match.match_skills as match_module
            match_module.SIMILARITY_THRESHOLD = request.similarity_threshold
        if request.fuzzy_threshold is not None:
            import employment_match.match_skills as match_module
            match_module.FUZZY_THRESHOLD = request.fuzzy_threshold
        
        try:
            result = match_skills_func(request.cv_skills, request.job_skills, sentence_transformer_model)
        finally:
            # Restore original thresholds
            import employment_match.match_skills as match_module
            match_module.SIMILARITY_THRESHOLD = original_sim_threshold
            match_module.FUZZY_THRESHOLD = original_fuzzy_threshold
        
        return MatchResponse(**result)
        
    except Exception as e:
        logger.error(f"Error matching skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/setup-data", response_model=Dict[str, str])
async def setup_data(background_tasks: BackgroundTasks):
    """Setup ESCO data and generate embeddings (runs in background)"""
    try:
        # Check if we have the necessary data files
        has_json = os.path.exists("data/esco_skills.json")
        has_embeddings = os.path.exists("data/esco_embeddings.npy")
        has_csv = os.path.exists("data/skills_en.csv")
        
        if not has_json and not has_csv:
            raise HTTPException(status_code=400, detail="Neither esco_skills.json nor skills_en.csv found in data/ directory")
        
        # Run setup in background
        background_tasks.add_task(run_data_setup)
        
        return {"message": "Data setup started in background. Check logs for progress."}
        
    except Exception as e:
        logger.error(f"Error starting data setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_data_setup():
    """Background task to setup ESCO data and embeddings"""
    try:
        logger.info("Starting data setup...")
        
        # Convert ESCO CSV to JSON
        if not os.path.exists("data/esco_skills.json"):
            logger.info("Converting ESCO CSV to JSON...")
            # Execute the conversion script
            import subprocess
            subprocess.run([sys.executable, "employment_match/convert_esco_to_json.py"], check=True)
        
        # Generate embeddings
        if not os.path.exists("data/esco_embeddings.npy"):
            logger.info("Generating ESCO embeddings...")
            # Execute the embedding generation script
            import subprocess
            subprocess.run([sys.executable, "employment_match/generate_embeddings.py"], check=True)
        
        logger.info("Data setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error in data setup: {e}")

@app.get("/esco-skills", response_model=Dict[str, Any])
async def get_esco_skills_info():
    """Get information about loaded ESCO skills"""
    try:
        if not esco_skills:
            raise HTTPException(status_code=500, detail="ESCO skills not loaded")
        
        return {
            "total_skills": len(esco_skills),
            "sample_skills": esco_skills[:5] if len(esco_skills) > 5 else esco_skills,
            "embeddings_available": os.path.exists("data/esco_embeddings.npy")
        }
        
    except Exception as e:
        logger.error(f"Error getting ESCO skills info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class JobPostingWithCountResponse(JobPostingResponse):
    application_count: int = Field(..., description="Number of applications received for this job")

@app.get("/company/jobs", response_model=List[JobPostingWithCountResponse])
async def get_company_jobs(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Get all jobs posted by the current company, with application counts"""
    # Get all jobs for this company
    jobs = db.query(JobPosting).filter(JobPosting.company_id == current_company.id).all()
    job_ids = [job.id for job in jobs]
    
    # Get application counts for all jobs in one query
    application_counts = dict(
        db.query(Application.job_posting_id, func.count(Application.id))
        .filter(Application.job_posting_id.in_(job_ids))
        .group_by(Application.job_posting_id)
        .all()
    ) if job_ids else {}

    result = []
    for job in jobs:
        result.append(JobPostingWithCountResponse(
            id=int(job.id),
            title=str(job.title),
            description=str(job.description),
            requirements=job.requirements,
            location=job.location,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            company_name=str(current_company.name),
            created_at=job.created_at,
            is_active=bool(job.is_active),
            application_count=application_counts.get(job.id, 0)
        ))
    return result

if __name__ == "__main__":
    uvicorn.run(
        "API:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    ) 