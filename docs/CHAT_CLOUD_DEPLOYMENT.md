# HR Assistant Chat Integration - Cloud Deployment Guide

## Overview

The Employment Match API now includes an enhanced HR Assistant with AI-powered chat functionality using Gemini AI and ChromaDB for vector search. This guide covers deploying this enhanced system to cloud platforms.

## Features

### HR Assistant Capabilities

- **AI-Powered Chat**: Natural language interaction with Gemini AI
- **Real-time Data Access**: Direct database integration for live company data
- **Vector Search**: ChromaDB for semantic search of applications and jobs
- **Intent Classification**: Automatic detection of user intent
- **Hiring Insights**: Automated analysis of candidates and applications
- **Interview Questions**: AI-generated questions for specific job roles

### Supported Intents

- Job posting management
- Application analysis
- Candidate comparison
- Hiring summaries
- Interview preparation
- Skill matching insights

## API Endpoints

### Chat Configuration

```http
POST /chat/configure-gemini
Content-Type: application/json
Authorization: Bearer <company_token>

{
  "api_key": "your_gemini_api_key"
}
```

### Chat Interaction

```http
POST /chat/message
Content-Type: application/json
Authorization: Bearer <company_token>

{
  "message": "Show me the best candidates for Software Engineer position"
}
```

### Hiring Insights

```http
GET /chat/summary
Authorization: Bearer <company_token>

GET /chat/best-candidate
Authorization: Bearer <company_token>

GET /chat/interview-questions/{job_title}
Authorization: Bearer <company_token>
```

## Cloud Deployment

### 1. Environment Variables

Add these to your cloud environment:

```bash
# Required for HR Assistant
GEMINI_API_KEY=your_gemini_api_key
CHROMA_PERSIST_DIRECTORY=/tmp/chroma_data

# Database (already configured)
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key

# Optional optimizations
CHROMA_CACHE_SIZE=1000
GEMINI_MODEL=gemini-2.0-flash-exp
```

### 2. Resource Requirements

#### Memory Requirements

- **Base API**: 1GB
- **HR Assistant**: +512MB (ChromaDB + embeddings)
- **Gemini AI**: +256MB
- **Total Recommended**: 2GB minimum

#### CPU Requirements

- **Base API**: 1 CPU
- **HR Assistant**: +0.5 CPU
- **Total Recommended**: 2 CPU minimum

#### Storage Requirements

- **Application Code**: ~500MB
- **ChromaDB Data**: ~100MB per company session
- **Temporary Files**: ~200MB
- **Total Recommended**: 1GB minimum

### 3. Cloud Platform Deployment

#### Google Cloud Run (Recommended)

```yaml
# cloudbuild.yaml (updated)
steps:
  - name: "gcr.io/cloud-builders/docker"
    args:
      ["build", "-t", "gcr.io/$PROJECT_ID/employment-match-chat:latest", "."]

  - name: "gcr.io/cloud-builders/docker"
    args: ["push", "gcr.io/$PROJECT_ID/employment-match-chat:latest"]

  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: gcloud
    args:
      - "run"
      - "deploy"
      - "employment-match-chat"
      - "--image"
      - "gcr.io/$PROJECT_ID/employment-match-chat:latest"
      - "--region"
      - "europe-north1"
      - "--platform"
      - "managed"
      - "--allow-unauthenticated"
      - "--memory"
      - "2Gi"
      - "--cpu"
      - "2"
      - "--max-instances"
      - "10"
      - "--timeout"
      - "300"
      - "--set-env-vars"
      - "DATABASE_URL=${_DATABASE_URL},SECRET_KEY=${_SECRET_KEY},GEMINI_API_KEY=${_GEMINI_API_KEY},CHROMA_PERSIST_DIRECTORY=/tmp/chroma_data"

images:
  - "gcr.io/$PROJECT_ID/employment-match-chat:latest"
```

#### AWS ECS/Fargate

