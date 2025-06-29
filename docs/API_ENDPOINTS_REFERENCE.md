# Employment Match API - Frontend Developer Reference

## Overview

The Employment Match API is a FastAPI-based REST API that provides job application and skill matching functionality. The API supports two main user types: **Companies** and **Candidates**.

**Base URL**: `http://localhost:8080` (or your deployed server URL)

## Authentication

Most endpoints require authentication using JWT Bearer tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

## Common Response Formats

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response

```json
{
  "detail": "Error message description"
}
```

---

## 🔐 Authentication Endpoints

### Register Company

**POST** `/register/company`

Register a new company account.

**Request Body:**

```json
{
  "name": "TechCorp Inc.",
  "email": "hr@techcorp.com",
  "password": "securepassword123",
  "description": "Leading technology company",
  "website": "https://techcorp.com",
  "location": "San Francisco, CA",
  "industry": "Technology"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_type": "company",
  "user_id": 1
}
```

### Register Candidate

**POST** `/register/candidate`

Register a new candidate account.

**Request Body:**

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@email.com",
  "password": "securepassword123",
  "phone": "+1-555-0123",
  "location": "New York, NY",
  "current_title": "Software Engineer",
  "years_experience": 3
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_type": "candidate",
  "user_id": 1
}
```

### Login Company

**POST** `/login/company`

Login for existing company accounts.

**Request Body:**

```json
{
  "email": "hr@techcorp.com",
  "password": "securepassword123"
}
```

**Response:** Same as register response

### Login Candidate

**POST** `/login/candidate`

Login for existing candidate accounts.

**Request Body:**

```json
{
  "email": "john.doe@email.com",
  "password": "securepassword123"
}
```

**Response:** Same as register response

---

## 🏢 Company Endpoints

_All company endpoints require company authentication_

### Create Job Posting

**POST** `/jobs`

Create a new job posting. Skills are automatically extracted from the job description.

**Headers:** `Authorization: Bearer <company_token>`

**Request Body:**

```json
{
  "title": "Senior Software Engineer",
  "description": "We are looking for a senior software engineer with experience in Python, FastAPI, and machine learning. The ideal candidate should have 5+ years of experience in backend development and be familiar with cloud platforms like AWS.",
  "requirements": "5+ years experience, Python, FastAPI, AWS, Machine Learning",
  "location": "San Francisco, CA",
  "salary_min": 120000,
  "salary_max": 180000,
  "employment_type": "Full-time",
  "experience_level": "Senior"
}
```

**Response:**

```json
{
  "id": 1,
  "title": "Senior Software Engineer",
  "description": "We are looking for a senior software engineer...",
  "requirements": "5+ years experience, Python, FastAPI, AWS, Machine Learning",
  "location": "San Francisco, CA",
  "salary_min": 120000,
  "salary_max": 180000,
  "employment_type": "Full-time",
  "experience_level": "Senior",
  "company_name": "TechCorp Inc.",
  "created_at": "2024-01-15T10:30:00Z",
  "is_active": true
}
```

### Get Company Applications

**GET** `/applications/company`

Get all applications for jobs posted by the authenticated company.

**Headers:** `Authorization: Bearer <company_token>`

**Response:**

```json
[
  {
    "id": 1,
    "candidate_name": "John Doe",
    "candidate_email": "john.doe@email.com",
    "job_title": "Senior Software Engineer",
    "cover_letter": "I am excited to apply for this position...",
    "status": "pending",
    "applied_at": "2024-01-16T14:20:00Z",
    "match_score": 85.5,
    "matched_skills": [
      {
        "cv_skill": "Python",
        "job_skill": "Python",
        "match_type": "exact",
        "confidence": 1.0
      }
    ],
    "missing_skills": ["AWS"],
    "extra_skills": ["JavaScript", "React"]
  }
]
```

### Update Application Status

**PUT** `/applications/{application_id}/status`

Update the status of an application (e.g., "accepted", "rejected", "under_review").

**Headers:** `Authorization: Bearer <company_token>`

**Request Body (Form Data):**

```
status: accepted
notes: Excellent candidate with strong technical skills
```

**Response:**

```json
{
  "message": "Application status updated successfully"
}
```

### Get Top Candidates for Job

**GET** `/jobs/{job_id}/top-candidates`

Get the top candidates by match score for a specific job posting.

**Headers:** `Authorization: Bearer <company_token>`

**Query Parameters:**

- `limit` (optional): Number of candidates to return (default: 10)

**Response:**

```json
[
  {
    "id": 1,
    "candidate_name": "John Doe",
    "candidate_email": "john.doe@email.com",
    "job_title": "Senior Software Engineer",
    "cover_letter": "I am excited to apply...",
    "status": "pending",
    "applied_at": "2024-01-16T14:20:00Z",
    "match_score": 92.3,
    "matched_skills": [...],
    "missing_skills": [...],
    "extra_skills": [...]
  }
]
```

---

## 👤 Candidate Endpoints

_All candidate endpoints require candidate authentication_

### Upload CV

**POST** `/upload-cv`

Upload and process a CV PDF file for skill extraction.

**Headers:** `Authorization: Bearer <candidate_token>`

**Request Body:** `multipart/form-data`

- `file`: PDF file

**Response:**

```json
{
  "message": "CV uploaded and processed successfully",
  "skills": {
    "standardized": ["Python", "FastAPI", "Machine Learning"],
    "raw": ["Python programming", "FastAPI framework", "ML algorithms"]
  }
}
```

### Apply to Job

**POST** `/jobs/{job_id}/apply`

Apply to a specific job posting.

**Headers:** `Authorization: Bearer <candidate_token>`

**Request Body:**

```json
{
  "cover_letter": "I am excited to apply for the Senior Software Engineer position at TechCorp. With my 5 years of experience in Python development and machine learning, I believe I would be a great fit for your team..."
}
```

**Response:**

```json
{
  "id": 1,
  "job_title": "Senior Software Engineer",
  "company_name": "TechCorp Inc.",
  "status": "pending",
  "applied_at": "2024-01-16T14:20:00Z",
  "match_score": 85.5
}
```

### Get My Applications

**GET** `/applications/my`

Get all applications submitted by the authenticated candidate.

**Headers:** `Authorization: Bearer <candidate_token>`

**Response:**

```json
[
  {
    "id": 1,
    "job_title": "Senior Software Engineer",
    "company_name": "TechCorp Inc.",
    "status": "pending",
    "applied_at": "2024-01-16T14:20:00Z",
    "match_score": 85.5
  }
]
```

---

## 🌐 Public Endpoints

_No authentication required_

### Health Check

**GET** `/health`

Check API health and system status.

**Response:**

```json
{
  "status": "healthy",
  "esco_skills_loaded": true,
  "embeddings_loaded": true,
  "gemini_configured": true
}
```

### Get All Job Postings

**GET** `/jobs`

Get all active job postings.

**Query Parameters:**

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)

**Response:**

```json
[
  {
    "id": 1,
    "title": "Senior Software Engineer",
    "description": "We are looking for a senior software engineer...",
    "requirements": "5+ years experience, Python, FastAPI, AWS, Machine Learning",
    "location": "San Francisco, CA",
    "salary_min": 120000,
    "salary_max": 180000,
    "employment_type": "Full-time",
    "experience_level": "Senior",
    "company_name": "TechCorp Inc.",
    "created_at": "2024-01-15T10:30:00Z",
    "is_active": true
  }
]
```

### Get Specific Job Posting

**GET** `/jobs/{job_id}`

Get details of a specific job posting.

**Response:** Same as job posting object in the list above

---

## 🔧 Utility Endpoints

_No authentication required_

### Extract Skills from Job Description

**POST** `/extract-job-skills`

Extract standardized skills from job description text.

**Request Body:**

```json
{
  "job_description": "We are looking for a Python developer with experience in FastAPI and machine learning.",
  "similarity_threshold": 0.6,
  "fuzzy_threshold": 90
}
```

**Response:**

```json
{
  "standardized": ["Python", "FastAPI", "Machine Learning"],
  "raw": ["Python developer", "FastAPI", "machine learning"]
}
```

### Extract Skills from CV Text

**POST** `/extract-cv-skills-text`

Extract standardized skills from CV text.

**Request Body:**

```json
{
  "cv_text": "I have 5 years of experience in Python development, working with FastAPI and machine learning algorithms.",
  "similarity_threshold": 0.4,
  "fuzzy_threshold": 90
}
```

**Response:**

```json
{
  "standardized": ["Python", "FastAPI", "Machine Learning"],
  "raw": ["Python development", "FastAPI", "machine learning algorithms"]
}
```

### Match Skills

**POST** `/match-skills`

Match CV skills against job skills and calculate match score.

**Request Body:**

```json
{
  "cv_skills": ["Python", "FastAPI", "Machine Learning"],
  "job_skills": ["Python", "FastAPI", "AWS", "Machine Learning"],
  "similarity_threshold": 0.3,
  "fuzzy_threshold": 80
}
```

**Response:**

```json
{
  "match_score": 85.5,
  "matched_skills": [
    {
      "cv_skill": "Python",
      "job_skill": "Python",
      "match_type": "exact",
      "confidence": 1.0
    }
  ],
  "missing_skills": ["AWS"],
  "extra_skills": []
}
```

### Setup Data

**POST** `/setup-data`

Initialize ESCO data and generate embeddings (runs in background).

**Response:**

```json
{
  "message": "Data setup started in background. Check logs for progress."
}
```

### Get ESCO Skills Info

**GET** `/esco-skills`

Get information about loaded ESCO skills.

**Response:**

```json
{
  "total_skills": 13485,
  "sample_skills": [
    "Python",
    "JavaScript",
    "Machine Learning",
    "Data Analysis",
    "Project Management"
  ],
  "embeddings_available": true
}
```

---

## 📊 Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## 📝 Application Status Values

- `pending` - Application submitted, awaiting review
- `under_review` - Application is being reviewed
- `accepted` - Application accepted, moving to next stage
- `rejected` - Application rejected
- `withdrawn` - Application withdrawn by candidate

## 🔧 Development Notes

### File Upload

- CV uploads must be PDF files
- Files are stored in `uploads/cvs/` directory
- File naming convention: `cv_{candidate_id}_{timestamp}.pdf`

### Skill Matching

- Skills are automatically extracted from job descriptions and CVs
- Matching uses both exact and fuzzy matching with configurable thresholds
- Match scores range from 0-100

### Database

- Uses SQLAlchemy ORM with PostgreSQL
- Automatic skill extraction and matching on job creation and application
- All timestamps are in UTC

### Rate Limiting

- No rate limiting currently implemented
- Consider implementing for production use

---

## 🚀 Getting Started

1. **Register/Login**: Use authentication endpoints to get access tokens
2. **Companies**: Create job postings and review applications
3. **Candidates**: Upload CV, browse jobs, and apply
4. **Skill Matching**: Automatic skill extraction and matching on all interactions

For more detailed information, see the interactive API documentation at `/docs` (Swagger UI) or `/redoc` (ReDoc).
