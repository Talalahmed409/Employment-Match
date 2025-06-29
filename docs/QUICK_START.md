# Quick Start Guide - Employment Match System

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Employment_Match
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Setup PostgreSQL**

   ```bash
   # Install PostgreSQL (Ubuntu/Debian)
   sudo apt update
   sudo apt install postgresql postgresql-contrib

   # Start PostgreSQL service
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

4. **Create database and user**

   ```bash
   sudo -u postgres psql

   CREATE DATABASE employment_match;
   CREATE USER employment_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE employment_match TO employment_user;
   \q
   ```

5. **Set environment variables**

   ```bash
   export DATABASE_URL="postgresql://employment_user:your_password@localhost/employment_match"
   export SECRET_KEY="your-secret-key-change-in-production"
   export GEMINI_API_KEY="your-gemini-api-key"  # Optional
   ```

6. **Initialize database**

   ```bash
   python -m employment_match.setup_database
   ```

7. **Setup ESCO data (optional)**
   ```bash
   # Place skills_en.csv in data/ directory
   # Then run:
   curl -X POST http://localhost:8080/setup-data
   ```

## Running the Application

1. **Start the server**

   ```bash
   python -m employment_match.API
   ```

2. **Access the API**
   - API Documentation: http://localhost:8080/docs
   - Health Check: http://localhost:8080/health

## Testing the System

### 1. Register a Company

```bash
curl -X POST "http://localhost:8080/register/company" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TechCorp Inc.",
    "email": "hr@techcorp.com",
    "password": "password123",
    "description": "Leading technology company"
  }'
```

### 2. Register a Candidate

```bash
curl -X POST "http://localhost:8080/register/candidate" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@email.com",
    "password": "password123",
    "current_title": "Software Engineer"
  }'
```

### 3. Login and Get Token

```bash
curl -X POST "http://localhost:8080/login/company" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "hr@techcorp.com",
    "password": "password123"
  }'
```

### 4. Create Job Posting (Company)

```bash
curl -X POST "http://localhost:8080/jobs" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "We are looking for an experienced Python developer...",
    "requirements": "Python, FastAPI, PostgreSQL, 3+ years experience",
    "location": "San Francisco, CA",
    "salary_min": 80000,
    "salary_max": 120000
  }'
```

### 5. Upload CV (Candidate)

```bash
curl -X POST "http://localhost:8080/upload-cv" \
  -H "Authorization: Bearer CANDIDATE_TOKEN_HERE" \
  -F "file=@path/to/your/cv.pdf"
```

### 6. Apply to Job (Candidate)

```bash
curl -X POST "http://localhost:8080/jobs/1/apply" \
  -H "Authorization: Bearer CANDIDATE_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "cover_letter": "I am excited to apply for this position..."
  }'
```

### 7. View Applications (Company)

```bash
curl -X GET "http://localhost:8080/applications/company" \
  -H "Authorization: Bearer COMPANY_TOKEN_HERE"
```

## Key Features

- **User Authentication**: JWT-based authentication for companies and candidates
- **Job Postings**: Companies can create and manage job postings
- **CV Processing**: Automatic skill extraction from uploaded CVs
- **Skill Matching**: AI-powered matching between candidate skills and job requirements
- **Application Management**: Track application status and match scores
- **API Documentation**: Interactive API docs at `/docs`

## File Structure

```
Employment_Match/
├── employment_match/
│   ├── API.py
│   ├── auth.py
│   ├── convert_esco_to_json.py
│   ├── database.py
│   ├── extract_cv_skills.py
│   ├── extract_skills.py
│   ├── generate_embeddings.py
│   ├── match_skills.py
│   ├── setup_database.py
│   └── __init__.py
├── requirements.txt
├── docker/
├── docs/
├── data/
├── uploads/
├── static/
├── migrations/
├── tests/
└── README.md
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**

   - Check if PostgreSQL is running
   - Verify DATABASE_URL format
   - Ensure database and user exist

2. **Import Errors**

   - Install all dependencies: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

3. **Permission Errors**

   - Ensure uploads directory exists and is writable
   - Check file permissions

4. **Skill Extraction Not Working**
   - Verify GEMINI_API_KEY is set (optional)
   - Check if ESCO data is loaded
   - Review logs for specific errors

### Getting Help

- Check the API documentation at `/docs`
- Review logs for detailed error messages
- Ensure all environment variables are set correctly
- Verify database setup with `python -m employment_match.setup_database`

## Next Steps

1. **Production Deployment**

   - Use a production WSGI server (Gunicorn)
   - Set up proper environment variables
   - Configure database for production
   - Set up SSL/TLS certificates

2. **Advanced Features**

   - Email notifications
   - Advanced search and filtering
   - Analytics and reporting
   - Integration with external job boards

3. **Security Enhancements**
   - Rate limiting
   - Input validation
   - Security headers
   - Regular security audits
