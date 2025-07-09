# Google OAuth Deployment Checklist

## Pre-Deployment Checklist

### ✅ Environment Variables

- [ ] `DATABASE_URL` is set to your Neon database URL
- [ ] `SECRET_KEY` is set to a secure random string
- [ ] `GOOGLE_CLIENT_ID` is set (default: 248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com)
- [ ] `GEMINI_API_KEY` is set (optional)

### ✅ Database Migration

- [ ] Run `python migrate_neon_google_oauth.py` to add Google OAuth fields
- [ ] Verify migration completed successfully
- [ ] Check that `google_id` and `is_google_user` columns exist in both tables

### ✅ Code Changes

- [ ] All Google OAuth code is committed to git
- [ ] Dependencies are updated in `requirements.txt`
- [ ] API endpoints are added (`/auth/google`)
- [ ] Database models are updated

## Deployment Steps

### 1. Quick Deployment (Recommended)

```bash
# Set environment variables
export DATABASE_URL="your-neon-database-url"
export SECRET_KEY="your-secret-key"
export GOOGLE_CLIENT_ID="248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com"

# Run the Google OAuth deployment script
./deploy_with_google_oauth.sh
```

### 2. Manual Deployment

```bash
# Run database migration
python migrate_neon_google_oauth.py

# Build and deploy
docker build -t gcr.io/employment-match-final/employment-match-final .
docker push gcr.io/employment-match-final/employment-match-final

gcloud run deploy employment-match-final \
    --image gcr.io/employment-match-final/employment-match-final \
    --region europe-north1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "DATABASE_URL=$DATABASE_URL,SECRET_KEY=$SECRET_KEY,GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID"
```

## Post-Deployment Verification

### ✅ Health Check

- [ ] Service is running: `curl https://your-service-url/health`
- [ ] API documentation is accessible: `https://your-service-url/docs`

### ✅ Google OAuth Endpoint

- [ ] Endpoint is accessible: `POST https://your-service-url/auth/google`
- [ ] Returns proper error for invalid token
- [ ] Accepts valid Google ID tokens

### ✅ Database Connection

- [ ] Application can connect to Neon database
- [ ] Google OAuth fields are accessible
- [ ] User creation/linking works correctly

## Testing Checklist

### Frontend Integration

- [ ] Google Sign-In button works
- [ ] Token is sent to `/auth/google` endpoint
- [ ] JWT token is received and stored
- [ ] User can access protected endpoints

### User Flows

- [ ] New user sign-up with Google works
- [ ] Existing user sign-in with Google works
- [ ] Email/password authentication still works
- [ ] User type selection (company/candidate) works

## Troubleshooting

### Common Issues

- [ ] **Database migration fails**: Check Neon connection and permissions
- [ ] **Google OAuth errors**: Verify client ID and token format
- [ ] **Deployment fails**: Check environment variables and Docker build
- [ ] **CORS issues**: Verify frontend domain is allowed

### Debug Commands

```bash
# Check service logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=employment-match-final"

# Test database connection
python -c "from employment_match.database import get_db; next(get_db())"

# Test Google OAuth endpoint
curl -X POST "https://your-service-url/auth/google" \
  -H "Content-Type: application/json" \
  -d '{"token":"test","user_type":"candidate"}'
```

## Security Checklist

### ✅ Environment Variables

- [ ] `SECRET_KEY` is strong and unique
- [ ] `DATABASE_URL` is secure and private
- [ ] `GOOGLE_CLIENT_ID` is correct for your domain

### ✅ Database Security

- [ ] Neon database has proper access controls
- [ ] Connection uses SSL/TLS
- [ ] Database user has minimal required permissions

### ✅ API Security

- [ ] JWT tokens are properly validated
- [ ] Google tokens are verified server-side
- [ ] CORS is properly configured
- [ ] Rate limiting is in place (if needed)

## Monitoring

### ✅ Logs and Metrics

- [ ] Cloud Run logs are being collected
- [ ] Error monitoring is set up
- [ ] Performance metrics are tracked
- [ ] Google OAuth success/failure rates are monitored

### ✅ Alerts

- [ ] Service availability alerts
- [ ] Error rate alerts
- [ ] Database connection alerts
- [ ] Google OAuth failure alerts

## Final Verification

### ✅ Production Ready

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Frontend integration is complete
- [ ] Monitoring is active
- [ ] Backup strategy is in place

### ✅ User Acceptance

- [ ] Test with real Google accounts
- [ ] Verify user experience is smooth
- [ ] Check that all user flows work
- [ ] Confirm error handling is user-friendly
