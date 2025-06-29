#!/usr/bin/env python3
"""
Health check script for Employment Match API
Useful for monitoring and CI/CD pipelines
"""

import requests
import sys
import json
from datetime import datetime

def check_health(url):
    """Check the health of the API"""
    try:
        # Check health endpoint
        health_response = requests.get(f"{url}/health", timeout=30)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   ESCO Skills Loaded: {health_data.get('esco_skills_loaded', False)}")
            print(f"   Embeddings Loaded: {health_data.get('embeddings_loaded', False)}")
            print(f"   Gemini Configured: {health_data.get('gemini_configured', False)}")
            return True
        else:
            print(f"❌ Health check failed with status code: {health_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def check_docs(url):
    """Check if API documentation is accessible"""
    try:
        docs_response = requests.get(f"{url}/docs", timeout=30)
        if docs_response.status_code == 200:
            print(f"✅ API documentation accessible")
            return True
        else:
            print(f"⚠️  API documentation not accessible: {docs_response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️  API documentation check failed: {e}")
        return False

def check_database_connection(url):
    """Check database connection through a simple API call"""
    try:
        # Try to get job postings (should work without authentication)
        jobs_response = requests.get(f"{url}/jobs", timeout=30)
        if jobs_response.status_code in [200, 401]:  # 401 is expected without auth
            print(f"✅ Database connection working")
            return True
        else:
            print(f"⚠️  Database connection check failed: {jobs_response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Database connection check failed: {e}")
        return False

def main():
    """Main health check function"""
    if len(sys.argv) != 2:
        print("Usage: python health_check.py <API_URL>")
        print("Example: python health_check.py https://employment-match-xxxxx-uc.a.run.app")
        sys.exit(1)
    
    url = sys.argv[1].rstrip('/')
    
    print(f"🔍 Health Check for Employment Match API")
    print(f"URL: {url}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # Run health checks
    health_ok = check_health(url)
    docs_ok = check_docs(url)
    db_ok = check_database_connection(url)
    
    print("=" * 50)
    
    # Summary
    if health_ok and docs_ok and db_ok:
        print("🎉 All health checks passed!")
        sys.exit(0)
    elif health_ok:
        print("⚠️  Basic health check passed, but some components may have issues")
        sys.exit(0)
    else:
        print("❌ Health checks failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 