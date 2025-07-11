# HR Assistant Chat Integration

## Overview

The HR Assistant Chat Integration provides AI-powered conversational interface for companies to manage their hiring process. It integrates with your existing Employment Match API to provide intelligent insights about candidates, applications, and hiring decisions.

## Features

- **AI-Powered Chat**: Natural language interface using Gemini AI
- **Intent Recognition**: Automatically detects user intent from messages
- **Real-time Data**: Works with your existing job postings and applications
- **Smart Insights**: Provides candidate analysis and recommendations
- **Interview Questions**: Generates relevant interview questions for positions
- **Hiring Analytics**: Summary statistics and best candidate identification

## API Endpoints

### 1. Configure Gemini AI

**POST** `/chat/configure-gemini`

Configure the Gemini AI model for the HR assistant.

**Headers:** `Authorization: Bearer <company_token>`

**Request Body:**

```json
{
  "api_key": "your-gemini-api-key"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Gemini configured successfully"
}
```

### 2. Chat with Assistant

**POST** `/chat/message`

Send a message to the HR assistant and get an AI-powered response.

**Headers:** `Authorization: Bearer <company_token>`

**Request Body:**

```json
{
  "message": "What jobs did I post?"
}
```

**Response:**

```json
{
  "response": "📋 **Your Posted Jobs:**\n\n• **Machine Learning Engineer** - 4 applications",
  "intent": "posted_jobs"
}
```

### 3. Get Hiring Summary

**GET** `/chat/summary`

Get a summary of hiring statistics.

**Headers:** `Authorization: Bearer <company_token>`

**Response:**

```json
{
  "total_jobs": 1,
  "total_applications": 4,
  "status_counts": {
    "pending": 4,
    "accepted": 0,
    "rejected": 0
  }
}
```

### 4. Get Best Candidate Analysis

**GET** `/chat/best-candidate`

Get AI analysis of the best candidate.

**Headers:** `Authorization: Bearer <company_token>`

**Response:**

```json
{
  "analysis": "🏆 **Best Candidate Analysis**\n\n**Top Candidate:** John Doe\n**Match Score:** 95.0%\n**Position:** Software Engineer\n**Email:** john@example.com"
}
```

### 5. Get Interview Questions

**GET** `/chat/interview-questions/{job_title}`

Generate interview questions for a specific job.

**Headers:** `Authorization: Bearer <company_token>`

**Response:**

```json
{
  "questions": "1. Can you describe your experience with Python and FastAPI?\n2. How do you approach debugging complex issues?\n3. Tell me about a challenging project you worked on..."
}
```

## Supported Chat Intents

The HR assistant recognizes the following intents from user messages:

### Job Management

- **posted_jobs**: "What jobs did I post?", "Show my jobs", "List job postings"
- **job_applications**: "Who applied for [job title]?", "Show applicants"

### Candidate Analysis

- **show_scores**: "Show me scores", "Application scores", "Candidate ratings"
- **highest_scorer**: "Who scored highest?", "Best score", "Top scorer"
- **best_candidate**: "Who is the best candidate?", "Best applicant", "Who should I hire"
- **compare_candidates**: "Compare candidates", "Candidate comparison"

### Hiring Process

- **interview_questions**: "Generate interview questions", "Questions for [job]"
- **hiring_summary**: "Hiring summary", "Statistics", "Overview"

### General Queries

- **general**: Any other questions about hiring, candidates, or the process

## Example Usage

### Basic Chat Flow

```python
import requests

# 1. Login as company
login_response = requests.post("http://localhost:8080/login/company", json={
    "email": "company@example.com",
    "password": "password123"
})
access_token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}

# 2. Configure Gemini
requests.post("http://localhost:8080/chat/configure-gemini",
    json={"api_key": "your-gemini-api-key"},
    headers=headers
)

# 3. Chat with assistant
chat_response = requests.post("http://localhost:8080/chat/message",
    json={"message": "Who is my best candidate?"},
    headers=headers
)
print(chat_response.json()["response"])
```

### Common Chat Commands

| Command                              | Response                                    |
| ------------------------------------ | ------------------------------------------- |
| "What jobs did I post?"              | List of posted jobs with application counts |
| "Show me scores for applicants"      | Detailed application scores and status      |
| "Who is the highest scorer?"         | Best candidate with match score             |
| "Who is the best candidate?"         | AI analysis of top candidate                |
| "Compare candidates for my job"      | Side-by-side candidate comparison           |
| "Who applied for Software Engineer?" | List of applicants for specific job         |
| "Generate interview questions"       | AI-generated questions for job              |
| "Show hiring summary"                | Statistics and overview                     |

## Integration with Existing System

The HR Assistant integrates seamlessly with your existing Employment Match system:

### Data Sources

- **Job Postings**: Uses existing job postings from your database
- **Applications**: Analyzes real application data and match scores
- **Candidates**: Accesses candidate profiles and skills
- **Skill Matches**: Utilizes existing skill matching results

### Authentication

- Uses the same JWT authentication as your existing API
- Requires company-level access (not available to candidates)
- Maintains session state for efficient data loading

### Database Integration

- Direct database queries for real-time data
- No external API calls required
- Maintains data consistency with your existing system

## Deployment

### Prerequisites

1. **Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **ChromaDB**: Added to requirements.txt
3. **Database Access**: HR assistant needs database session

### Environment Variables

```bash
# Required for Gemini AI
GEMINI_API_KEY=your-gemini-api-key

# Existing variables
DATABASE_URL=your-database-url
SECRET_KEY=your-secret-key
```

### Installation

```bash
# Install new dependencies
pip install -r requirements.txt

# Start the server
python start_server.py
```

### Testing

```bash
# Run the test script
python test_chat_integration.py
```

## Security Considerations

1. **API Key Management**: Store Gemini API key securely
2. **Authentication**: All endpoints require valid company authentication
3. **Data Access**: Only company data is accessible to the assistant
4. **Session Management**: Database sessions are properly managed and cleaned up

## Performance Optimization

1. **Lazy Loading**: Data is loaded only when needed
2. **Caching**: ChromaDB provides vector search caching
3. **Connection Pooling**: Database connections are reused
4. **Background Processing**: Heavy operations are handled asynchronously

## Troubleshooting

### Common Issues

1. **Gemini Configuration Failed**

   - Check API key validity
   - Verify internet connectivity
   - Ensure API key has proper permissions

2. **No Data Available**

   - Verify company has posted jobs
   - Check for applications in the system
   - Ensure database connection is working

3. **Chat Not Responding**
   - Check if Gemini is configured
   - Verify authentication token
   - Check server logs for errors

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **Multi-language Support**: Support for different languages
2. **Advanced Analytics**: More detailed candidate insights
3. **Automated Actions**: Ability to perform actions via chat
4. **Integration APIs**: Connect with external HR systems
5. **Custom Training**: Company-specific AI model training

## Support

For issues or questions about the HR Assistant Chat Integration:

1. Check the server logs for error messages
2. Verify all dependencies are installed
3. Test with the provided test script
4. Review the API documentation at `/docs`

The HR Assistant Chat Integration provides a powerful, AI-driven interface for managing your hiring process, making it easier to identify the best candidates and make informed hiring decisions.
