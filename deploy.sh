#!/bin/bash

# Employment Match - Google Cloud Run Deployment Script
# This script deploys the application to Google Cloud Run with Neon database

set -e

# Configuration
PROJECT_ID="employment-match-final"  # Replace with your Google Cloud project ID
REGION="europe-north1"
SERVICE_NAME="employment-match-final"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Employment Match - Google Cloud Run Deployment${NC}"
echo "=================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud SDK is not installed. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  You are not authenticated with Google Cloud.${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set the project
echo -e "${YELLOW}📋 Setting Google Cloud project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Check if environment variables are set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL environment variable is not set.${NC}"
    echo "Please set your Neon database URL:"
    echo "export DATABASE_URL='postgresql://neondb_owner:npg_ZoB1Unqpc3rJ@ep-red-salad-a20vuj1d.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo -e "${RED}❌ SECRET_KEY environment variable is not set.${NC}"
    echo "Please set a secret key for JWT tokens:"
    echo "export SECRET_KEY='your-secret-key-here'"
    exit 1
fi

# Build and push the Docker image
echo -e "${YELLOW}🐳 Building and pushing Docker image...${NC}"
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Google Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "DATABASE_URL=$DATABASE_URL,SECRET_KEY=$SECRET_KEY,GEMINI_API_KEY=$GEMINI_API_KEY" \
    --port 8080

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo "=================================================="
echo -e "${GREEN}🌐 Service URL: $SERVICE_URL${NC}"
echo -e "${GREEN}📚 API Documentation: $SERVICE_URL/docs${NC}"
echo -e "${GREEN}🔍 Health Check: $SERVICE_URL/health${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Test the API endpoints using the documentation"
echo "2. Set up a custom domain if needed"
echo "3. Configure monitoring and logging"
echo "4. Set up CI/CD pipeline with Cloud Build"

# Optional: Set up custom domain
read -p "Do you want to set up a custom domain? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🌐 To set up a custom domain, run:${NC}"
    echo "gcloud run domain-mappings create --service=$SERVICE_NAME --domain=your-domain.com --region=$REGION"
fi 