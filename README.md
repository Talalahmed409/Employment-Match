# Employment Match - Job Application and Skill Matching System

A comprehensive job application platform that combines AI-powered skill extraction with a full job posting and application management system. The platform extracts technical and soft skills from job descriptions and CVs, standardizes them against the ESCO taxonomy (v1.2.0), and provides intelligent skill matching for job applications.

## 🚀 Overview

This project has evolved from a skill extraction tool into a complete job application system with the following capabilities:

- **Job Posting Management**: Companies can create and manage job postings
- **CV Processing**: Automatic skill extraction from uploaded CVs (PDF or text)
- **Skill Matching**: AI-powered matching between candidate skills and job requirements
- **Application Tracking**: Complete application lifecycle management
- **User Authentication**: Secure JWT-based authentication for companies and candidates
- **Docker Support**: Easy deployment with Docker and Docker Compose

## ✨ Key Features

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
- Docker containerization for easy deployment

## 🛠️ Quick Start

### Prerequisites

- Python 3.8+ (for local development)
- PostgreSQL 12+ (for local development)
- Docker & Docker Compose (for containerized deployment)
- Google Gemini API Key (optional, for enhanced skill extraction)

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**

   ```bash
   git clone https://github.com/Talalahmed409/Employment-Match.git
   cd Employment-Match
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**

   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - API Documentation: http://localhost:8080/docs
   - Health Check: http://localhost:8080/health

### Option 2: Local Development

1. **Clone and setup**

   ```bash
   git clone https://github.com/Talalahmed409/Employment-Match.git
   cd Employment-Match
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
   python start_server.py
   ```

6. **Access the API**
   - API Documentation: http://localhost:8080/docs
   - Health Check: http://localhost:8080/health

## 🐳 Docker Deployment

### Using Docker Compose

The easiest way to deploy the application is using Docker Compose:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build the image
docker build -t employment-match .

# Run the container
docker run -p 8080:8080 \
  -e DATABASE_URL="your_database_url" \
  -e SECRET_KEY="your_secret_key" \
  employment-match
```

### Production Deployment

For production deployment, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions including:

- Google Cloud Platform deployment
- Environment variable configuration
- Database setup
- SSL/TLS configuration
- Monitoring and logging

## 📚 API Endpoints

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

For detailed API documentation, visit `/docs` when the server is running.

## 🗄️ Database Schema

The system uses PostgreSQL with the following main tables:

- **companies**: Company/employer information
- **candidates**: Job seeker profiles
- **job_postings**: Job listings with extracted skills
- **applications**: Job applications
- **skill_matches**: Skill matching results with scores

See [docs/DATABASE_GUIDE.md](docs/DATABASE_GUIDE.md) for detailed schema information.

## 🔄 Workflow Example

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

## ⚙️ Configuration

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

## 📁 Project Structure

```
Employment_Match/
├── employment_match/          # Main application package
│   ├── __init__.py
│   ├── API.py                # Main FastAPI application
│   ├── database.py           # Database models and configuration
│   ├── auth.py              # Authentication utilities
│   ├── setup_database.py    # Database setup script
│   ├── extract_skills.py    # Skill extraction module
│   ├── extract_cv_skills.py # CV skill extraction
│   ├── match_skills.py      # Skill matching logic
│   ├── generate_embeddings.py # ESCO embeddings generation
│   └── convert_esco_to_json.py # ESCO data conversion
├── docs/                     # Documentation
│   ├── API_README.md
│   ├── API_ENDPOINTS_REFERENCE.md
│   ├── API_QUICK_REFERENCE.md
│   ├── DATABASE_GUIDE.md
│   ├── DOCKER_OPTIMIZATION.md
│   └── QUICK_START.md
├── docker/                   # Docker configuration
│   ├── Dockerfile
│   ├── Dockerfile.lightweight
│   └── build-docker.sh
├── migrations/               # Database migrations
├── data/                    # ESCO skills data
├── uploads/                 # Uploaded CV files
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile              # Main Dockerfile
├── requirements.txt         # Python dependencies
├── start_server.py         # Server startup script
├── health_check.py         # Health check endpoint
├── setup_neon_database.py  # Neon database setup
├── test_api_endpoints.py   # API testing script
├── deploy.sh               # Deployment script
├── cloudbuild.yaml         # Google Cloud Build configuration
├── alembic.ini             # Alembic configuration
└── DEPLOYMENT_GUIDE.md     # Deployment guide
```

## 📦 Dependencies

Key dependencies include:

- **FastAPI**: Modern web framework for building APIs
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Primary database
- **JWT**: Authentication and authorization
- **Transformers**: NLP models for skill extraction
- **Google Generative AI**: AI-powered skill extraction
- **PyPDF2**: PDF processing for CV uploads
- **Docker**: Containerization
- **Alembic**: Database migrations

See `requirements.txt` for complete list.

## 📖 Documentation

- [Quick Start Guide](docs/QUICK_START.md) - Get up and running quickly
- [API Documentation](docs/API_README.md) - Comprehensive API guide
- [Database Guide](docs/DATABASE_GUIDE.md) - Detailed database information
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment instructions
- [Docker Optimization](docs/DOCKER_OPTIMIZATION.md) - Docker best practices
- [Interactive API Docs](http://localhost:8080/docs) - Swagger UI documentation

## 🐛 Troubleshooting

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

4. **Docker Issues**
   - Check Docker and Docker Compose are installed
   - Verify ports are not in use
   - Check container logs with `docker-compose logs`

### Getting Help

- Check API documentation at `/docs`
- Review application logs
- Verify environment variables
- Run `python setup_database.py` to test database setup
- Check Docker logs: `docker-compose logs -f`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ESCO** (European Skills/Competences, qualifications and Occupations) for the skills taxonomy
- **Google Gemini API** for AI-powered skill extraction
- **FastAPI** for the modern web framework
- **SQLAlchemy** for database management
- **Docker** for containerization support

## 📞 Support

For support and questions:

- Check the [documentation](docs/)
- Open an [issue](https://github.com/Talalahmed409/Employment-Match/issues)
- Review the [API documentation](http://localhost:8080/docs) when running locally

---

**Made with ❤️ for better job matching**
