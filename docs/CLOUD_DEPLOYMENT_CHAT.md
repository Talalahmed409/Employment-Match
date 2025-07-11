# Cloud Deployment Guide - HR Assistant Chat Integration

## Overview

This guide covers deploying the HR Assistant Chat Integration to your cloud server. The integration adds AI-powered chat functionality to your existing Employment Match API.

## Prerequisites

1. **Existing Employment Match API** deployed and running
2. **Gemini API Key** from Google AI Studio
3. **Database Access** (PostgreSQL)
4. **Cloud Platform Access** (Google Cloud, AWS, etc.)

## Step 1: Update Dependencies

### Update requirements.txt

The chat integration requires additional dependencies. Ensure your `requirements.txt` includes:

```txt
# New dependencies for chat integration
chromadb>=0.4.0
google-generativeai>=0.3.0
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Environment Configuration

### Add Environment Variables

Add these to your cloud environment variables:

```bash
# Required for Gemini AI
GEMINI_API_KEY=your-gemini-api-key-here

# Existing variables (should already be set)
DATABASE_URL=your-database-url
SECRET_KEY=your-secret-key
```

### Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and add it to your environment variables

## Step 3: Code Deployment

### Files to Deploy

Ensure these files are deployed to your cloud server:

1. **`employment_match/hr_assistant.py`** - HR Assistant module
2. **`employment_match/API.py`** - Updated API with chat endpoints
3. **`requirements.txt`** - Updated with new dependencies

### File Structure

```
employment_match/
├── API.py (updated with chat endpoints)
├── hr_assistant.py (new file)
├── database.py
├── auth.py
└── ... (other existing files)
```

## Step 4: Database Considerations

### No Schema Changes Required

The chat integration uses your existing database schema:

- `companies` table
- `candidates` table
- `job_postings` table
- `applications` table
- `skill_matches` table

### Performance Considerations

- The HR assistant loads data on-demand
- ChromaDB creates temporary files for vector search
- Consider disk space for temporary ChromaDB files

## Step 5: Cloud Platform Specific Deployment

### Google Cloud Platform (GCP)

#### Update Dockerfile

If using Docker, ensure your Dockerfile includes the new dependencies:

```dockerfile
# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY employment_match/ ./employment_match/
```

#### Update Cloud Build

If using Cloud Build, your `cloudbuild.yaml` should include:

```yaml
steps:
  - name: "gcr.io/cloud-builders/docker"
    args: ["build", "-t", "gcr.io/$PROJECT_ID/employment-match", "."]
  - name: "gcr.io/cloud-builders/docker"
    args: ["push", "gcr.io/$PROJECT_ID/employment-match"]
```

#### Environment Variables in GCP

Set environment variables in Cloud Run:

```bash
gcloud run services update employment-match \
  --set-env-vars GEMINI_API_KEY=your-key-here
```

### AWS

#### Update ECS Task Definition

Add environment variables to your ECS task definition:

```json
{
  "environment": [
    {
      "name": "GEMINI_API_KEY",
      "value": "your-gemini-api-key"
    }
  ]
}
```

#### Update Lambda (if applicable)

For Lambda deployments, update your deployment package:

```bash
# Include new dependencies
pip install -r requirements.txt -t ./package
cp -r employment_match ./package/
```

### Azure

#### Update App Service Configuration

Add application settings in Azure App Service:

```bash
az webapp config appsettings set \
  --name your-app-name \
  --resource-group your-resource-group \
  --settings GEMINI_API_KEY=your-key-here
```

## Step 6: Testing Deployment

### Health Check

Test the basic health endpoint:

```bash
curl https://your-domain.com/health
```

### Authentication Test

Test company login:

```bash
curl -X POST https://your-domain.com/login/company \
  -H "Content-Type: application/json" \
  -d '{"email": "company@example.com", "password": "password"}'
```

### Chat Integration Test

Test the chat endpoints:

```bash
# 1. Get access token
TOKEN=$(curl -s -X POST https://your-domain.com/login/company \
  -H "Content-Type: application/json" \
  -d '{"email": "company@example.com", "password": "password"}' | \
  jq -r '.access_token')

# 2. Configure Gemini
curl -X POST https://your-domain.com/chat/configure-gemini \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-gemini-api-key"}'

# 3. Test chat
curl -X POST https://your-domain.com/chat/message \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What jobs did I post?"}'
```

## Step 7: Monitoring and Logging

### Enable Logging

Ensure your cloud platform captures application logs:

```python
# In your application
import logging
logging.basicConfig(level=logging.INFO)
```

### Monitor Key Metrics

- API response times
- Database query performance
- Gemini API usage
- Error rates

### Set Up Alerts

Configure alerts for:

- High error rates
- Gemini API failures
- Database connection issues
- Memory/CPU usage

## Step 8: Security Considerations

### API Key Security

- Store Gemini API key in environment variables
- Never commit API keys to version control
- Use cloud platform secret management if available

### Access Control

- All chat endpoints require company authentication
- Verify JWT tokens on all requests
- Implement rate limiting if needed

### Data Privacy

- HR assistant only accesses company's own data
- No data is shared between companies
- Temporary ChromaDB files are cleaned up

## Step 9: Performance Optimization

### Resource Allocation

- Monitor memory usage (ChromaDB can be memory-intensive)
- Consider increasing CPU/memory for chat-heavy usage
- Use connection pooling for database connections

### Caching Strategy

- ChromaDB provides vector search caching
- Consider Redis for session caching if needed
- Implement response caching for static data

### Scaling Considerations

- Each company gets its own HR assistant instance
- Consider horizontal scaling for multiple companies
- Monitor database connection limits

## Troubleshooting

### Common Issues

1. **ChromaDB Installation Failed**

   ```bash
   # Try installing with specific version
   pip install chromadb==0.4.15
   ```

2. **Gemini API Errors**

   - Check API key validity
   - Verify internet connectivity
   - Check API quotas and limits

3. **Database Connection Issues**

   - Verify DATABASE_URL is correct
   - Check database permissions
   - Ensure connection pool settings

4. **Memory Issues**
   - Monitor memory usage
   - Consider increasing container memory
   - Implement data cleanup routines

### Debug Commands

```bash
# Check if dependencies are installed
pip list | grep -E "(chromadb|google-generativeai)"

# Test Gemini API directly
python -c "import google.generativeai as genai; genai.configure(api_key='your-key'); print('OK')"

# Check database connection
python -c "from employment_match.database import get_db; print('DB OK')"
```

## Rollback Plan

If issues occur, you can rollback by:

1. **Revert Code Changes**: Deploy previous version without chat integration
2. **Remove Environment Variables**: Remove GEMINI_API_KEY
3. **Clean Up Dependencies**: Remove chromadb from requirements.txt

## Support

For deployment issues:

1. Check cloud platform logs
2. Verify environment variables
3. Test with the provided test script
4. Review the comprehensive documentation in `docs/CHAT_INTEGRATION.md`

The HR Assistant Chat Integration is designed to be a non-breaking addition to your existing Employment Match API, providing enhanced functionality while maintaining backward compatibility.
