#!/bin/bash

echo "Setting up Google OAuth for Employment Match Backend"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database configuration
DATABASE_URL=postgresql://employment_user:password123@localhost:5432/employment_match

# Security
SECRET_KEY=your-secret-key-change-in-production

# Google OAuth
GOOGLE_CLIENT_ID=248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com

# Gemini API (optional)
GEMINI_API_KEY=your-gemini-api-key-here
EOF
    echo "✅ Created .env file with default configuration"
else
    echo "✅ .env file already exists"
fi

# Run database migration
echo "🗄️  Running database migration..."
python run_migration.py

if [ $? -eq 0 ]; then
    echo "✅ Database migration completed successfully"
else
    echo "❌ Database migration failed. Please check your database connection."
    exit 1
fi

# Test the implementation
echo "🧪 Testing Google OAuth implementation..."
python test_google_oauth.py

echo ""
echo "🎉 Google OAuth setup completed!"
echo ""
echo "Next steps:"
echo "1. Start your server: python start_server.py"
echo "2. Test with your frontend Google Sign-In implementation"
echo "3. Check the documentation: docs/GOOGLE_OAUTH_SETUP.md"
echo ""
echo "API Endpoint: POST /auth/google"
echo "Request Body: {\"token\": \"google_id_token\", \"user_type\": \"company\" or \"candidate\"}" 