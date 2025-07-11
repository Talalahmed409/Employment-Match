# HR Assistant Chat - Quick Reference Guide

## Overview

The Employment Match API now includes an AI-powered HR Assistant with chat functionality. This guide provides quick access to all chat-related features and endpoints.

## Quick Start

### 1. Configure Gemini AI

```bash
curl -X POST "https://your-api-url/chat/configure-gemini" \
  -H "Authorization: Bearer YOUR_COMPANY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your_gemini_api_key"}'
```

### 2. Start Chatting

```bash
curl -X POST "https://your-api-url/chat/message" \
  -H "Authorization: Bearer YOUR_COMPANY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me the best candidates for Software Engineer"}'
```

## API Endpoints

### Chat Configuration

| Method | Endpoint                 | Description                      |
| ------ | ------------------------ | -------------------------------- |
| POST   | `/chat/configure-gemini` | Configure Gemini AI with API key |

### Chat Interaction

| Method | Endpoint        | Description                  |
| ------ | --------------- | ---------------------------- |
| POST   | `/chat/message` | Send message to HR assistant |

### Hiring Insights

| Method | Endpoint                                | Description                 |
| ------ | --------------------------------------- | --------------------------- |
| GET    | `/chat/summary`                         | Get hiring summary          |
| GET    | `/chat/best-candidate`                  | Get best candidate analysis |
| GET    | `/chat/interview-questions/{job_title}` | Get interview questions     |

## Supported Chat Intents

### Job Management

- "Show me all my job postings"
- "How many applications do I have for [job title]?"
- "Create a new job posting for [position]"

### Candidate Analysis

- "Who are the best candidates for [job title]?"
- "Compare candidates for [job title]"
- "Show me candidates with [skill]"

### Application Management

- "What's the status of applications for [job title]?"
- "Update application status for [candidate] to [status]"
- "Show me recent applications"

### Hiring Insights

- "Give me a hiring summary"
- "What are the top skills in demand?"
- "Show me hiring trends"

### Interview Preparation

- "Generate interview questions for [job title]"
- "What should I ask [candidate] about [skill]?"
- "Create interview questions for [position]"

## Example Conversations

### Scenario 1: Hiring Summary

```
User: "Give me a summary of my hiring situation"
Assistant: "Based on your current data, you have:
- 5 active job postings
- 23 total applications
- 8 applications pending review
- 3 candidates with >90% skill match
- Most applications for 'Software Engineer' position"
```

### Scenario 2: Candidate Comparison

```
User: "Compare the top candidates for Software Engineer"
Assistant: "Here are your top 3 candidates for Software Engineer:

1. John Smith (95% match)
   - Matched skills: Python, JavaScript, React, AWS
   - Missing skills: Kubernetes
   - Applied: 2 days ago

2. Sarah Johnson (92% match)
   - Matched skills: Python, JavaScript, Docker, Git
   - Missing skills: AWS, React
   - Applied: 1 week ago

3. Mike Davis (88% match)
   - Matched skills: Python, Java, SQL, Git
   - Missing skills: JavaScript, React, AWS
   - Applied: 3 days ago"
```

### Scenario 3: Interview Questions

```
User: "Generate interview questions for Data Scientist"
Assistant: "Here are interview questions for Data Scientist:

Technical Questions:
1. Explain the difference between supervised and unsupervised learning
2. How would you handle missing data in a dataset?
3. Describe a time you used machine learning to solve a business problem
4. What's your experience with Python libraries like pandas, scikit-learn?

Behavioral Questions:
1. Tell me about a project where you had to work with a large dataset
2. How do you stay updated with the latest ML/AI trends?
3. Describe a situation where you had to explain complex technical concepts to non-technical stakeholders

Case Study Questions:
1. How would you approach building a recommendation system?
2. What metrics would you use to evaluate a classification model?
3. How would you design an A/B testing framework?"
```

## Response Format

### Chat Response

```json
{
  "response": "AI assistant response text",
  "intent": "detected_intent_type"
}
```

### Hiring Summary

```json
{
  "total_jobs": 5,
  "total_applications": 23,
  "pending_applications": 8,
  "top_candidates": [
    {
      "name": "John Smith",
      "job_title": "Software Engineer",
      "match_score": 95.0,
      "applied_at": "2024-01-15T10:30:00Z"
    }
  ],
  "skills_in_demand": ["Python", "JavaScript", "React"],
  "recent_activity": "3 new applications in the last 24 hours"
}
```

### Best Candidate Analysis

```json
{
  "analysis": "Detailed analysis of the best candidate including skills, experience, and recommendations"
}
```

## Error Handling

### Common Error Responses

```json
{
  "response": "❌ Error: Gemini AI not configured. Please configure Gemini first.",
  "intent": "error"
}
```

```json
{
  "response": "❌ Error: No applications found for the specified job.",
  "intent": "error"
}
```

```json
{
  "response": "❌ Error: Database connection failed.",
  "intent": "error"
}
```

## Authentication

All chat endpoints require company authentication:

```bash
Authorization: Bearer YOUR_COMPANY_JWT_TOKEN
```

## Rate Limiting

- Chat messages: 10 requests per minute per company
- Configuration: 5 requests per minute per company
- Summary/analysis: 20 requests per minute per company

## Performance Tips

1. **Configure Gemini once** - Don't reconfigure on every request
2. **Use specific queries** - "Show me candidates for Software Engineer" vs "Show me candidates"
3. **Batch requests** - Get summary and then drill down
4. **Cache responses** - Store frequently requested data

## Troubleshooting

### Gemini Not Configured

```bash
# Configure Gemini first
curl -X POST "/chat/configure-gemini" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"api_key": "your_key"}'
```

### No Data Available

- Ensure company has job postings
- Check if applications exist
- Verify database connection

### Slow Responses

- Check Gemini API status
- Monitor memory usage
- Verify ChromaDB initialization

## Integration Examples

### Frontend Integration (JavaScript)

```javascript
class HRAssistant {
  constructor(apiUrl, token) {
    this.apiUrl = apiUrl;
    this.token = token;
  }

  async configureGemini(apiKey) {
    const response = await fetch(`${this.apiUrl}/chat/configure-gemini`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ api_key: apiKey }),
    });
    return response.json();
  }

  async sendMessage(message) {
    const response = await fetch(`${this.apiUrl}/chat/message`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });
    return response.json();
  }

  async getSummary() {
    const response = await fetch(`${this.apiUrl}/chat/summary`, {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    });
    return response.json();
  }
}

// Usage
const assistant = new HRAssistant("https://your-api-url", "your-token");
await assistant.configureGemini("your-gemini-key");
const response = await assistant.sendMessage("Show me hiring summary");
```

### Python Integration

```python
import requests

class HRAssistant:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def configure_gemini(self, api_key):
        response = requests.post(
            f'{self.api_url}/chat/configure-gemini',
            headers=self.headers,
            json={'api_key': api_key}
        )
        return response.json()

    def send_message(self, message):
        response = requests.post(
            f'{self.api_url}/chat/message',
            headers=self.headers,
            json={'message': message}
        )
        return response.json()

    def get_summary(self):
        response = requests.get(
            f'{self.api_url}/chat/summary',
            headers=self.headers
        )
        return response.json()

# Usage
assistant = HRAssistant('https://your-api-url', 'your-token')
assistant.configure_gemini('your-gemini-key')
response = assistant.send_message('Show me hiring summary')
```

## Support

For issues or questions:

1. Check the health endpoint: `GET /health`
2. Review logs in Google Cloud Console
3. Test with simple queries first
4. Verify all environment variables are set
