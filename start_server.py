#!/usr/bin/env python3
"""
Startup script for the Employment Match FastAPI server
Production-ready configuration for Google Cloud Run
"""

import uvicorn
import os
import sys
from dotenv import load_dotenv

def main():
    """Start the FastAPI server"""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    workers = int(os.getenv("WORKERS", "1"))
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("Warning: .env file not found. Using environment variables.")
    
    # Check if data files exist
    if not os.path.exists('data/esco_skills.json'):
        print("Warning: ESCO skills data not found. Run the setup first:")
        print("python employment_match/convert_esco_to_json.py")
        print("python employment_match/generate_embeddings.py")
    
    # Check required environment variables
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Warning: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before starting the server.")
    
    print("Starting Employment Match API server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Reload: {reload}")
    print(f"Log Level: {log_level}")
    print(f"Workers: {workers}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Health Check: http://{host}:{port}/health")
    print("\nPress Ctrl+C to stop the server")
    
    # Start the server
    uvicorn.run(
        "employment_match.API:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        workers=workers if workers > 1 else None,
        access_log=True
    )

if __name__ == "__main__":
    main() 