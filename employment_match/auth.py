#!/usr/bin/env python3
"""
Authentication utilities for Employment Match system
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from employment_match.database import get_db, Company, Candidate

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Union[Company, Candidate]:
    """Get current authenticated user from token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_type = payload.get("user_type")
    user_id = payload.get("sub")
    
    if user_type == "company":
        user = db.query(Company).filter(Company.id == user_id).first()
    elif user_type == "candidate":
        user = db.query(Candidate).filter(Candidate.id == user_id).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_company(
    current_user: Union[Company, Candidate] = Depends(get_current_user)
) -> Company:
    """Get current authenticated company user"""
    if not isinstance(current_user, Company):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Company account required."
        )
    return current_user

async def get_current_candidate(
    current_user: Union[Company, Candidate] = Depends(get_current_user)
) -> Candidate:
    """Get current authenticated candidate user"""
    if not isinstance(current_user, Candidate):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Candidate account required."
        )
    return current_user

def authenticate_company(db: Session, email: str, password: str) -> Optional[Company]:
    """Authenticate a company user"""
    company = db.query(Company).filter(Company.email == email).first()
    if not company:
        return None
    if not verify_password(password, company.password_hash):
        return None
    return company

def authenticate_candidate(db: Session, email: str, password: str) -> Optional[Candidate]:
    """Authenticate a candidate user"""
    candidate = db.query(Candidate).filter(Candidate.email == email).first()
    if not candidate:
        return None
    if not verify_password(password, candidate.password_hash):
        return None
    return candidate 