# API Quick Reference

## 🔐 Authentication

| Method | Endpoint              | User Type | Description                |
| ------ | --------------------- | --------- | -------------------------- |
| POST   | `/register/company`   | -         | Register company account   |
| POST   | `/register/candidate` | -         | Register candidate account |
| POST   | `/login/company`      | -         | Login company              |
| POST   | `/login/candidate`    | -         | Login candidate            |

## 🏢 Company Endpoints

| Method | Endpoint                    | Description                           |
| ------ | --------------------------- | ------------------------------------- |
| POST   | `/jobs`                     | Create job posting                    |
| GET    | `/applications/company`     | Get all applications for company jobs |
| PUT    | `/applications/{id}/status` | Update application status             |
| GET    | `/jobs/{id}/top-candidates` | Get top candidates by match score     |

## 👤 Candidate Endpoints

| Method | Endpoint           | Description                        |
| ------ | ------------------ | ---------------------------------- |
| POST   | `/upload-cv`       | Upload CV PDF for skill extraction |
| POST   | `/jobs/{id}/apply` | Apply to job posting               |
| GET    | `/applications/my` | Get candidate's applications       |

## 🌐 Public Endpoints

| Method | Endpoint     | Description                 |
| ------ | ------------ | --------------------------- |
| GET    | `/health`    | API health check            |
| GET    | `/jobs`      | Get all active job postings |
| GET    | `/jobs/{id}` | Get specific job posting    |

## 🔧 Utility Endpoints

| Method | Endpoint                  | Description                         |
| ------ | ------------------------- | ----------------------------------- |
| POST   | `/extract-job-skills`     | Extract skills from job description |
| POST   | `/extract-cv-skills-text` | Extract skills from CV text         |
| POST   | `/match-skills`           | Match CV skills vs job skills       |
| POST   | `/setup-data`             | Initialize ESCO data                |
| GET    | `/esco-skills`            | Get ESCO skills info                |

---

## 📋 Common Request Headers

```
Authorization: Bearer <token>
Content-Type: application/json
```

## 📊 Response Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## 📝 Application Statuses

- `pending` - Awaiting review
- `under_review` - Being reviewed
- `accepted` - Accepted
- `rejected` - Rejected
- `withdrawn` - Withdrawn

---

**Full documentation**: See `API_ENDPOINTS_REFERENCE.md` for detailed examples and usage.
