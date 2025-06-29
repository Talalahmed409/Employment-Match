# Employment Match - Job Application and Skill Matching System

A comprehensive job application platform that combines AI-powered skill extraction with a full job posting and application management system. The platform extracts technical and soft skills from job descriptions and CVs, standardizes them against the ESCO taxonomy (v1.2.0), and provides intelligent skill matching for job applications.

## Overview

This project has evolved from a skill extraction tool into a complete job application system with the following capabilities:

- **Job Posting Management**: Companies can create and manage job postings
- **CV Processing**: Automatic skill extraction from uploaded CVs (PDF or text)
- **Skill Matching**: AI-powered matching between candidate skills and job requirements
- **Application Tracking**: Complete application lifecycle management
- **User Authentication**: Secure JWT-based authentication for companies and candidates

## Key Features

### For Companies

- Register and manage company profiles
- Create job postings with automatic skill extraction
- Review applications with detailed skill match scores
- Track application status and add notes
- View candidate skills and match details

### For Candidates

- Register and create candidate profiles
- Upload CVs for automatic skill extraction
- Browse available job postings
- Apply to jobs with optional cover letters
- Track application status and match scores

### Technical Features

- Extracts technical and soft skills from job descriptions and CVs
- Standardizes skills against the ESCO v1.2.0 taxonomy
- Uses Google Gemini API for skill summarization
- Implements sentence-transformers for embedding-based matching
- Supports fuzzy matching as fallback
- PostgreSQL database with SQLAlchemy ORM
- JWT-based authentication
- RESTful API with FastAPI

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Google Gemini API Key (optional, for enhanced skill extraction)

### Installation

1. **Clone and setup**

   ```bash
   git clone https://github.com/MahmoudSalama7/Employment_Match.git
   cd Employment_Match
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL**

   ```bash
   # Create database and user
   sudo -u postgres psql
   CREATE DATABASE employment_match;
   CREATE USER employment_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE employment_match TO employment_user;
   \q
   ```

3. **Configure environment**

   ```bash
   export DATABASE_URL="postgresql://employment_user:your_password@localhost/employment_match"
   export SECRET_KEY="your-secret-key-change-in-production"
   export GEMINI_API_KEY="your-gemini-api-key"  # Optional
   ```

4. **Initialize database**

   ```bash
   python setup_database.py
   ```

5. **Start the application**

   ```bash
   python API.py
   ```

6. **Access the API**
   - API Documentation: http://localhost:8080/docs
   - Health Check: http://localhost:8080/health

## API Endpoints

### Authentication

- `POST /register/company` - Register a new company
- `POST /register/candidate` - Register a new candidate
- `POST /login/company` - Login for companies
- `POST /login/candidate` - Login for candidates

### Job Postings

- `POST /jobs` - Create a new job posting (company only)
- `GET /jobs` - Get all active job postings
- `GET /jobs/{job_id}` - Get specific job posting

### Applications

- `POST /jobs/{job_id}/apply` - Apply to a job (candidate only)
- `GET /applications/my` - Get candidate's applications
- `GET /applications/company` - Get applications for company's jobs
- `PUT /applications/{application_id}/status` - Update application status

### CV Management

- `POST /upload-cv` - Upload and process CV (candidate only)

### Skill Extraction (Legacy)

- `POST /extract-job-skills` - Extract skills from job description
- `POST /extract-cv-skills-text` - Extract skills from CV text
- `POST /match-skills` - Match CV skills against job skills

## Database Schema

The system uses PostgreSQL with the following main tables:

- **companies**: Company/employer information
- **candidates**: Job seeker profiles
- **job_postings**: Job listings with extracted skills
- **applications**: Job applications
- **skill_matches**: Skill matching results with scores

See [DATABASE_GUIDE.md](DATABASE_GUIDE.md) for detailed schema information.

## Workflow Example

1. **Company Registration**

   ```bash
   curl -X POST "http://localhost:8080/register/company" \
     -H "Content-Type: application/json" \
     -d '{"name": "TechCorp", "email": "hr@techcorp.com", "password": "password123"}'
   ```

2. **Create Job Posting**

   ```bash
   curl -X POST "http://localhost:8080/jobs" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"title": "Python Developer", "description": "We need a Python developer..."}'
   ```

3. **Candidate Registration**

   ```bash
   curl -X POST "http://localhost:8080/register/candidate" \
     -H "Content-Type: application/json" \
     -d '{"first_name": "John", "last_name": "Doe", "email": "john@email.com", "password": "password123"}'
   ```

4. **Upload CV**

   ```bash
   curl -X POST "http://localhost:8080/upload-cv" \
     -H "Authorization: Bearer CANDIDATE_TOKEN" \
     -F "file=@cv.pdf"
   ```

5. **Apply to Job**

   ```bash
   curl -X POST "http://localhost:8080/jobs/1/apply" \
     -H "Authorization: Bearer CANDIDATE_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"cover_letter": "I am excited to apply..."}'
   ```

6. **Review Applications**
   ```bash
   curl -X GET "http://localhost:8080/applications/company" \
     -H "Authorization: Bearer COMPANY_TOKEN"
   ```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `GEMINI_API_KEY`: Google Gemini API key (optional)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8080)

### Skill Extraction Settings

- `SIMILARITY_THRESHOLD`: Embedding-based matching threshold (default: 0.4)
- `FUZZY_THRESHOLD`: Fuzzy matching threshold (default: 90)
- `BATCH_SIZE`: Processing batch size (default: 100)

## File Structure

```
Employment_Match/
├── API.py                 # Main FastAPI application
├── database.py            # Database models and configuration
├── auth.py               # Authentication utilities
├── setup_database.py     # Database setup script
├── extract_skills.py     # Skill extraction module
├── extract_cv_skills.py  # CV skill extraction
├── match_skills.py       # Skill matching logic
├── generate_embeddings.py # ESCO embeddings generation
├── convert_esco_to_json.py # ESCO data conversion
├── requirements.txt      # Python dependencies
├── DATABASE_GUIDE.md     # Detailed database guide
├── QUICK_START.md        # Quick start guide
├── migrations/           # Database migrations
├── data/                # ESCO skills data
├── uploads/             # Uploaded CV files
└── static/              # Static files
```

## Dependencies

Key dependencies include:

- FastAPI: Web framework
- SQLAlchemy: Database ORM
- PostgreSQL: Database
- JWT: Authentication
- Transformers: NLP models
- Google Generative AI: Skill extraction
- PyPDF2: PDF processing

See `requirements.txt` for complete list.

## Documentation

- [Quick Start Guide](QUICK_START.md) - Get up and running quickly
- [Database Guide](DATABASE_GUIDE.md) - Detailed database information
- [API Documentation](http://localhost:8080/docs) - Interactive API docs

## Troubleshooting

### Common Issues

1. **Database Connection**

   - Ensure PostgreSQL is running
   - Check DATABASE_URL format
   - Verify database and user exist

2. **Skill Extraction**

   - Check GEMINI_API_KEY (optional)
   - Verify ESCO data is loaded
   - Review logs for specific errors

3. **Authentication**
   - Ensure SECRET_KEY is set
   - Check JWT token format
   - Verify user exists in database

### Getting Help

- Check API documentation at `/docs`
- Review application logs
- Verify environment variables
- Run `python setup_database.py` to test database setup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ESCO (European Skills/Competences, qualifications and Occupations) for the skills taxonomy
- Google Gemini API for AI-powered skill extraction
- FastAPI for the web framework
- SQLAlchemy for database management
