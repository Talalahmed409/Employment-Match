# Google Cloud Run Deployment with Cloud Storage

This guide explains how to deploy your Employment Match application to Google Cloud Run with proper file storage using Google Cloud Storage.

## File Storage Architecture

### Local Development

- **CV Files**: `uploads/cvs/cv_{candidate_id}_{timestamp}.pdf`
- **Profile Pictures**: `uploads/candidate_pictures/{candidate_id}/profile.{ext}`
- **Background Pictures**: `uploads/company_pictures/{company_id}/background.{ext}`

### Google Cloud Run (Production)

- **CV Files**: `gs://{bucket-name}/cvs/cv_{candidate_id}_{timestamp}.pdf`
- **Profile Pictures**: `gs://{bucket-name}/candidate_pictures/{candidate_id}/profile.{ext}`
- **Background Pictures**: `gs://{bucket-name}/company_pictures/{company_id}/background.{ext}`

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Google Cloud CLI** installed and configured
3. **Docker** installed locally
4. **Service Account** with necessary permissions

## Setup Steps

### 1. Create Google Cloud Storage Bucket

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Create a storage bucket
gsutil mb gs://employment-match-files-$PROJECT_ID

# Make bucket publicly readable (optional, for direct access)
gsutil iam ch allUsers:objectViewer gs://employment-match-files-$PROJECT_ID
```

### 2. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create employment-match-sa \
    --display-name="Employment Match Service Account"

# Get the service account email
SA_EMAIL="employment-match-sa@$PROJECT_ID.iam.gserviceaccount.com"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/cloudsql.client"
```

### 3. Create and Download Service Account Key

```bash
# Create service account key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=$SA_EMAIL
```

### 4. Environment Variables

Create a `.env` file for your Cloud Run deployment:

```env
# Database
DATABASE_URL="postgresql://user:password@host:5432/database"

# JWT Secret
SECRET_KEY="your-super-secret-key-change-in-production"

# Gemini API
GEMINI_API_KEY="your-gemini-api-key"

# Google OAuth
GOOGLE_CLIENT_ID="your-google-client-id"

# Cloud Storage
GCS_BUCKET_NAME="employment-match-files-your-project-id"

# Service Account (for local testing)
GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
```

### 5. Update Dockerfile

Ensure your Dockerfile includes the service account key:

```dockerfile
# Copy service account key
COPY service-account-key.json /app/service-account-key.json
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
```

### 6. Deploy to Cloud Run

```bash
# Build and deploy
gcloud run deploy employment-match \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars="DATABASE_URL=$DATABASE_URL,SECRET_KEY=$SECRET_KEY,GEMINI_API_KEY=$GEMINI_API_KEY,GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID,GCS_BUCKET_NAME=$GCS_BUCKET_NAME" \
    --service-account=$SA_EMAIL \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10
```

## File Access Patterns

### CV Upload

1. User uploads CV via `/upload-cv`
2. File is uploaded to Cloud Storage: `gs://bucket/cvs/cv_{id}_{timestamp}.pdf`
3. Database stores the Cloud Storage path
4. Skills are extracted from the file

### CV Download

1. User requests download via `/download-cv`
2. System generates signed URL for Cloud Storage file
3. User receives download URL with expiration

### Profile Pictures

1. User uploads pictures via `/profile/upload-pictures`
2. Files uploaded to Cloud Storage: `gs://bucket/{user_type}_pictures/{user_id}/profile.{ext}`
3. Database stores Cloud Storage paths
4. Profile responses include the paths

## Security Considerations

### Service Account Permissions

- **Minimum required**: `roles/storage.objectAdmin` for file operations
- **Optional**: `roles/storage.objectViewer` for public read access

### Signed URLs

- CV downloads use signed URLs with 1-hour expiration
- Prevents unauthorized access to user files
- URLs are single-use and time-limited

### File Validation

- File type validation (PDF for CVs, images for pictures)
- File size limits enforced
- Content-Type headers set correctly

## Monitoring and Logging

### Cloud Storage Metrics

```bash
# Monitor bucket usage
gsutil du -sh gs://employment-match-files-$PROJECT_ID

# List files by type
gsutil ls gs://employment-match-files-$PROJECT_ID/cvs/
gsutil ls gs://employment-match-files-$PROJECT_ID/candidate_pictures/
gsutil ls gs://employment-match-files-$PROJECT_ID/company_pictures/
```

### Cloud Run Logs

```bash
# View application logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=employment-match" --limit 50
```

## Cost Optimization

### Storage Classes

- **Standard**: For frequently accessed files (profile pictures)
- **Nearline**: For CVs (accessed less frequently)
- **Coldline**: For archived files

### Lifecycle Management

```bash
# Set lifecycle policy for CV files (move to Nearline after 30 days)
gsutil lifecycle set lifecycle.json gs://employment-match-files-$PROJECT_ID
```

Example `lifecycle.json`:

```json
{
  "rule": [
    {
      "action": { "type": "SetStorageClass", "storageClass": "NEARLINE" },
      "condition": {
        "age": 30,
        "matchesPrefix": ["cvs/"]
      }
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **Permission Denied**

   ```bash
   # Check service account permissions
   gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:$SA_EMAIL"
   ```

2. **File Not Found**

   ```bash
   # Check if file exists in bucket
   gsutil ls gs://employment-match-files-$PROJECT_ID/cvs/
   ```

3. **Authentication Issues**
   ```bash
   # Verify service account key
   gcloud auth activate-service-account --key-file=service-account-key.json
   ```

### Debug Mode

Enable debug logging by setting environment variable:

```bash
export LOG_LEVEL=DEBUG
```

## Migration from Local Storage

If you have existing files in local storage:

```bash
# Upload existing files to Cloud Storage
gsutil -m cp -r uploads/cvs gs://employment-match-files-$PROJECT_ID/
gsutil -m cp -r uploads/candidate_pictures gs://employment-match-files-$PROJECT_ID/
gsutil -m cp -r uploads/company_pictures gs://employment-match-files-$PROJECT_ID/

# Update database paths (run migration script)
python3 migrations/update_file_paths.py
```

## Backup Strategy

### Database Backup

- Neon provides automatic backups
- Manual backups available via Neon dashboard

### File Backup

```bash
# Create backup bucket
gsutil mb gs://employment-match-backup-$PROJECT_ID

# Schedule daily backups
gsutil -m rsync -d -r gs://employment-match-files-$PROJECT_ID gs://employment-match-backup-$PROJECT_ID
```
