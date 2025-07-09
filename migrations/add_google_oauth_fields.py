#!/usr/bin/env python3
"""
Migration script to add Google OAuth fields to Company and Candidate tables
"""

from sqlalchemy import create_engine, text
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://employment_user:password123@localhost:5432/employment_match")

def add_google_oauth_fields():
    """Add Google OAuth fields to existing tables"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Add Google OAuth fields to companies table
        conn.execute(text("""
            ALTER TABLE companies 
            ADD COLUMN IF NOT EXISTS google_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS is_google_user BOOLEAN DEFAULT FALSE;
        """))
        
        # Add unique index on google_id for companies
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_google_id 
            ON companies(google_id) 
            WHERE google_id IS NOT NULL;
        """))
        
        # Add index on is_google_user for companies
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_companies_is_google_user 
            ON companies(is_google_user);
        """))
        
        # Add Google OAuth fields to candidates table
        conn.execute(text("""
            ALTER TABLE candidates 
            ADD COLUMN IF NOT EXISTS google_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS is_google_user BOOLEAN DEFAULT FALSE;
        """))
        
        # Add unique index on google_id for candidates
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_candidates_google_id 
            ON candidates(google_id) 
            WHERE google_id IS NOT NULL;
        """))
        
        # Add index on is_google_user for candidates
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_candidates_is_google_user 
            ON candidates(is_google_user);
        """))
        
        conn.commit()
        print("Successfully added Google OAuth fields to database tables")

if __name__ == "__main__":
    add_google_oauth_fields() 