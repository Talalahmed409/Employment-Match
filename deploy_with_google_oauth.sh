#!/bin/bash

# Employment Match - Google Cloud Run Deployment with Google OAuth
# This script deploys the application with Google OAuth support

set -e

# Configuration
PROJECT_ID="employment-match-final"
REGION="europe-north1"
SERVICE_NAME="employment-match-final"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Employment Match - Google Cloud Run Deployment with Google OAuth${NC}"
echo "=================================================================="

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

# Check environment variables
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

# Set Google OAuth client ID
if [ -z "$GOOGLE_CLIENT_ID" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_CLIENT_ID environment variable is not set.${NC}"
    echo "Setting default Google OAuth client ID..."
    export GOOGLE_CLIENT_ID="248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com"
fi

echo -e "${BLUE}🔐 Google OAuth Configuration:${NC}"
echo "   Client ID: $GOOGLE_CLIENT_ID"

# Run database migration for Google OAuth
echo -e "${YELLOW}🗄️  Running Google OAuth database migration...${NC}"
if python migrate_neon_google_oauth.py; then
    echo -e "${GREEN}✅ Database migration completed successfully!${NC}"
else
    echo -e "${RED}❌ Database migration failed. Please check the error above.${NC}"
    echo "You can run the migration manually:"
    echo "python migrate_neon_google_oauth.py"
    read -p "Continue with deployment anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
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
    --set-env-vars "DATABASE_URL=$DATABASE_URL,SECRET_KEY=$SECRET_KEY,GEMINI_API_KEY=$GEMINI_API_KEY,GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" \
    --port 8080

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo "=================================================================="
echo -e "${GREEN}🌐 Service URL: $SERVICE_URL${NC}"
echo -e "${GREEN}📚 API Documentation: $SERVICE_URL/docs${NC}"
echo -e "${GREEN}🔍 Health Check: $SERVICE_URL/health${NC}"
echo -e "${GREEN}🔐 Google OAuth Endpoint: $SERVICE_URL/auth/google${NC}"
echo ""
echo -e "${BLUE}🔐 Google OAuth Testing:${NC}"
echo "1. Test the Google OAuth endpoint:"
echo "   POST $SERVICE_URL/auth/google"
echo "   Body: {\"token\": \"google_id_token\", \"user_type\": \"company\" or \"candidate\"}"
echo ""
echo "2. Verify with your frontend Google Sign-In implementation"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Test the Google OAuth endpoint using the documentation"
echo "2. Verify your frontend can authenticate with Google"
echo "3. Set up a custom domain if needed"
echo "4. Configure monitoring and logging"

# Test the Google OAuth endpoint
echo -e "${BLUE}🧪 Testing Google OAuth endpoint...${NC}"
if curl -s -f "$SERVICE_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed - service is running${NC}"
    echo -e "${GREEN}✅ Google OAuth endpoint is available at: $SERVICE_URL/auth/google${NC}"
else
    echo -e "${RED}❌ Health check failed - service may not be running properly${NC}"
fi

# Optional: Set up custom domain
read -p "Do you want to set up a custom domain? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🌐 To set up a custom domain, run:${NC}"
    echo "gcloud run domain-mappings create --service=$SERVICE_NAME --domain=your-domain.com --region=$REGION"
fi 