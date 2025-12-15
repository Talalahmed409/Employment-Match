#!/usr/bin/env python3
"""
Migration script to add profile_complete field to Company and Candidate tables
"""

from sqlalchemy import create_engine, text
import os

# Database configuration - must be supplied via environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

def add_profile_complete_field():
    """Add profile_complete field to existing tables"""
    print(f"🔧 Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Unknown'}")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("🔧 Adding profile_complete field to companies table...")
            
            # Add profile_complete field to companies table
            conn.execute(text("""
                ALTER TABLE companies 
                ADD COLUMN IF NOT EXISTS profile_complete BOOLEAN DEFAULT TRUE;
            """))
            
            # Update existing Google OAuth users to have incomplete profiles
            conn.execute(text("""
                UPDATE companies 
                SET profile_complete = FALSE 
                WHERE is_google_user = TRUE AND profile_complete = TRUE;
            """))
            
            print("✅ Companies table updated successfully!")
            
            print("🔧 Adding profile_complete field to candidates table...")
            
            # Add profile_complete field to candidates table
            conn.execute(text("""
                ALTER TABLE candidates 
                ADD COLUMN IF NOT EXISTS profile_complete BOOLEAN DEFAULT TRUE;
            """))
            
            # Update existing Google OAuth users to have incomplete profiles
            conn.execute(text("""
                UPDATE candidates 
                SET profile_complete = FALSE 
                WHERE is_google_user = TRUE AND profile_complete = TRUE;
            """))
            
            print("✅ Candidates table updated successfully!")
            
            conn.commit()
            print("\n🎉 Successfully added profile_complete field to both tables!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    add_profile_complete_field() 