import uuid
import requests
import chromadb
import google.generativeai as genai
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Union
from chromadb.utils import embedding_functions
from IPython.display import display, Markdown, clear_output
from getpass import getpass
from collections import defaultdict
import os
import tempfile
import shutil
import re

# Enhanced Pydantic models with better validation
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

class Candidate(BaseModel):
    id: str = Field(..., description="Candidate ID")
    name: str
    skills: List[str] = []
    compatibility_score: float = 0.0
    applied: bool = False
    
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

# Configuration
EXTERNAL_API_URL = "https://employment-match-final-cicb6wgitq-lz.a.run.app"
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

class EnhancedHRAssistant:
    def __init__(self):
        self.session_id = None
        self.access_token = None
        self.vector_db = None
        self.chroma_client = None
        self.job_dict = {}
        self.logged_in = False
        self.gemini_configured = False
        self.temp_dir = None
        self.applications = []
        self.jobs_from_applications = {}  # Track jobs from applications
        
    def configure_gemini(self):
        try:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY is not set")

            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('models/gemini-2.5-pro')
            test_response = self.model.generate_content("Test connection")
            if test_response.text:
                print("✅ Gemini configured successfully")
                self.gemini_configured = True
                return True
        except Exception as e:
            print(f"❌ Gemini setup failed: {str(e)}")
            return False
        
    def login(self):
        if not self.gemini_configured:
            print("⚠️ Configure Gemini first")
            return False
        
        print("\n🏢 Company Login")
        print("Please enter your company credentials:")
        
        try:
            email = input("📧 Email: ")
            password = getpass("🔒 Password: ")
            
            if not email or not password:
                print("❌ Email and password are required")
                return False
                
            print("🔄 Authenticating...")
            
            response = requests.post(
                f"{EXTERNAL_API_URL}/login/company",
                json={"email": email, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self.access_token = auth_data["access_token"]
                self.session_id = str(uuid.uuid4())
                
                print("✅ Authentication successful!")
                print("🔄 Loading company data...")
                
                try:
                    self._initialize_data()
                    print(f"✅ Login successful! Session ID: {self.session_id}")
                    self.logged_in = True
                    return True
                except Exception as e:
                    print(f"⚠️ Data initialization failed: {str(e)}")
                    print("✅ Login successful but data loading failed")
                    self.logged_in = True
                    return True
            else:
                error_msg = response.text if response.text else response.reason
                if "no such table: tenants" in error_msg:
                    raise Exception("🔧 Server database configuration error")
                elif response.status_code == 401:
                    raise Exception("❌ Invalid credentials")
                elif response.status_code == 404:
                    raise Exception("❌ Company not found")
                else:
                    raise Exception(f"❌ Login failed: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            return False
    
    def _external_api_request(self, method: str, endpoint: str):
        if not self.access_token:
            return []
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{EXTERNAL_API_URL}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=headers, timeout=10)
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"⚠️ API Error: {str(e)}")
            return []
    
    def _cleanup_chromadb(self):
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
            print(f"⚠️ ChromaDB cleanup warning: {str(e)}")
    
    def _initialize_data(self):
        self._cleanup_chromadb()
        
        try:
            self.temp_dir = tempfile.mkdtemp(prefix=f"chroma_hr_{self.session_id}_")
            self.chroma_client = chromadb.PersistentClient(path=self.temp_dir)
            print("✅ ChromaDB initialized successfully")
        except Exception as e:
            print(f"⚠️ ChromaDB initialization failed: {str(e)}")
            self.chroma_client = None
        
        # Fetch applications first to get accurate job data
        try:
            applications_data = self._external_api_request("GET", "/applications/company")
            
            if applications_data and isinstance(applications_data, list):
                applications = []
                job_titles_from_apps = set()
                
                for app_data in applications_data:
                    try:
                        if isinstance(app_data, dict):
                            standardized_data = {
                                "id": app_data.get("id", str(uuid.uuid4())),
                                "job_id": app_data.get("job_id"),
                                "job_title": app_data.get("job_title"),
                                "candidate_id": app_data.get("candidate_id"),
                                "candidate_name": app_data.get("candidate_name"),
                                "candidate_email": app_data.get("candidate_email"),
                                "status": app_data.get("status", "pending"),
                                "match_score": app_data.get("match_score"),
                                "cover_letter": app_data.get("cover_letter"),
                                "applied_at": app_data.get("applied_at"),
                                "matched_skills": app_data.get("matched_skills"),
                                "missing_skills": app_data.get("missing_skills"),
                                "extra_skills": app_data.get("extra_skills")
                            }
                            
                            app = Application(**standardized_data)
                            applications.append(app)
                            
                            # Track job titles from applications
                            if app.job_title:
                                job_titles_from_apps.add(app.job_title)
                    except Exception as e:
                        print(f"⚠️ Skipping invalid application data: {str(e)}")
                        continue
                        
                self.applications = applications
                
                # Create jobs from application data if no jobs from API
                for job_title in job_titles_from_apps:
                    job_id = str(uuid.uuid4())
                    self.jobs_from_applications[job_id] = Job(
                        id=job_id,
                        title=job_title,
                        description=f"Job posting for {job_title}",
                        skills=[]
                    )
                    
            else:
                self.applications = []
                
            print(f"✅ Loaded {len(self.applications)} applications")
            
        except Exception as e:
            print(f"⚠️ Failed to load applications: {str(e)}")
            self.applications = []
        
        # Fetch jobs from API
        try:
            jobs_data = self._external_api_request("GET", "/company/jobs")
            
            if jobs_data and isinstance(jobs_data, list):
                jobs = []
                for job_data in jobs_data:
                    try:
                        job = Job(**job_data)
                        jobs.append(job)
                    except Exception as e:
                        print(f"⚠️ Skipping invalid job data: {str(e)}")
                        continue
                
                self.job_dict = {job.id: job for job in jobs}
            else:
                # Use jobs from applications if API jobs not available
                self.job_dict = self.jobs_from_applications.copy()
            
            # Merge jobs from applications with API jobs
            for job_id, job in self.jobs_from_applications.items():
                if job.title not in [j.title for j in self.job_dict.values()]:
                    self.job_dict[job_id] = job
            
            # Update application counts
            for job in self.job_dict.values():
                job.application_count = sum(1 for app in self.applications if app.job_title == job.title)
            
            # Setup vector DB
            all_jobs = list(self.job_dict.values())
            if all_jobs and self.chroma_client:
                try:
                    try:
                        self.chroma_client.delete_collection("jobs")
                    except:
                        pass
                    
                    collection = self.chroma_client.create_collection(
                        name="jobs",
                        embedding_function=embedding_function
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
                    print(f"✅ Loaded {len(all_jobs)} jobs with vector search")
                except Exception as e:
                    print(f"⚠️ Vector DB setup failed: {str(e)}")
                    self.vector_db = None
                    print(f"✅ Loaded {len(all_jobs)} jobs (without vector search)")
            else:
                self.vector_db = None
                if all_jobs:
                    print(f"✅ Loaded {len(all_jobs)} jobs (without vector search)")
                else:
                    print("⚠️ No jobs available")
                    
        except Exception as e:
            print(f"⚠️ Failed to load jobs: {str(e)}")
            if not self.job_dict:
                self.job_dict = self.jobs_from_applications.copy()
    
    def _find_relevant_job(self, query: str) -> Optional[Job]:
        if not self.vector_db:
            query_lower = query.lower()
            for job in self.job_dict.values():
                if (query_lower in job.title.lower() or 
                    query_lower in job.description.lower() or
                    any(query_lower in skill.lower() for skill in job.skills)):
                    return job
            return None
            
        try:
            results = self.vector_db.query(
                query_texts=[query],
                n_results=1
            )
            
            if results["ids"][0]:
                job_id = results["ids"][0][0]
                return self.job_dict.get(job_id)
        except Exception as e:
            print(f"⚠️ Vector search failed: {str(e)}")
            return self._find_relevant_job_fallback(query)
        return None
    
    def _find_relevant_job_fallback(self, query: str) -> Optional[Job]:
        query_lower = query.lower()
        for job in self.job_dict.values():
            if (query_lower in job.title.lower() or 
                query_lower in job.description.lower() or
                any(query_lower in skill.lower() for skill in job.skills)):
                return job
        return None
    
    def get_posted_jobs(self) -> List[Job]:
        return list(self.job_dict.values())
    
    def get_applications_with_scores(self, job_title: Optional[str] = None) -> List[Application]:
        """Get applications with their match scores"""
        if job_title:
            return [app for app in self.applications if app.job_title == job_title]
        return self.applications
    
    def get_hiring_summary(self) -> Dict:
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
        if not self.gemini_configured:
            return "❌ Gemini not configured. Please restart the application."
            
        if not self.logged_in:
            return "❌ Not logged in. Please restart the application and login first."
        
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
        self._cleanup_chromadb()

# Initialize the assistant
assistant = EnhancedHRAssistant()

def main():
    print("🤖 Enhanced HR Assistant System")
    print("=" * 50)
    
    # Configure Gemini
    print("\n⚙️ Configuring Gemini AI...")
    if not assistant.configure_gemini():
        print("❌ Failed to configure Gemini. Exiting.")
        return
    
    # Login
    if not assistant.login():
        print("❌ Login failed. Exiting.")
        return
    
    # Start chat
    print("\n💬 HR Assistant Ready!")
    print("=" * 50)
    print("Try asking:")
    print("• 'What jobs did I post?'")
    print("• 'Show me scores for applicants'")
    print("• 'Who is the highest scorer?'")
    print("• 'Who is the best candidate?'")
    print("• 'Compare candidates for my job'")
    print("• 'Who applied for Machine Learning Engineer?'")
    print("• 'Generate interview questions'")
    print("• 'Show hiring summary'")
    print("• Type 'exit' to quit")
    print("=" * 50)
    
    try:
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            response = assistant.chat(user_input)
            print(f"\nAssistant: {response}")
            
    except KeyboardInterrupt:
        print("\n\n👋 Session ended. Goodbye!")
    finally:
        assistant.cleanup()

if __name__ == "__main__":
    main()