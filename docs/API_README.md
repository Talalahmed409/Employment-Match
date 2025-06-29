# Employment Match FastAPI

A comprehensive FastAPI application that provides AI-powered skill extraction and matching capabilities for job candidates and requirements.

## Features

- **Skill Extraction**: Extract skills from job descriptions and CVs (text or PDF)
- **Skill Standardization**: Map skills to ESCO taxonomy using AI
- **Skill Matching**: Match CV skills against job requirements
- **Complete Workflow**: End-to-end matching process
- **Web Interface**: Modern HTML frontend for easy testing
- **API Documentation**: Auto-generated OpenAPI docs

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Create a `.env` file with your Gemini API key:

```bash
echo "GEMINI_API_KEY=your-gemini-api-key-here" > .env
```

### 3. Prepare Data (if not already done)

```bash
# Convert ESCO CSV to JSON
python convert_esco_to_json.py

# Generate embeddings
python generate_embeddings.py
```

### 4. Start the Server

```bash
python start_server.py
```

Or directly with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Web Interface**: http://localhost:8000/ui
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Core Endpoints

#### 1. Extract Job Skills

```http
POST /extract-job-skills
Content-Type: application/json

{
  "job_description": "We are seeking a Software Engineer...",
  "similarity_threshold": 0.6,
  "fuzzy_threshold": 90
}
```

#### 2. Extract CV Skills (Text)

```http
POST /extract-cv-skills-text
Content-Type: application/json

{
  "cv_text": "EXPERIENCE\nSoftware Engineer...",
  "similarity_threshold": 0.4,
  "fuzzy_threshold": 90
}
```

#### 3. Extract CV Skills (PDF)

```http
POST /extract-cv-skills-pdf
Content-Type: multipart/form-data

file: [PDF file]
similarity_threshold: 0.4
fuzzy_threshold: 90
```

#### 4. Match Skills

```http
POST /match-skills
Content-Type: application/json

{
  "cv_skills": ["Python", "JavaScript", "SQL"],
  "job_skills": ["Python", "Java", "SQL", "Agile"],
  "similarity_threshold": 0.3,
  "fuzzy_threshold": 80
}
```

#### 5. Complete Matching Workflow

```http
POST /complete-matching
Content-Type: multipart/form-data

job_description: "We are seeking a Software Engineer..."
cv_text: "EXPERIENCE\nSoftware Engineer..."
# OR cv_file: [PDF file]
job_similarity_threshold: 0.6
cv_similarity_threshold: 0.4
match_similarity_threshold: 0.3
```

### Utility Endpoints

#### Health Check

```http
GET /health
```

#### ESCO Skills Info

```http
GET /esco-skills
```

#### Setup Data

```http
POST /setup-data
```

## Configuration

### Thresholds

- **Similarity Threshold** (0.0-1.0): Controls embedding-based matching sensitivity

  - Higher values = more strict matching
  - Lower values = more lenient matching

- **Fuzzy Threshold** (0-100): Controls fuzzy string matching sensitivity
  - Higher values = more strict matching
  - Lower values = more lenient matching

### Default Values

- Job Skills Extraction: similarity=0.6, fuzzy=90
- CV Skills Extraction: similarity=0.4, fuzzy=90
- Skill Matching: similarity=0.3, fuzzy=80

## Response Formats

### Skills Response

```json
{
  "standardized": ["Python (computer programming)", "SQL"],
  "raw": ["Python", "SQL"]
}
```

### Match Response

```json
{
  "match_score": 75.0,
  "matched_skills": [
    {
      "cv_skill": "Python",
      "job_skill": "Python",
      "similarity": 0.95
    }
  ],
  "missing_skills": ["Java"],
  "extra_skills": ["JavaScript"]
}
```

## Testing

### Using the Web Interface

1. Open http://localhost:8000/ui
2. Choose the appropriate tab for your use case
3. Fill in the required information
4. Click the submit button
5. View results in real-time

### Using the API Documentation

1. Open http://localhost:8000/docs
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

### Using the Test Script

```bash
python test_api.py
```

## Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**

   - Create a `.env` file with your API key
   - Restart the server

2. **"Models not properly loaded"**

   - Check if data files exist in `data/` directory
   - Run the setup scripts if needed

3. **"ESCO skills not loaded"**

   - Run `python convert_esco_to_json.py`
   - Ensure `data/esco_skills.json` exists

4. **"Embeddings not found"**

   - Run `python generate_embeddings.py`
   - Ensure `data/esco_embeddings.npy` exists

5. **"Module object is not callable"**
   - This has been fixed in the latest version
   - Restart the server if you see this error

### Performance Tips

- Use appropriate similarity thresholds for your use case
- For large-scale processing, consider batch operations
- Monitor memory usage when processing large PDFs

## Development

### Project Structure

```
Employment_Match/
├── main.py                 # FastAPI application
├── start_server.py         # Server startup script
├── test_api.py            # API testing script
├── static/
│   └── index.html         # Web interface
├── data/                  # Data files
├── extract_skills.py      # Job skills extraction
├── extract_cv_skills.py   # CV skills extraction
├── match_skills.py        # Skill matching
├── generate_embeddings.py # Embedding generation
└── convert_esco_to_json.py # Data conversion
```

### Adding New Endpoints

1. Define Pydantic models for request/response
2. Create the endpoint function
3. Add proper error handling
4. Update this documentation

### Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)

## License

This project is licensed under the same terms as the original Employment Match project.
