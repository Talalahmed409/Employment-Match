"""
HR Assistant Module for FastAPI Integration
Provides AI-powered HR assistant functionality for companies
"""

import uuid
import requests
import chromadb
import google.generativeai as genai
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Union
from chromadb.utils import embedding_functions
from collections import defaultdict
import os
import tempfile
import shutil
import re
import logging

logger = logging.getLogger(__name__)

# Pydantic models for HR assistant
class Job(BaseModel):
    id: str = Field(..., description="Job ID")
    title: str
    description: str = ""
    skills: List[str] = []
    application_count: Optional[int] = None
    
    @validator('id', pre=True)
    def convert_id_to_string(cls, v):
        """Convert integer IDs to strings"""
        return str(v) if v is not None else None

class Application(BaseModel):
    id: str = Field(..., description="Application ID")
    job_id: Optional[str] = None
    job_title: Optional[str] = None
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    status: str = "pending"
    match_score: Optional[float] = None
    cover_letter: Optional[str] = None
    applied_at: Optional[str] = None
    matched_skills: Optional[List[Dict]] = None
    missing_skills: Optional[List[str]] = None
    extra_skills: Optional[List[str]] = None
    
    class Config:
        extra = "ignore"
    
    @validator('id', 'job_id', 'candidate_id', pre=True)
    def convert_ids_to_string(cls, v):
        """Convert integer IDs to strings"""
        return str(v) if v is not None else None

