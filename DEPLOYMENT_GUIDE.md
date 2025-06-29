# Employment Match - Google Cloud Run Deployment Guide

This guide will walk you through deploying the Employment Match application to Google Cloud Run with a Neon database.

## Prerequisites

1. **Google Cloud Account**: You need a Google Cloud account with billing enabled
2. **Google Cloud SDK**: Install the Google Cloud CLI
3. **Docker**: Install Docker on your local machine
4. **Neon Database**: Create a Neon database account and database
5. **Python 3.11+**: For local development and testing

## Step 1: Set Up Google Cloud Project

### 1.1 Create a New Project

```bash
# Create a new project (replace with your desired project name)
gcloud projects create employment-match-final --name="Employment Match Final"

# Set the project as active
gcloud config set project employment-match-final
```

### 1.2 Enable Required APIs

```bash
# Enable required Google Cloud APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 1.3 Authenticate with Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Configure Docker to use gcloud as a credential helper
gcloud auth configure-docker
```

## Step 2: Set Up Neon Database

### 2.1 Create Neon Account

1. Go to [neon.tech](https://neon.tech)
2. Sign up for a free account
3. Create a new project

### 2.2 Create Database

1. In your Neon project, create a new database
2. Note down the connection string (it will look like):
   ```
   postgresql://neondb_owner:npg_ZoB1Unqpc3rJ@ep-red-salad-a20vuj1d.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```

### 2.3 Set Up Database Tables

```bash
# Set your Neon database URL
export DATABASE_URL="postgresql://neondb_owner:npg_ZoB1Unqpc3rJ@ep-red-salad-a20vuj1d.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Run the database setup script
python setup_neon_database.py
```

## Step 3: Configure Environment Variables

### 3.1 Set Required Environment Variables

```bash
# Database URL (from Neon)
export DATABASE_URL="postgresql://neondb_owner:npg_ZoB1Unqpc3rJ@ep-red-salad-a20vuj1d.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Secret key for JWT tokens (generate a secure random string)
export SECRET_KEY="your-super-secret-key-here"

# Optional: Gemini API key for enhanced features
export GEMINI_API_KEY="your-gemini-api-key"
```

### 3.2 Generate a Secure Secret Key

```bash
# Generate a secure random secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 4: Deploy to Google Cloud Run

### 4.1 Update Project Configuration

The `deploy.sh` script is already configured with:

- Project ID: `employment-match-final`
- Region: `europe-north1`
- Service Name: `employment-match-final`

### 4.2 Run the Deployment Script

```bash
# Make the script executable (if not already)
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

### 4.3 Manual Deployment (Alternative)

If you prefer manual deployment:

```bash
# Build the Docker image
docker build -t gcr.io/employment-match-final/employment-match-final .

# Push to Google Container Registry
docker push gcr.io/employment-match-final/employment-match-final

# Deploy to Cloud Run
gcloud run deploy employment-match-final \
    --image gcr.io/employment-match-final/employment-match-final \
    --region europe-north1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "DATABASE_URL=$DATABASE_URL,SECRET_KEY=$SECRET_KEY,GEMINI_API_KEY=$GEMINI_API_KEY"
```

## Step 5: Verify Deployment

### 5.1 Check Service Status

```bash
# Get the service URL
gcloud run services describe employment-match-final --region=europe-north1 --format="value(status.url)"

# Test the health endpoint
curl https://your-service-url/health
```

### 5.2 Access API Documentation

- Open your service URL in a browser
- Navigate to `/docs` for Swagger UI documentation
- Navigate to `/redoc` for ReDoc documentation

## Step 6: Set Up CI/CD (Optional)

### 6.1 Configure Cloud Build

1. Go to Google Cloud Console > Cloud Build
2. Create a new trigger
3. Connect your GitHub repository
4. Use the `cloudbuild.yaml` configuration

### 6.2 Set Up Substitution Variables

In your Cloud Build trigger, set these substitution variables:

- `_DATABASE_URL`: `postgresql://neondb_owner:npg_ZoB1Unqpc3rJ@ep-red-salad-a20vuj1d.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
- `_SECRET_KEY`: Your secret key
- `_GEMINI_API_KEY`: Your Gemini API key (optional)

## Step 7: Custom Domain (Optional)

### 7.1 Map Custom Domain

```bash
# Map a custom domain to your service
gcloud run domain-mappings create \
    --service=employment-match-final \
    --domain=your-domain.com \
    --region=europe-north1
```

### 7.2 SSL Certificate

Cloud Run automatically provisions SSL certificates for custom domains.

## Monitoring and Logging

### 7.1 View Logs

```bash
# View service logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=employment-match-final" --limit=50
```

### 7.2 Set Up Monitoring

1. Go to Google Cloud Console > Monitoring
2. Create dashboards for your Cloud Run service
3. Set up alerts for errors and performance metrics

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

- Verify your Neon database URL is correct
- Check if your Neon database is accessible from Google Cloud
- Ensure the database user has proper permissions

#### 2. Memory Issues

- Increase memory allocation in Cloud Run configuration
- Optimize your application for memory usage

#### 3. Cold Start Issues

- Consider using Cloud Run with minimum instances > 0
- Optimize your Docker image size

#### 4. Timeout Issues

- Increase the timeout value in Cloud Run configuration
- Optimize your application response times

### Debug Commands

```bash
# Check service status
gcloud run services describe employment-match-final --region=europe-north1

# View recent logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=employment-match-final" --limit=10

# Test database connection locally
python setup_neon_database.py
```

## Cost Optimization

### 7.1 Resource Optimization

- Use appropriate memory and CPU allocation
- Set maximum instances to control costs
- Use minimum instances = 0 for development

### 7.2 Neon Database Optimization

- Use Neon's autoscaling features
- Monitor query performance
- Use connection pooling when needed

## Security Considerations

### 7.1 Environment Variables

- Never commit secrets to version control
- Use Google Secret Manager for sensitive data
- Rotate secrets regularly

### 7.2 Network Security

- Consider using VPC connector for private networking
- Implement proper authentication and authorization
- Use HTTPS for all communications

## Next Steps

1. **Set up monitoring and alerting**
2. **Implement proper authentication**
3. **Add rate limiting**
4. **Set up backup strategies**
5. **Implement CI/CD pipeline**
6. **Add custom domain and SSL**
7. **Optimize performance and costs**

## Support

For issues related to:

- **Google Cloud Run**: Check [Google Cloud documentation](https://cloud.google.com/run/docs)
- **Neon Database**: Check [Neon documentation](https://neon.tech/docs)
- **Application**: Check the project README and API documentation

## Useful Commands

```bash
# Update service with new environment variables
gcloud run services update employment-match-final \
    --region=europe-north1 \
    --set-env-vars "NEW_VAR=value"

# Scale service
gcloud run services update employment-match-final \
    --region=europe-north1 \
    --max-instances=20

# View service configuration
gcloud run services describe employment-match-final --region=europe-north1
```
