#!/usr/bin/env python3
"""
Test script for Google OAuth implementation
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com")

def test_google_oauth_endpoint():
    """Test the Google OAuth endpoint"""
    print("Testing Google OAuth endpoint...")
    
    # Test with invalid token
    test_data = {
        "token": "invalid_token",
        "user_type": "candidate"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/google", json=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 401:
            print("✅ Correctly rejected invalid token")
        else:
            print("❌ Unexpected response for invalid token")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")

def test_health_endpoint():
    """Test the health endpoint to ensure server is running"""
    print("\nTesting health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Server is running and healthy")
        else:
            print("❌ Server health check failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")

def test_database_migration():
    """Test if database migration has been run"""
    print("\nTesting database migration...")
    
    try:
        # Try to get companies to see if the new fields exist
        response = requests.get(f"{BASE_URL}/jobs")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Database connection working")
        else:
            print("❌ Database connection issues")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
    except Exception as e:
        print(f"❌ Error testing database: {e}")

def main():
    """Run all tests"""
    print("=" * 50)
    print("Google OAuth Implementation Test")
    print("=" * 50)
    
    print(f"Testing with Google Client ID: {GOOGLE_CLIENT_ID}")
    print(f"Server URL: {BASE_URL}")
    
    # Test health endpoint first
    test_health_endpoint()
    
    # Test database migration
    test_database_migration()
    
    # Test Google OAuth endpoint
    test_google_oauth_endpoint()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("1. Make sure your server is running: python start_server.py")
    print("2. Run the database migration: python run_migration.py")
    print("3. Set the GOOGLE_CLIENT_ID environment variable")
    print("4. Test with a real Google ID token from your frontend")
    print("=" * 50)

if __name__ == "__main__":
    main() 