class HRAssistant:
    """HR Assistant for companies to manage applications and get AI insights"""
    
    def __init__(self, api_base_url: str = "http://localhost:8080"):
        self.api_base_url = api_base_url
        self.vector_db = None
        self.chroma_client = None
        self.job_dict = {}
        self.gemini_configured = False
        self.temp_dir = None
        self.applications = []
        self.jobs_from_applications = {}
        
        # Initialize embedding function
        try:
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize embedding function: {e}")
            self.embedding_function = None
    
    def configure_gemini(self, api_key: str) -> bool:
        """Configure Gemini AI with API key"""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('models/gemini-2.5-pro')
            test_response = self.model.generate_content("Test connection")
            if test_response.text:
                logger.info("✅ Gemini configured successfully")
                self.gemini_configured = True
                return True
        except Exception as e:
            logger.error(f"❌ Gemini setup failed: {str(e)}")
            return False
    
    def initialize_company_data(self, company_id: str, db_session=None) -> bool:
        """Initialize company data using company ID and database session"""
        try:
            self.company_id = company_id
            self.session_id = str(uuid.uuid4())
            self.db_session = db_session
            
            # Initialize ChromaDB
            self._cleanup_chromadb()
            self.temp_dir = tempfile.mkdtemp(prefix=f"chroma_hr_{self.session_id}_")
            self.chroma_client = chromadb.PersistentClient(path=self.temp_dir)
            logger.info("✅ ChromaDB initialized successfully")
            
            # Load data
            self._load_applications()
            self._load_jobs()
            self._setup_vector_db()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize company data: {e}")
            return False
    
    def _load_applications_from_db(self):
        """Load applications from database"""
        if not self.db_session:
            return []
            
        try:
            # Import database models
            from employment_match.database import Application, JobPosting, Candidate
            
            # Get all job postings for this company
            job_postings = self.db_session.query(JobPosting).filter(
                JobPosting.company_id == self.company_id
            ).all()
            
            job_ids = [job.id for job in job_postings]
            
            # Get applications for these jobs
            applications = self.db_session.query(Application).filter(
                Application.job_posting_id.in_(job_ids)
            ).all()
            
            return applications
        except Exception as e:
            logger.error(f"Error loading applications from database: {e}")
            return []
    
    def _cleanup_chromadb(self):
        """Clean up ChromaDB resources"""
        try:
            if hasattr(self, 'chroma_client') and self.chroma_client:
                try:
                    self.chroma_client.reset()
                except:
                    pass
                self.chroma_client = None
            
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
                self.temp_dir = None
        except Exception as e:
            logger.warning(f"ChromaDB cleanup warning: {str(e)}")
    
    def _load_applications(self):
        """Load applications from database"""
        try:
            # Import database models
            from employment_match.database import Application as DBApplication, JobPosting, Candidate, SkillMatch
            
            # Get all job postings for this company
            job_postings = self.db_session.query(JobPosting).filter(
                JobPosting.company_id == self.company_id
            ).all()
            
            job_ids = [job.id for job in job_postings]
            
            # Get applications for these jobs with candidates
            applications = self.db_session.query(DBApplication, Candidate, JobPosting, SkillMatch).join(
                Candidate, DBApplication.candidate_id == Candidate.id
            ).join(
                JobPosting, DBApplication.job_posting_id == JobPosting.id
            ).outerjoin(
                SkillMatch, DBApplication.id == SkillMatch.application_id
            ).filter(
                DBApplication.job_posting_id.in_(job_ids)
            ).all()
            
            processed_applications = []
            job_titles_from_apps = set()
            
            for app, candidate, job, skill_match in applications:
                try:
                    # Create standardized application data
                    app_data = {
                        "id": str(app.id),
                        "job_id": str(app.job_posting_id),
                        "job_title": job.title,
                        "candidate_id": str(app.candidate_id),
                        "candidate_name": f"{candidate.first_name} {candidate.last_name}",
                        "candidate_email": candidate.email,
                        "status": app.status,
                        "match_score": skill_match.match_score if skill_match else None,
                        "cover_letter": app.cover_letter,
                        "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                        "matched_skills": skill_match.matched_skills if skill_match else None,
                        "missing_skills": skill_match.missing_skills if skill_match else None,
                        "extra_skills": skill_match.extra_skills if skill_match else None
                    }
                    
                    processed_app = Application(**app_data)
                    processed_applications.append(processed_app)
                    
                    # Track job titles
                    if job.title:
                        job_titles_from_apps.add(job.title)
                        
                except Exception as e:
                    logger.warning(f"Skipping invalid application data: {str(e)}")
                    continue
            
            self.applications = processed_applications
            
            # Create jobs from application data
            for job_title in job_titles_from_apps:
                job_id = str(uuid.uuid4())
                self.jobs_from_applications[job_id] = Job(
                    id=job_id,
                    title=job_title,
                    description=f"Job posting for {job_title}",
                    skills=[]
                )
                
            logger.info(f"✅ Loaded {len(self.applications)} applications")
            
        except Exception as e:
            logger.error(f"Failed to load applications: {str(e)}")
            self.applications = []
    
    def _load_jobs(self):
        """Load jobs from database"""
        try:
            # Import database models
            from employment_match.database import JobPosting
            
            # Get all job postings for this company
            job_postings = self.db_session.query(JobPosting).filter(
                JobPosting.company_id == self.company_id
            ).all()
            
            jobs = []
            for job_posting in job_postings:
                try:
                    # Extract skills from job posting
                    skills = []
                    if job_posting.extracted_skills and isinstance(job_posting.extracted_skills, dict):
                        skills = job_posting.extracted_skills.get("raw", [])
                    
                    job = Job(
                        id=str(job_posting.id),
                        title=job_posting.title,
                        description=job_posting.description or "",
                        skills=skills,
                        application_count=0  # Will be updated below
                    )
                    jobs.append(job)
                except Exception as e:
                    logger.warning(f"Skipping invalid job data: {str(e)}")
                    continue
            
            self.job_dict = {job.id: job for job in jobs}
            
            # Merge jobs from applications with database jobs
            for job_id, job in self.jobs_from_applications.items():
                if job.title not in [j.title for j in self.job_dict.values()]:
                    self.job_dict[job_id] = job
            
            # Update application counts
            for job in self.job_dict.values():
                job.application_count = sum(1 for app in self.applications if app.job_title == job.title)
            
            logger.info(f"✅ Loaded {len(self.job_dict)} jobs")
                    
        except Exception as e:
            logger.error(f"Failed to load jobs: {str(e)}")
            if not self.job_dict:
                self.job_dict = self.jobs_from_applications.copy()
    
    def _setup_vector_db(self):
        """Setup vector database for job search"""
        all_jobs = list(self.job_dict.values())
        if all_jobs and self.chroma_client and self.embedding_function:
            try:
                try:
                    self.chroma_client.delete_collection("jobs")
                except:
                    pass
                
                collection = self.chroma_client.create_collection(
                    name="jobs",
                    embedding_function=self.embedding_function
                )
                
                job_data = []
                job_metadatas = []
                job_ids = []
                
                for job in all_jobs:
                    job_text = f"Title: {job.title}\nDescription: {job.description}\nSkills: {', '.join(job.skills)}"
                    job_data.append(job_text)
                    job_metadatas.append({"title": job.title, "id": job.id})
                    job_ids.append(job.id)
                
                collection.add(
                    documents=job_data,
                    metadatas=job_metadatas,
                    ids=job_ids
                )
                
                self.vector_db = collection
                logger.info(f"✅ Setup vector DB with {len(all_jobs)} jobs")
            except Exception as e:
                logger.warning(f"Vector DB setup failed: {str(e)}")
                self.vector_db = None
        else:
            self.vector_db = None
    
    def _find_relevant_job(self, query: str) -> Optional[Job]:
        """Find relevant job using vector search or fallback"""
        if not self.vector_db:
            return self._find_relevant_job_fallback(query)
            
        try:
            results = self.vector_db.query(
                query_texts=[query],
                n_results=1
            )
            
            if results["ids"][0]:
                job_id = results["ids"][0][0]
                return self.job_dict.get(job_id)
        except Exception as e:
            logger.warning(f"Vector search failed: {str(e)}")
            return self._find_relevant_job_fallback(query)
        return None
    
    def _find_relevant_job_fallback(self, query: str) -> Optional[Job]:
        """Fallback job search using text matching"""
        query_lower = query.lower()
        for job in self.job_dict.values():
            if (query_lower in job.title.lower() or 
                query_lower in job.description.lower() or
                any(query_lower in skill.lower() for skill in job.skills)):
                return job
        return None
    
    def get_posted_jobs(self) -> List[Job]:
        """Get all posted jobs"""
        return list(self.job_dict.values())
    
    def get_applications_with_scores(self, job_title: Optional[str] = None) -> List[Application]:
        """Get applications with their match scores"""
        if job_title:
            return [app for app in self.applications if app.job_title == job_title]
        return self.applications
    
    def get_hiring_summary(self) -> Dict:
        """Get hiring summary statistics"""
        status_counts = defaultdict(int)
        for app in self.applications:
            status_counts[app.status] += 1
        
        return {
            "total_jobs": len(self.job_dict),
            "total_applications": len(self.applications),
            "status_counts": dict(status_counts)
        }
    
    def get_highest_scorer(self) -> Optional[Application]:
        """Get the application with highest score"""
        if not self.applications:
            return None
        return max(self.applications, key=lambda app: app.match_score or 0)
    
    def get_best_candidate_analysis(self) -> str:
        """Analyze and return the best candidate with detailed reasoning"""
        if not self.applications:
            return "No applications available to analyze."
        
        # Sort applications by score
        sorted_apps = sorted(self.applications, key=lambda app: app.match_score or 0, reverse=True)
        best_app = sorted_apps[0]
        
        response = f"🏆 **Best Candidate Analysis**\n\n"
        response += f"**Top Candidate:** {best_app.candidate_name}\n"
        response += f"**Match Score:** {best_app.match_score}%\n"
        response += f"**Position:** {best_app.job_title}\n"
        response += f"**Email:** {best_app.candidate_email}\n\n"
        
        if best_app.extra_skills:
            response += f"**Extra Skills:** {', '.join(best_app.extra_skills[:5])}\n"
        
        if best_app.missing_skills:
            response += f"**Missing Skills:** {', '.join(best_app.missing_skills[:5])}\n\n"
        
        # Compare with others
        if len(sorted_apps) > 1:
            response += f"**Comparison:**\n"
            for i, app in enumerate(sorted_apps[:3], 1):
                response += f"{i}. {app.candidate_name} - {app.match_score}%\n"
        
        return response
    
    def generate_interview_questions(self, job: Job) -> str:
        """Generate interview questions for a job"""
        if not self.gemini_configured:
            return "❌ Gemini AI not configured."
            
        prompt = (
            f"Generate 5 relevant interview questions for the position: {job.title}\n\n"
            f"Job Description:\n{job.description}\n\n"
            f"Required Skills: {', '.join(job.skills)}\n\n"
            "Focus on technical skills and behavioral aspects. Format as a numbered list."
        )
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating questions: {str(e)}"
    
    def compare_candidates_summary(self, job_title: Optional[str] = None) -> str:
        """Compare candidates with summary analysis"""
        if not self.gemini_configured:
            return "❌ Gemini AI not configured."
            
        if job_title:
            applications = [app for app in self.applications if app.job_title == job_title]
        else:
            applications = self.applications
        
        if len(applications) < 2:
            return "Need at least 2 applications to compare."
        
        # Sort by match score
        applications.sort(key=lambda x: x.match_score or 0, reverse=True)
        top_candidates = applications[:2]
        
        job = None
        for j in self.job_dict.values():
            if j.title == job_title:
                job = j
                break
        
        if not job:
            job_title = applications[0].job_title if applications else "Unknown"
        
        prompt = (
            f"Compare these top 2 candidates for {job_title or 'the position'}:\n\n"
            f"**Candidate 1: {top_candidates[0].candidate_name}**\n"
            f"- Match Score: {top_candidates[0].match_score}%\n"
            f"- Missing Skills: {', '.join(top_candidates[0].missing_skills or [])}\n"
            f"- Extra Skills: {', '.join(top_candidates[0].extra_skills or [])}\n\n"
            f"**Candidate 2: {top_candidates[1].candidate_name}**\n"
            f"- Match Score: {top_candidates[1].match_score}%\n"
            f"- Missing Skills: {', '.join(top_candidates[1].missing_skills or [])}\n"
            f"- Extra Skills: {', '.join(top_candidates[1].extra_skills or [])}\n\n"
            "Provide a brief summary (2-3 sentences) with a clear recommendation."
        )
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error comparing candidates: {str(e)}"
    
    def _classify_intent(self, message: str) -> str:
        """Classify user intent using pattern matching and keywords"""
        message_lower = message.lower()
        
        # Normalize common variations
        message_lower = re.sub(r'\s+', ' ', message_lower.strip())
        
        # Intent patterns with multiple variations
        intent_patterns = {
            'posted_jobs': [
                'posted jobs', 'my jobs', 'what jobs', 'jobs posted', 'job postings',
                'jobs i posted', 'show jobs', 'list jobs', 'available jobs'
            ],
            'show_scores': [
                'score', 'scores', 'applicant score', 'candidate score', 'application score',
                'match score', 'rating', 'ratings', 'show scores', 'all scores'
            ],
            'highest_scorer': [
                'highest score', 'best score', 'top score', 'highest scorer', 'best scorer',
                'who scored highest', 'highest scoring', 'maximum score', 'top scorer'
            ],
            'best_candidate': [
                'best candidate', 'best one', 'who is the best', 'best applicant',
                'top candidate', 'recommended candidate', 'who should i hire',
                'best person', 'strongest candidate'
            ],
            'compare_candidates': [
                'compare', 'comparison', 'compare candidates', 'candidate comparison',
                'vs', 'versus', 'difference between'
            ],
            'who_applied': [
                'who applied', 'applicants for', 'candidates for', 'applications for',
                'who applied for', 'list applicants', 'show applicants'
            ],
            'interview_questions': [
                'interview question', 'interview questions', 'questions for interview',
                'what to ask', 'generate questions'
            ],
            'hiring_summary': [
                'summary', 'overview', 'hiring summary', 'status', 'report',
                'statistics', 'stats', 'total'
            ]
        }
        
        # Check for exact matches first
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return intent
        
        # Check for partial matches
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                pattern_words = pattern.split()
                if len(pattern_words) > 1:
                    if all(word in message_lower for word in pattern_words):
                        return intent
        
        return 'general'
    
    def chat(self, message: str) -> str:
        """Process chat message and return response"""
        if not self.gemini_configured:
            return "❌ Gemini AI not configured. Please configure Gemini first."
        
        # Classify user intent
        intent = self._classify_intent(message)
        
        # Handle different intents
        if intent == 'posted_jobs':
            jobs = self.get_posted_jobs()
            if jobs:
                response = "📋 **Your Posted Jobs:**\n\n"
                for job in jobs:
                    response += f"• **{job.title}** - {job.application_count or 0} applications\n"
                return response
            else:
                return "❌ No jobs posted yet."
        
        elif intent == 'show_scores':
            applications = self.get_applications_with_scores()
            if applications:
                response = "📊 **Application Scores:**\n\n"
                for i, app in enumerate(applications, 1):
                    response += f"{i}. **{app.candidate_name}**\n"
                    response += f"   └─ Job: {app.job_title}\n"
                    response += f"   └─ Match Score: {app.match_score}%\n"
                    response += f"   └─ Status: {app.status.title()}\n"
                    response += f"   └─ Email: {app.candidate_email}\n"
                    if app.missing_skills:
                        response += f"   └─ Missing Skills: {', '.join(app.missing_skills[:3])}{'...' if len(app.missing_skills) > 3 else ''}\n"
                    response += "\n"
                return response
            else:
                return "❌ No applications found."
        
        elif intent == 'highest_scorer':
            highest_scorer = self.get_highest_scorer()
            if highest_scorer:
                response = f"🏆 **Highest Scorer:**\n\n"
                response += f"**Name:** {highest_scorer.candidate_name}\n"
                response += f"**Score:** {highest_scorer.match_score}%\n"
                response += f"**Position:** {highest_scorer.job_title}\n"
                response += f"**Email:** {highest_scorer.candidate_email}\n"
                if highest_scorer.extra_skills:
                    response += f"**Extra Skills:** {', '.join(highest_scorer.extra_skills[:5])}\n"
                return response
            else:
                return "❌ No applications found."
        
        elif intent == 'best_candidate':
            return self.get_best_candidate_analysis()
        
        elif intent == 'compare_candidates':
            job = self._find_relevant_job(message)
            if job:
                return self.compare_candidates_summary(job.title)
            else:
                return self.compare_candidates_summary()
        
        elif intent == 'who_applied':
            job = self._find_relevant_job(message)
            if job:
                applications = self.get_applications_with_scores(job.title)
                if applications:
                    response = f"👥 **Applicants for {job.title}:**\n\n"
                    for i, app in enumerate(applications, 1):
                        response += f"{i}. **{app.candidate_name}** - {app.match_score}% match\n"
                        response += f"   └─ Email: {app.candidate_email}\n"
                    return response
                else:
                    return f"❌ No applications found for {job.title}."
            else:
                return "❌ Please specify a job title."
        
        elif intent == 'interview_questions':
            job = self._find_relevant_job(message)
            if job:
                return f"📝 **Interview Questions for {job.title}:**\n\n{self.generate_interview_questions(job)}"
            else:
                return "❌ Please specify a job title."
        
        elif intent == 'hiring_summary':
            summary = self.get_hiring_summary()
            response = f"📈 **Hiring Summary:**\n\n"
            response += f"• **Total Jobs:** {summary['total_jobs']}\n"
            response += f"• **Total Applications:** {summary['total_applications']}\n"
            response += f"• **Pending Applications:** {summary['status_counts'].get('pending', 0)}\n"
            response += f"• **Accepted Applications:** {summary['status_counts'].get('accepted', 0)}\n"
            response += f"• **Rejected Applications:** {summary['status_counts'].get('rejected', 0)}\n"
            return response
        
        else:
            # General AI response with context
            context = f"Company has {len(self.job_dict)} jobs and {len(self.applications)} applications."
            if self.applications:
                best_app = max(self.applications, key=lambda app: app.match_score or 0)
                context += f" Best candidate: {best_app.candidate_name} with {best_app.match_score}% match."
            
            full_prompt = (
                f"You are an HR assistant. {context}\n\n"
                f"User Query: {message}\n\n"
                "Provide a brief, helpful response (2-3 sentences max). "
                "If the user is asking about candidates, scores, or hiring decisions, "
                "provide specific information based on the context."
            )
            
            try:
                response = self.model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                return f"❌ Error: {str(e)}"
    
    def cleanup(self):
        """Clean up resources"""
        self._cleanup_chromadb()

# Global HR assistant instance
hr_assistant = HRAssistant() 