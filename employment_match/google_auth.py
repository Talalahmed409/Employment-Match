#!/usr/bin/env python3
"""
Google OAuth authentication utilities for Employment Match system
"""

import os
import json
from typing import Optional, Dict, Any, Union
from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth.exceptions import GoogleAuthError as GoogleAuthErrorOriginal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from employment_match.database import Company, Candidate
from employment_match.auth import create_access_token, get_password_hash

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com")

class GoogleAuthError(Exception):
    """Custom exception for Google authentication errors"""
    pass

def verify_google_token(token: str) -> Dict[str, Any]:
    """
    Verify Google ID token and return user information
    
    Args:
        token: Google ID token from frontend
        
    Returns:
        Dict containing user information from Google
        
    Raises:
        GoogleAuthError: If token verification fails
    """
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Check if the token is still valid
        if idinfo['aud'] != GOOGLE_CLIENT_ID:
            raise GoogleAuthError("Wrong audience.")
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise GoogleAuthError("Wrong issuer.")
        
        return idinfo
        
    except GoogleAuthErrorOriginal as e:
        raise GoogleAuthError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise GoogleAuthError(f"Token verification failed: {str(e)}")

def get_or_create_google_user(db: Session, google_user_info: Dict[str, Any], user_type: str) -> tuple[Union[Company, Candidate], bool]:
    """
    Get existing user or create new user from Google OAuth data
    
    Args:
        db: Database session
        google_user_info: User information from Google
        user_type: Either 'company' or 'candidate'
        
    Returns:
        Tuple of (Company or Candidate object, is_new_user boolean)
    """
    email = google_user_info.get('email')
    if not email:
        raise GoogleAuthError("Email not provided by Google")
    
    # Check if user already exists
    if user_type == "company":
        user = db.query(Company).filter(Company.email == email).first()
        if user:
            return user, False
        
        # Create new company user
        company = Company(
            name=google_user_info.get('name', 'Unknown Company'),
            email=email,
            password_hash=get_password_hash("google_oauth_user"),  # Placeholder password
            google_id=google_user_info.get('sub'),  # Google user ID
            is_google_user=True,
            profile_complete=False  # New Google OAuth users need to complete profile
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return company, True
        
    elif user_type == "candidate":
        user = db.query(Candidate).filter(Candidate.email == email).first()
        if user:
            return user, False
        
        # Parse name from Google data
        name_parts = google_user_info.get('name', 'Unknown User').split(' ', 1)
        first_name = name_parts[0] if name_parts else 'Unknown'
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create new candidate user
        candidate = Candidate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=get_password_hash("google_oauth_user"),  # Placeholder password
            google_id=google_user_info.get('sub'),  # Google user ID
            is_google_user=True,
            profile_complete=False  # New Google OAuth users need to complete profile
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return candidate, True
    
    else:
        raise ValueError("Invalid user_type. Must be 'company' or 'candidate'")

def authenticate_google_user(db: Session, token: str, user_type: str) -> tuple[Union[Company, Candidate], bool]:
    """
    Authenticate user with Google OAuth token
    
    Args:
        db: Database session
        token: Google ID token
        user_type: Either 'company' or 'candidate'
        
    Returns:
        Tuple of (Company or Candidate object, is_new_user boolean)
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Verify Google token
        google_user_info = verify_google_token(token)
        
        # Get or create user
        user, is_new_user = get_or_create_google_user(db, google_user_info, user_type)
        
        return user, is_new_user
        
    except GoogleAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        ) 