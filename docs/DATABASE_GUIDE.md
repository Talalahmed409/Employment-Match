# Database Guide for Employment Match System

## Overview

The Employment Match system uses PostgreSQL as its primary database to store job postings, candidate applications, and skill matching results. This guide covers the database setup, schema, and usage.

## Database Schema

### Tables

#### 1. `companies` - Company/Employer Information

- **id**: Primary key (auto-increment)
- **name**: Company name
- **email**: Unique email address
- **password_hash**: Hashed password for authentication
- **description**: Company description
- **website**: Company website URL
- **location**: Company location
- **industry**: Company industry
- **created_at**: Account creation timestamp
- **updated_at**: Last update timestamp
- **is_active**: Whether account is active

#### 2. `candidates` - Job Seeker Information

- **id**: Primary key (auto-increment)
- **first_name**: First name
- **last_name**: Last name
- **email**: Unique email address
- **password_hash**: Hashed password for authentication
- **phone**: Phone number
- **location**: Current location
- **current_title**: Current job title
- **years_experience**: Years of experience
- **cv_file_path**: Path to uploaded CV file
- **cv_text**: Extracted CV text
- **extracted_skills**: JSON field storing standardized skills
- **created_at**: Account creation timestamp
- **updated_at**: Last update timestamp
- **is_active**: Whether account is active

#### 3. `job_postings` - Job Postings

- **id**: Primary key (auto-increment)
- **company_id**: Foreign key to companies table
- **title**: Job title
- **description**: Job description
- **requirements**: Job requirements
- **location**: Job location
- **salary_min**: Minimum salary
- **salary_max**: Maximum salary
- **employment_type**: Type of employment (full-time, part-time, etc.)
- **experience_level**: Required experience level
- **extracted_skills**: JSON field storing standardized skills from job description
- **is_active**: Whether job posting is active
- **created_at**: Creation timestamp
- **updated_at**: Last update timestamp

#### 4. `applications` - Job Applications

- **id**: Primary key (auto-increment)
- **candidate_id**: Foreign key to candidates table
- **job_posting_id**: Foreign key to job_postings table
- **cover_letter**: Cover letter text
- **status**: Application status (pending, reviewed, shortlisted, rejected, hired)
- **applied_at**: Application timestamp
- **reviewed_at**: Review timestamp
- **reviewed_by**: Foreign key to companies table (who reviewed)
- **notes**: Review notes

#### 5. `skill_matches` - Skill Matching Results

- **id**: Primary key (auto-increment)
- **application_id**: Foreign key to applications table
- **match_score**: Overall match percentage (0-100)
- **matched_skills**: JSON array of matched skills with details
- **missing_skills**: JSON array of missing skills
- **extra_skills**: JSON array of extra skills
- **cv_skills**: JSON array of skills extracted from CV
- **job_skills**: JSON array of skills extracted from job posting
- **similarity_threshold**: Threshold used for matching
- **fuzzy_threshold**: Fuzzy matching threshold used
- **created_at**: Creation timestamp

## Database Setup

### Prerequisites

1. **PostgreSQL Installation**

   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib

   # macOS (using Homebrew)
   brew install postgresql

   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Setup Steps

#### 1. Create Database

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Create database and user
CREATE DATABASE employment_match;
CREATE USER employment_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE employment_match TO employment_user;
\q
```

#### 2. Set Environment Variables

```bash
# Set database URL
export DATABASE_URL="postgresql://employment_user:your_password@localhost/employment_match"

# Set secret key for JWT tokens
export SECRET_KEY="your-secret-key-change-in-production"

# Set Gemini API key (optional, for skill extraction)
export GEMINI_API_KEY="your-gemini-api-key"
```

#### 3. Initialize Database

```bash
# Run the setup script
python setup_database.py
```

This will:

- Test database connection
- Create all tables
- Optionally create sample data
- Verify table creation

#### 4. Run Migrations (Optional)

If you need to make schema changes later:

```bash
# Initialize Alembic (first time only)
alembic init migrations

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

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

## Workflow

### For Candidates

1. **Register/Login**: Create account or login
2. **Upload CV**: Upload PDF CV for skill extraction
3. **Browse Jobs**: View available job postings
4. **Apply**: Apply to jobs with optional cover letter
5. **Track Applications**: View application status and match scores

### For Companies

1. **Register/Login**: Create company account or login
2. **Post Jobs**: Create job postings with descriptions
3. **Review Applications**: View all applications with skill match scores
4. **Update Status**: Change application status and add notes

## Data Flow

1. **Job Creation**: When a company creates a job posting, the system automatically extracts skills from the job description
2. **CV Upload**: When a candidate uploads a CV, the system extracts skills and stores them
3. **Application**: When a candidate applies, the system:
   - Creates an application record
   - Performs skill matching between CV and job requirements
   - Stores the match results with scores
4. **Review**: Companies can view applications with detailed skill matching information

## Security Considerations

- Passwords are hashed using bcrypt
- JWT tokens are used for authentication
- Database connections use parameterized queries
- File uploads are validated and stored securely
- Environment variables are used for sensitive configuration

## Backup and Maintenance

### Regular Backups

```bash
# Create backup
pg_dump employment_match > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql employment_match < backup_file.sql
```

### Database Maintenance

```bash
# Analyze tables for query optimization
psql employment_match -c "ANALYZE;"

# Vacuum to reclaim storage
psql employment_match -c "VACUUM;"
```

## Troubleshooting

### Common Issues

1. **Connection Refused**

   - Check if PostgreSQL is running
   - Verify database URL format
   - Check firewall settings

2. **Permission Denied**

   - Verify database user permissions
   - Check file permissions for uploads directory

3. **Migration Errors**
   - Ensure all dependencies are installed
   - Check database URL in alembic.ini
   - Verify model imports in env.py

### Logs

Check application logs for detailed error information:

```bash
# If running with uvicorn
uvicorn API:app --log-level debug
```

## Performance Optimization

1. **Indexes**: Key fields are indexed for faster queries
2. **Connection Pooling**: SQLAlchemy handles connection pooling
3. **Lazy Loading**: Models are loaded only when needed
4. **Background Processing**: Heavy operations run in background tasks

## Scaling Considerations

1. **Database**: Consider read replicas for high read loads
2. **File Storage**: Use cloud storage (S3, etc.) for CV files
3. **Caching**: Implement Redis for session and query caching
4. **Load Balancing**: Use multiple application instances