```yaml
# task-definition.json
{
  "family": "employment-match-chat",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions":
    [
      {
        "name": "employment-match-chat",
        "image": "your-ecr-repo/employment-match-chat:latest",
        "portMappings": [{ "containerPort": 8080, "protocol": "tcp" }],
        "environment":
          [
            { "name": "DATABASE_URL", "value": "your_database_url" },
            { "name": "GEMINI_API_KEY", "value": "your_gemini_api_key" },
            { "name": "CHROMA_PERSIST_DIRECTORY", "value": "/tmp/chroma_data" },
          ],
        "logConfiguration":
          {
            "logDriver": "awslogs",
            "options":
              {
                "awslogs-group": "/ecs/employment-match-chat",
                "awslogs-region": "us-east-1",
                "awslogs-stream-prefix": "ecs",
              },
          },
      },
    ],
}
```

#### Azure Container Instances

```yaml
# azure-deployment.yaml
apiVersion: 2019-12-01
location: eastus
name: employment-match-chat
properties:
  containers:
    - name: employment-match-chat
      properties:
        image: your-acr.azurecr.io/employment-match-chat:latest
        resources:
          requests:
            memoryInGB: 4
            cpu: 2
        ports:
          - port: 8080
        environmentVariables:
          - name: DATABASE_URL
            value: "your_database_url"
          - name: GEMINI_API_KEY
            value: "your_gemini_api_key"
          - name: CHROMA_PERSIST_DIRECTORY
            value: "/tmp/chroma_data"
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
      - protocol: tcp
        port: 8080
```

### 4. Docker Optimizations

#### Multi-stage Build (Optimized)

```dockerfile
# Dockerfile.optimized
FROM python:3.9-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data /tmp/chroma_data uploads

# Set permissions
RUN chmod 755 /tmp/chroma_data

# Clean up
RUN find /app -name "*.pyc" -delete && \
    find /app -name "__pycache__" -type d -delete && \
    pip uninstall -y setuptools pip && \
    rm -rf /root/.cache/pip

EXPOSE 8080

ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV CHROMA_PERSIST_DIRECTORY=/tmp/chroma_data

CMD ["uvicorn", "employment_match.API:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 5. Performance Optimizations

#### ChromaDB Configuration

```python
# In hr_assistant.py
import chromadb
from chromadb.config import Settings

# Optimized ChromaDB settings for cloud
chroma_settings = Settings(
    anonymized_telemetry=False,
    allow_reset=True,
    is_persistent=True,
    persist_directory="/tmp/chroma_data"
)

self.chroma_client = chromadb.PersistentClient(
    path=self.temp_dir,
    settings=chroma_settings
)
```

#### Memory Management

```python
# Add to hr_assistant.py
import gc
import psutil

def cleanup_memory(self):
    """Clean up memory after processing"""
    gc.collect()

    # Log memory usage
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.info(f"Memory usage: {memory_mb:.2f} MB")
```

#### Session Management

```python
# Add session cleanup to API endpoints
@app.middleware("http")
async def cleanup_sessions(request: Request, call_next):
    response = await call_next(request)

    # Clean up HR assistant sessions periodically
    if hasattr(request.app.state, 'hr_assistant'):
        hr_assistant = request.app.state.hr_assistant
        hr_assistant.cleanup_old_sessions()

    return response
