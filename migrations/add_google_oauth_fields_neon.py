#!/usr/bin/env python3
"""
Migration script to add Google OAuth fields to Company and Candidate tables for Neon database
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def get_neon_database_url():
    """Get the Neon database URL from environment or user input"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("📝 Please provide your Neon database URL:")
        print("Format: postgresql://user:password@host:port/database")
        database_url = input("Database URL: ").strip()
        
        if not database_url:
            print("❌ No database URL provided. Exiting.")
            sys.exit(1)
    
    return database_url

def test_database_connection(database_url):
    """Test the database connection"""
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            row = result.fetchone()
            if row:
                version = row[0]
                print(f"✅ Database connection successful!")
                print(f"📊 PostgreSQL version: {version}")
                return True
            else:
                print("❌ No version information returned from database")
                return False
    except SQLAlchemyError as e:
        print(f"❌ Database connection failed: {e}")
        return False

def add_google_oauth_fields_neon():
    """Add Google OAuth fields to existing tables in Neon database"""
    database_url = get_neon_database_url()
    
    if not test_database_connection(database_url):
        print("❌ Cannot proceed without database connection.")
        sys.exit(1)
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            print("🔧 Adding Google OAuth fields to companies table...")
            
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
            
            print("✅ Companies table updated successfully!")
            
            print("🔧 Adding Google OAuth fields to candidates table...")
            
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
            
            print("✅ Candidates table updated successfully!")
            
            # Verify the changes
            print("🔍 Verifying changes...")
            
            # Check companies table
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'companies' 
                AND column_name IN ('google_id', 'is_google_user')
                ORDER BY column_name;
            """))
            
            company_columns = result.fetchall()
            if len(company_columns) == 2:
                print("✅ Companies table has Google OAuth fields:")
                for col in company_columns:
                    print(f"   - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            else:
                print("⚠️  Companies table may not have all expected fields")
            
            # Check candidates table
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'candidates' 
                AND column_name IN ('google_id', 'is_google_user')
                ORDER BY column_name;
            """))
            
            candidate_columns = result.fetchall()
            if len(candidate_columns) == 2:
                print("✅ Candidates table has Google OAuth fields:")
                for col in candidate_columns:
                    print(f"   - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            else:
                print("⚠️  Candidates table may not have all expected fields")
            
            conn.commit()
            print("\n🎉 Successfully added Google OAuth fields to Neon database!")
            
    except SQLAlchemyError as e:
        print(f"❌ Database operation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Google OAuth Migration for Neon Database")
    print("============================================")
    add_google_oauth_fields_neon() 