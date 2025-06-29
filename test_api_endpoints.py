#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Employment Match System

This script tests all endpoints and demonstrates:
1. Company and candidate registration/login
2. Job posting creation
3. Multiple candidate applications to the same job
4. Getting top candidates by match score
5. All other API endpoints
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional
from datetime import datetime
import tempfile
from fpdf import FPDF

# Configuration
BASE_URL = "http://localhost:8080"
API_DOCS_URL = f"{BASE_URL}/docs"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.company_token = None
        self.candidate_tokens = []
        self.job_id = None
        self.application_ids = []
        
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_test(self, test_name: str, success: bool, details: str = ""):
        """Print test result"""
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    headers: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict:
        """Make HTTP request and return response"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.company_token:
            headers.setdefault("Authorization", f"Bearer {self.company_token}")
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, data=data, files=files, headers=headers)
                else:
                    response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, data=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.HTTPError as e:
            # Return error details for proper handling
            error_detail = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", "")
                except:
                    error_detail = e.response.text
            return {"error": str(e), "detail": error_detail, "status_code": e.response.status_code if hasattr(e, 'response') else None}
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return {"error": str(e)}
    
    def test_health_check(self):
        """Test health check endpoint"""
        self.print_section("Health Check")
        
        result = self.make_request("GET", "/health")
        success = "status" in result and result["status"] == "healthy"
        self.print_test("Health Check", success, f"Status: {result.get('status', 'unknown')}")
        
        return success
    
    def test_company_authentication(self):
        """Test company registration or login"""
        self.print_section("Company Authentication")
        
        company_data = {
            "name": "TechCorp Solutions",
            "email": "hr@techcorp.com",
            "password": "securepass123",
            "description": "Leading technology solutions provider",
            "website": "https://techcorp.com",
            "location": "San Francisco, CA",
            "industry": "Technology"
        }
        
        # Try to register first
        result = self.make_request("POST", "/register/company", company_data)
        if "access_token" in result:
            self.print_test("Company Registration", True, 
                           f"Company: {company_data['name']}, Token: {result.get('access_token', 'None')[:20]}...")
            self.company_token = result["access_token"]
            return True
        elif "Email already registered" in result.get("detail", ""):
            # Try to login instead
            login_data = {
                "email": company_data["email"],
                "password": company_data["password"]
            }
            result = self.make_request("POST", "/login/company", login_data)
            if "access_token" in result:
                self.print_test("Company Login", True, 
                               f"Company: {company_data['name']}, Token: {result.get('access_token', 'None')[:20]}...")
                self.company_token = result["access_token"]
                return True
            else:
                self.print_test("Company Login", False, "Failed to login with existing credentials")
                return False
        else:
            self.print_test("Company Registration", False, f"Error: {result.get('detail', 'Unknown error')}")
            return False
    
    def test_candidate_authentications(self):
        """Test multiple candidate registrations or logins"""
        self.print_section("Candidate Authentications")
        
        candidates = [
            {
                "first_name": "Alice",
                "last_name": "Johnson",
                "email": "alice.johnson@email.com",
                "password": "password123",
                "phone": "+1-555-0101",
                "location": "New York, NY",
                "current_title": "Senior Python Developer",
                "years_experience": 5
            },
            {
                "first_name": "Bob",
                "last_name": "Smith",
                "email": "bob.smith@email.com",
                "password": "password123",
                "phone": "+1-555-0102",
                "location": "Boston, MA",
                "current_title": "Full Stack Developer",
                "years_experience": 3
            },
            {
                "first_name": "Carol",
                "last_name": "Davis",
                "email": "carol.davis@email.com",
                "password": "password123",
                "phone": "+1-555-0103",
                "location": "Seattle, WA",
                "current_title": "Software Engineer",
                "years_experience": 2
            },
            {
                "first_name": "David",
                "last_name": "Wilson",
                "email": "david.wilson@email.com",
                "password": "password123",
                "phone": "+1-555-0104",
                "location": "Austin, TX",
                "current_title": "Backend Developer",
                "years_experience": 4
            },
            {
                "first_name": "Eva",
                "last_name": "Brown",
                "email": "eva.brown@email.com",
                "password": "password123",
                "phone": "+1-555-0105",
                "location": "Denver, CO",
                "current_title": "Python Developer",
                "years_experience": 1
            }
        ]
        
        all_success = True
        for i, candidate_data in enumerate(candidates, 1):
            # Try to register first
            result = self.make_request("POST", "/register/candidate", candidate_data)
            if "access_token" in result:
                self.print_test(f"Candidate {i} Registration", True,
                               f"{candidate_data['first_name']} {candidate_data['last_name']}")
                self.candidate_tokens.append(result["access_token"])
            elif "Email already registered" in result.get("detail", ""):
                # Try to login instead
                login_data = {
                    "email": candidate_data["email"],
                    "password": candidate_data["password"]
                }
                result = self.make_request("POST", "/login/candidate", login_data)
                if "access_token" in result:
                    self.print_test(f"Candidate {i} Login", True,
                                   f"{candidate_data['first_name']} {candidate_data['last_name']}")
                    self.candidate_tokens.append(result["access_token"])
                else:
                    self.print_test(f"Candidate {i} Login", False,
                                   f"Failed to login {candidate_data['first_name']} {candidate_data['last_name']}")
                    all_success = False
            else:
                self.print_test(f"Candidate {i} Registration", False,
                               f"Error: {result.get('detail', 'Unknown error')}")
                all_success = False
        
        return all_success
    
    def test_job_posting_creation(self):
        """Test job posting creation"""
        self.print_section("Job Posting Creation")
        
        if not self.company_token:
            self.print_test("Job Posting Creation", False, "No company token available")
            return False
        
        job_data = {
            "title": "Senior Python Developer",
            "description": """
            We are looking for an experienced Python developer to join our dynamic team.
            
            Key Responsibilities:
            - Develop and maintain high-quality Python applications
            - Work with FastAPI, Django, and Flask frameworks
            - Design and implement RESTful APIs
            - Collaborate with cross-functional teams
            - Write clean, maintainable, and well-documented code
            - Participate in code reviews and technical discussions
            
            Required Skills:
            - Python programming (3+ years)
            - FastAPI, Django, or Flask experience
            - PostgreSQL database experience
            - Git version control
            - RESTful API design
            - Unit testing and test-driven development
            - Docker containerization
            - AWS or cloud platform experience
            
            Nice to Have:
            - Machine learning experience
            - React or Vue.js frontend skills
            - Microservices architecture
            - CI/CD pipeline experience
            """,
            "requirements": "Python, FastAPI, PostgreSQL, Git, Docker, AWS, 3+ years experience",
            "location": "San Francisco, CA (Hybrid)",
            "salary_min": 80000,
            "salary_max": 130000,
            "employment_type": "full-time",
            "experience_level": "senior"
        }
        
        result = self.make_request("POST", "/jobs", job_data)
        success = "id" in result
        self.print_test("Job Posting Creation", success,
                       f"Job ID: {result.get('id', 'None')}, Title: {result.get('title', 'None')}")
        
        if success:
            self.job_id = result["id"]
        
        return success
    
    def test_get_job_postings(self):
        """Test getting job postings"""
        self.print_section("Get Job Postings")
        
        result = self.make_request("GET", "/jobs")
        success = isinstance(result, list) and len(result) > 0
        self.print_test("Get All Job Postings", success,
                       f"Found {len(result)} job postings")
        
        if success and result:
            job = result[0]
            job_id = job.get("id")
            result_detail = self.make_request("GET", f"/jobs/{job_id}")
            success_detail = "id" in result_detail
            self.print_test("Get Specific Job Posting", success_detail,
                           f"Job ID: {result_detail.get('id', 'None')}")
            
            # Set job_id if not already set
            if not self.job_id:
                self.job_id = job_id
        
        return success
    
    def generate_mock_cv_pdf(self, candidate_name, cv_text):
        """Generate a mock PDF CV file and return its path"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, candidate_name, ln=True, align='C')
        for line in cv_text.splitlines():
            pdf.cell(200, 10, line, ln=True, align='L')
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf.output(temp.name)
        return temp.name

    def test_cv_upload_and_skill_extraction(self):
        """Test CV upload and skill extraction for candidates using /upload-cv with mock PDFs"""
        self.print_section("CV Upload and Skill Extraction")

        if not self.candidate_tokens:
            self.print_test("CV Skill Extraction", False, "No candidate tokens available")
            return False

        # Create sample CV text for each candidate
        cv_texts = [
            """
            ALICE JOHNSON
            Senior Python Developer
            EXPERIENCE:
            Senior Python Developer at TechStart Inc. (2020-2023)
            - Developed microservices using FastAPI and Django
            - Led team of 3 developers in building RESTful APIs
            - Implemented PostgreSQL database design and optimization
            - Used Docker for containerization and AWS for deployment
            - Mentored junior developers and conducted code reviews
            Python Developer at DataCorp (2018-2020)
            - Built data processing pipelines using Python
            - Worked with PostgreSQL and Redis databases
            - Implemented unit tests and integration tests
            - Used Git for version control and CI/CD pipelines
            SKILLS:
            Python, FastAPI, Django, Flask, PostgreSQL, Redis, Docker, AWS, Git, RESTful APIs, Microservices, Unit Testing, CI/CD, Machine Learning
            """,
            """
            BOB SMITH
            Full Stack Developer
            EXPERIENCE:
            Full Stack Developer at WebSolutions (2020-2023)
            - Built full-stack applications using Python and JavaScript
            - Developed APIs with FastAPI and Express.js
            - Worked with PostgreSQL and MongoDB databases
            - Implemented frontend using React and Vue.js
            - Used Docker and Kubernetes for deployment
            Junior Developer at StartupXYZ (2018-2020)
            - Developed web applications using Python and Django
            - Worked with MySQL database
            - Basic Git and deployment experience
            SKILLS:
            Python, JavaScript, FastAPI, Django, React, Vue.js, PostgreSQL, MongoDB, Docker, Kubernetes, Git, RESTful APIs
            """,
            """
            CAROL DAVIS
            Software Engineer
            EXPERIENCE:
            Software Engineer at InnovateTech (2021-2023)
            - Developed Python applications and APIs
            - Worked with PostgreSQL database
            - Basic experience with Docker and AWS
            - Participated in code reviews and testing
            Intern at TechCorp (2020-2021)
            - Assisted in Python development tasks
            - Learned Git version control
            - Basic database operations
            SKILLS:
            Python, FastAPI, PostgreSQL, Docker, AWS, Git, Unit Testing
            """,
            """
            DAVID WILSON
            Backend Developer
            EXPERIENCE:
            Backend Developer at DataSystems (2019-2023)
            - Built scalable backend systems using Python
            - Developed APIs with Django and FastAPI
            - Worked extensively with PostgreSQL and Redis
            - Implemented microservices architecture
            - Used Docker, Kubernetes, and AWS for deployment
            Developer at CloudTech (2018-2019)
            - Developed Python applications
            - Worked with various databases
            - Basic cloud deployment experience
            SKILLS:
            Python, Django, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, AWS, Microservices, RESTful APIs, Git, CI/CD
            """,
            """
            EVA BROWN
            Python Developer
            EXPERIENCE:
            Python Developer at StartupABC (2022-2023)
            - Developed Python applications and scripts
            - Basic experience with FastAPI and PostgreSQL
            - Learning Docker and cloud deployment
            - Participated in team development processes
            Recent graduate with computer science degree
            - Academic projects in Python programming
            - Basic understanding of databases and web development
            SKILLS:
            Python, FastAPI, PostgreSQL, Git, Basic Docker, Web Development
            """
        ]

        all_success = True
        for i, (token, cv_text) in enumerate(zip(self.candidate_tokens, cv_texts), 1):
            candidate_name = f"Candidate {i}"
            pdf_path = self.generate_mock_cv_pdf(candidate_name, cv_text)
            with open(pdf_path, "rb") as f:
                files = {"file": (f"cv_{i}.pdf", f, "application/pdf")}
                # Temporarily set candidate token
                original_token = self.company_token
                self.company_token = token
                result = self.make_request("POST", "/upload-cv", files=files)
                self.company_token = original_token
            os.remove(pdf_path)
            success = "skills" in result
            self.print_test(f"Candidate {i} CV Upload", success, f"Skills extracted: {len(result.get('skills', {}).get('raw', [])) if success else 0}")
            if not success:
                all_success = False
        return all_success
    
    def test_job_applications(self):
        """Test multiple candidates applying to the same job"""
        self.print_section("Job Applications")
        
        if not self.candidate_tokens or not self.job_id:
            self.print_test("Job Applications", False, "No candidate tokens or job ID available")
            return False
        
        cover_letters = [
            "I am excited to apply for this Senior Python Developer position. With 5 years of experience in Python development and expertise in FastAPI, Django, and PostgreSQL, I believe I would be a great fit for your team.",
            "As a Full Stack Developer with 3 years of experience, I have worked extensively with Python, FastAPI, and PostgreSQL. I am passionate about building scalable applications and would love to contribute to your team.",
            "I am a Software Engineer with 2 years of experience in Python development. While I may be early in my career, I am eager to learn and grow, and I believe my skills in FastAPI and PostgreSQL would be valuable to your team.",
            "With 4 years of experience as a Backend Developer, I have built numerous Python applications using Django, FastAPI, and PostgreSQL. I am particularly interested in your microservices architecture and would love to contribute.",
            "As a recent graduate and Python Developer, I am excited about this opportunity to grow my skills. I have experience with FastAPI and PostgreSQL, and I am eager to learn from your experienced team."
        ]
        
        all_success = True
        for i, (token, cover_letter) in enumerate(zip(self.candidate_tokens, cover_letters), 1):
            # Temporarily set candidate token
            original_token = self.company_token
            self.company_token = token
            
            application_data = {
                "cover_letter": cover_letter
            }
            
            result = self.make_request("POST", f"/jobs/{self.job_id}/apply", application_data)
            success = "id" in result
            self.print_test(f"Candidate {i} Application", success,
                           f"Application ID: {result.get('id', 'None')}, Match Score: {result.get('match_score', 'None')}")
            
            if success:
                self.application_ids.append(result["id"])
            else:
                all_success = False
            
            # Restore company token
            self.company_token = original_token
        
        return all_success
    
    def test_get_candidate_applications(self):
        """Test getting candidate applications"""
        self.print_section("Get Candidate Applications")
        
        if not self.candidate_tokens:
            self.print_test("Get Candidate Applications", False, "No candidate tokens available")
            return False
        
        all_success = True
        for i, token in enumerate(self.candidate_tokens, 1):
            # Temporarily set candidate token
            original_token = self.company_token
            self.company_token = token
            
            result = self.make_request("GET", "/applications/my")
            success = isinstance(result, list)
            self.print_test(f"Candidate {i} Applications", success,
                           f"Found {len(result)} applications")
            
            if not success:
                all_success = False
            
            # Restore company token
            self.company_token = original_token
        
        return all_success
    
    def test_get_company_applications(self):
        """Test getting company applications"""
        self.print_section("Get Company Applications")
        
        if not self.company_token:
            self.print_test("Get Company Applications", False, "No company token available")
            return False
        
        result = self.make_request("GET", "/applications/company")
        success = isinstance(result, list) and len(result) > 0
        self.print_test("Get Company Applications", success,
                       f"Found {len(result)} applications")
        
        if success:
            for app in result:
                print(f"    - {app.get('candidate_name', 'Unknown')}: "
                      f"Match Score {app.get('match_score', 'N/A')}")
        
        return success
    
    def test_top_candidates_by_match_score(self):
        """Test getting top candidates by match score"""
        self.print_section("Top Candidates by Match Score")
        
        if not self.company_token or not self.job_id:
            self.print_test("Get Top Candidates", False, "No company token or job ID available")
            return False
        
        result = self.make_request("GET", f"/jobs/{self.job_id}/top-candidates?limit=5")
        success = isinstance(result, list) and len(result) > 0
        self.print_test("Get Top Candidates", success,
                       f"Found {len(result)} top candidates")
        
        if success:
            print("\nTop Candidates (ordered by match score):")
            for i, candidate in enumerate(result, 1):
                print(f"  {i}. {candidate.get('candidate_name', 'Unknown')} - "
                      f"Match Score: {candidate.get('match_score', 'N/A')}%")
                if candidate.get('matched_skills'):
                    print(f"     Matched Skills: {len(candidate['matched_skills'])}")
                if candidate.get('missing_skills'):
                    print(f"     Missing Skills: {len(candidate['missing_skills'])}")
        
        return success
    
    def test_update_application_status(self):
        """Test updating application status"""
        self.print_section("Update Application Status")
        
        if not self.company_token or not self.application_ids:
            self.print_test("Update Application Status", False, "No company token or applications to update")
            return False
        
        # Update first application status
        app_id = self.application_ids[0]
        status_data = {
            "status": "shortlisted",
            "notes": "Strong technical skills and good match score"
        }
        
        result = self.make_request("PUT", f"/applications/{app_id}/status", status_data)
        success = "message" in result
        self.print_test("Update Application Status", success,
                       f"Updated application {app_id} to shortlisted")
        
        return success
    
    def test_skill_extraction_endpoints(self):
        """Test skill extraction endpoints"""
        self.print_section("Skill Extraction Endpoints")
        
        # Test job skills extraction
        job_description = """
        We are looking for a Python developer with experience in:
        - FastAPI and Django frameworks
        - PostgreSQL database management
        - Docker containerization
        - AWS cloud services
        - Git version control
        - RESTful API development
        """
        
        job_data = {
            "job_description": job_description,
            "similarity_threshold": 0.6,
            "fuzzy_threshold": 90
        }
        
        result = self.make_request("POST", "/extract-job-skills", job_data)
        success_job = "standardized" in result and "raw" in result
        self.print_test("Job Skills Extraction", success_job,
                       f"Extracted {len(result.get('raw', []))} skills")
        
        # Test CV skills extraction
        cv_text = """
        Python Developer with 3 years experience in:
        - FastAPI and Django development
        - PostgreSQL and MySQL databases
        - Docker and Kubernetes
        - AWS and Azure cloud platforms
        - Git and GitHub
        - RESTful API design
        """
        
        cv_data = {
            "cv_text": cv_text,
            "similarity_threshold": 0.4,
            "fuzzy_threshold": 90
        }
        
        result = self.make_request("POST", "/extract-cv-skills-text", cv_data)
        success_cv = "standardized" in result and "raw" in result
        self.print_test("CV Skills Extraction", success_cv,
                       f"Extracted {len(result.get('raw', []))} skills")
        
        # Test skill matching
        if success_job and success_cv:
            match_data = {
                "cv_skills": result.get("raw", []),
                "job_skills": job_data["job_description"].split(),
                "similarity_threshold": 0.3,
                "fuzzy_threshold": 80
            }
            
            result = self.make_request("POST", "/match-skills", match_data)
            success_match = "match_score" in result
            self.print_test("Skill Matching", success_match,
                           f"Match Score: {result.get('match_score', 'N/A')}%")
            
            return success_job and success_cv and success_match
        
        return success_job and success_cv
    
    def test_data_setup_endpoint(self):
        """Test data setup endpoint"""
        self.print_section("Data Setup Endpoint")
        
        result = self.make_request("POST", "/setup-data")
        success = "message" in result
        self.print_test("Data Setup", success, result.get("message", "Unknown"))
        
        return success
    
    def test_esco_skills_info(self):
        """Test ESCO skills info endpoint"""
        self.print_section("ESCO Skills Info")
        
        result = self.make_request("GET", "/esco-skills")
        success = "total_skills" in result
        self.print_test("ESCO Skills Info", success,
                       f"Total skills: {result.get('total_skills', 'Unknown')}")
        
        return success
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("Starting Comprehensive API Testing")
        print(f"Base URL: {self.base_url}")
        print(f"API Documentation: {API_DOCS_URL}")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Company Authentication", self.test_company_authentication),
            ("Candidate Authentications", self.test_candidate_authentications),
            ("Job Posting Creation", self.test_job_posting_creation),
            ("Get Job Postings", self.test_get_job_postings),
            ("CV Upload and Skill Extraction", self.test_cv_upload_and_skill_extraction),
            ("Job Applications", self.test_job_applications),
            ("Get Candidate Applications", self.test_get_candidate_applications),
            ("Get Company Applications", self.test_get_company_applications),
            ("Top Candidates by Match Score", self.test_top_candidates_by_match_score),
            ("Update Application Status", self.test_update_application_status),
            ("Skill Extraction Endpoints", self.test_skill_extraction_endpoints),
            ("Data Setup Endpoint", self.test_data_setup_endpoint),
            ("ESCO Skills Info", self.test_esco_skills_info),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"✗ FAIL {test_name} - Exception: {e}")
                results.append((test_name, False))
        
        # Summary
        self.print_section("Test Summary")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed < total:
            print("\nFailed Tests:")
            for test_name, result in results:
                if not result:
                    print(f"  - {test_name}")
        
        return passed == total

def main():
    """Main function to run the tests"""
    print("Employment Match API - Comprehensive Testing")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding properly at {BASE_URL}")
            print("Please ensure the server is running with: python API.py")
            return
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("Please ensure the server is running with: python API.py")
        return
    
    # Run tests
    tester = APITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! The API is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the server logs and configuration.")
    
    print(f"\n📖 API Documentation: {API_DOCS_URL}")

if __name__ == "__main__":
    main() 