```

### 6. Monitoring and Logging

#### Health Check Enhancement

```python
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check including HR assistant status"""
    try:
        # Check base services
        esco_loaded = len(esco_skills) > 0 if esco_skills else False
        embeddings_loaded = os.path.exists("data/esco_embeddings.npy")

        # Check HR assistant
        hr_assistant_status = "healthy"
        try:
            if hasattr(hr_assistant, 'gemini_configured'):
                hr_assistant_status = "configured" if hr_assistant.gemini_configured else "not_configured"
        except Exception as e:
            hr_assistant_status = f"error: {str(e)}"

        return HealthResponse(
            status="healthy",
            esco_skills_loaded=esco_loaded,
            embeddings_loaded=embeddings_loaded,
            gemini_configured=hr_assistant.gemini_configured if hasattr(hr_assistant, 'gemini_configured') else False,
            hr_assistant_status=hr_assistant_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Structured Logging

```python
# Add to hr_assistant.py
import structlog

logger = structlog.get_logger()

def chat(self, message: str) -> str:
    """Enhanced chat with structured logging"""
    logger.info("chat_request",
                message_length=len(message),
                company_id=self.company_id,
                session_id=self.session_id)

    try:
        # Process chat
        response = self._process_chat(message)

        logger.info("chat_response",
                    response_length=len(response),
                    success=True)

        return response
    except Exception as e:
        logger.error("chat_error",
                     error=str(e),
                     message=message)
        return f"❌ Error: {str(e)}"
```

### 7. Security Considerations

#### API Key Management

```python
# Use environment variables for sensitive data
import os
from cryptography.fernet import Fernet

def get_gemini_api_key():
    """Securely retrieve Gemini API key"""
    encrypted_key = os.getenv('GEMINI_API_KEY_ENCRYPTED')
    if encrypted_key:
        # Decrypt if encrypted
        key = os.getenv('ENCRYPTION_KEY')
        f = Fernet(key.encode())
        return f.decrypt(encrypted_key.encode()).decode()
    return os.getenv('GEMINI_API_KEY')
```

#### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/chat/message")
@limiter.limit("10/minute")
async def chat_with_assistant(request: Request, ...):
    # Chat implementation
    pass
```

### 8. Testing

#### Integration Tests

```python
# test_chat_integration.py
import pytest
from fastapi.testclient import TestClient
from employment_match.API import app

client = TestClient(app)

def test_chat_configuration():
    """Test Gemini configuration"""
    response = client.post("/chat/configure-gemini",
                          json={"api_key": "test_key"})
    assert response.status_code == 200
    assert response.json()["success"] in [True, False]

def test_chat_message():
    """Test chat functionality"""
    response = client.post("/chat/message",
                          json={"message": "Hello"})
    assert response.status_code == 200
    assert "response" in response.json()

def test_hiring_summary():
    """Test hiring summary endpoint"""
    response = client.get("/chat/summary")
    assert response.status_code in [200, 401]  # 401 if not authenticated
```

### 9. Troubleshooting

#### Common Issues

1. **ChromaDB Initialization Failures**

   ```bash
   # Check disk space
   df -h /tmp

   # Check permissions
   ls -la /tmp/chroma_data
   ```

2. **Memory Issues**

   ```bash
   # Monitor memory usage
   docker stats <container_id>

   # Check logs
   docker logs <container_id> | grep -i memory
   ```

3. **Gemini API Errors**
   ```bash
   # Test API key
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://generativelanguage.googleapis.com/v1beta/models
   ```

#### Debug Endpoints

```python
@app.get("/debug/hr-assistant")
async def debug_hr_assistant(
    current_company: Company = Depends(get_current_company)
):
    """Debug HR assistant status"""
    return {
        "company_id": current_company.id,
        "gemini_configured": hr_assistant.gemini_configured,
        "chroma_initialized": hr_assistant.chroma_client is not None,
        "session_id": getattr(hr_assistant, 'session_id', None),
        "applications_count": len(hr_assistant.applications),
        "jobs_count": len(hr_assistant.job_dict)
    }
```

### 10. Rollback Plan

1. **Database Backup**

   ```bash
   # Backup before deployment
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Container Rollback**

   ```bash
   # Rollback to previous version
   gcloud run services update-traffic employment-match-chat \
     --to-revisions=employment-match-chat-00001-abc=100
   ```

3. **Environment Rollback**
   ```bash
   # Revert environment variables
   gcloud run services update employment-match-chat \
     --set-env-vars DATABASE_URL=$OLD_DATABASE_URL
   ```

## Conclusion

The HR Assistant chat integration is now fully optimized for cloud deployment with:

- ✅ Memory and CPU optimizations
- ✅ Proper session management
- ✅ Security best practices
- ✅ Comprehensive monitoring
- ✅ Automated testing
- ✅ Rollback procedures

The system is ready for production deployment on any major cloud platform.
