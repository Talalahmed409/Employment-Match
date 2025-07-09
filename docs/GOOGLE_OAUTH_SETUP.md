# Google OAuth Setup Guide

This guide explains how to set up and use Google OAuth authentication in the Employment Match backend.

## Overview

The backend now supports Google OAuth authentication for both companies and candidates. Users can sign in or sign up using their Google accounts, and the system will automatically create or link their accounts.

## Setup Instructions

### 1. Install Dependencies

The required Google OAuth dependencies have been added to `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Add the Google Client ID to your environment variables:

```bash
export GOOGLE_CLIENT_ID="248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com"
```

Or add it to your `.env` file:

```
GOOGLE_CLIENT_ID=248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com
```

### 3. Database Migration

#### For Local Database:

```bash
python run_migration.py
```

#### For Neon Database:

```bash
# Set your Neon database URL
export DATABASE_URL="your-neon-database-url"

# Run the Neon-specific migration
python migrate_neon_google_oauth.py
```

Or use the automatic detection:

```bash
export DATABASE_URL="your-neon-database-url"
python run_migration.py
```

This will add the following fields to both `companies` and `candidates` tables:

- `google_id`: Stores the Google user ID
- `is_google_user`: Boolean flag indicating if the user signed up via Google

### 4. Restart the Server

Restart your FastAPI server to load the new Google OAuth functionality:

```bash
python start_server.py
```

## API Endpoints

### Google OAuth Authentication

**POST** `/auth/google`

Authenticate a user with Google OAuth token.

**Request Body:**

```json
{
  "token": "google_id_token_from_frontend",
  "user_type": "company" // or "candidate"
}
```

**Response:**

```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user_type": "company",
  "user_id": 123
}
```

## Frontend Integration

### 1. Google Sign-In Button

Your frontend should implement Google Sign-In using the Google Identity Services library. Here's a basic example:

```javascript
// Initialize Google Sign-In
google.accounts.id.initialize({
  client_id:
    "248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com",
  callback: handleCredentialResponse,
});

// Handle the credential response
function handleCredentialResponse(response) {
  const token = response.credential;

  // Send token to backend
  fetch("/auth/google", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      token: token,
      user_type: "candidate", // or 'company'
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      // Store the JWT token
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_type", data.user_type);
      localStorage.setItem("user_id", data.user_id);

      // Redirect or update UI
      console.log("Successfully authenticated with Google");
    })
    .catch((error) => {
      console.error("Google authentication failed:", error);
    });
}
```

### 2. User Type Selection

You'll need to implement a way for users to select whether they're signing up as a company or candidate before initiating Google OAuth. This could be:

- A toggle/radio button before the Google Sign-In
- Separate buttons for "Sign in with Google as Company" and "Sign in with Google as Candidate"
- A modal or form that asks for user type

## How It Works

### 1. Token Verification

When a user signs in with Google, the frontend receives an ID token. This token is sent to the backend endpoint `/auth/google`.

The backend verifies the token using Google's public keys and extracts user information including:

- Email address
- Full name
- Google user ID
- Profile picture (if available)

### 2. User Creation/Linking

The system checks if a user with the provided email already exists:

- **If user exists**: The existing account is linked to the Google ID (if not already linked)
- **If user doesn't exist**: A new account is created with the information from Google

### 3. JWT Token Generation

After successful authentication, the backend generates a JWT token that can be used for subsequent API calls, just like the regular email/password authentication.

## Security Considerations

1. **Token Verification**: The backend verifies Google ID tokens server-side using Google's public keys
2. **Email Uniqueness**: Each email can only be associated with one account
3. **Google ID Linking**: Google user IDs are stored to prevent duplicate accounts
4. **JWT Tokens**: Standard JWT tokens are used for session management

## Error Handling

The API returns appropriate HTTP status codes:

- `400 Bad Request`: Invalid user_type or malformed request
- `401 Unauthorized`: Invalid or expired Google token
- `500 Internal Server Error`: Server-side errors

## Testing

You can test the Google OAuth integration by:

1. Setting up a test Google account
2. Using the Google Sign-In button in your frontend
3. Checking that the user is created/linked in the database
4. Verifying that subsequent API calls work with the JWT token

## Troubleshooting

### Common Issues

1. **"Invalid token" error**: Make sure the Google Client ID matches between frontend and backend
2. **"Wrong audience" error**: Verify the client ID is correct
3. **Database errors**: Ensure the migration has been run successfully
4. **CORS issues**: Make sure your frontend domain is allowed in the Google OAuth console

### Debug Mode

To enable debug logging for Google OAuth, add this to your environment:

```bash
export GOOGLE_OAUTH_DEBUG=true
```

## Neon Database Deployment

### Environment Variables for Production

When deploying to production with Neon, make sure to set these environment variables:

```bash
# Database
DATABASE_URL=your-neon-database-url

# Google OAuth
GOOGLE_CLIENT_ID=248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com

# Security
SECRET_KEY=your-production-secret-key
```

### Deployment Steps

1. **Run the migration on Neon:**

   ```bash
   export DATABASE_URL="your-neon-database-url"
   python migrate_neon_google_oauth.py
   ```

2. **Deploy your updated code** (using your existing deployment process)

3. **Verify the migration:**
   ```bash
   python test_google_oauth.py
   ```

### Troubleshooting Neon Migration

- **Connection issues**: Make sure your Neon database URL is correct and accessible
- **Permission errors**: Ensure your database user has ALTER TABLE permissions
- **Timeout issues**: Neon may have connection limits; retry if needed

## Migration Notes

If you have existing users in your database, the migration will:

1. Add the new Google OAuth fields without affecting existing data
2. Set `is_google_user` to `false` for all existing users
3. Leave `google_id` as `null` for existing users

Existing users can continue to use email/password authentication, and new users can choose either method.
