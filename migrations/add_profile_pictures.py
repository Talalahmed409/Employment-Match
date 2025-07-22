#!/usr/bin/env python3
"""
Migration script to add profile_picture_path and background_picture_path fields to Company and Candidate tables
"""

from sqlalchemy import create_engine, text
import os

# Database configuration - use Neon database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_ZoB1Unqpc3rJ@ep-red-salad-a20vuj1d.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def add_profile_pictures():
    """Add profile_picture_path and background_picture_path fields to existing tables"""
    print(f"🔧 Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Unknown'}")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("🔧 Adding profile picture fields to companies table...")
            
            # Add profile_picture_path field to companies table
            conn.execute(text("""
                ALTER TABLE companies 
                ADD COLUMN IF NOT EXISTS profile_picture_path VARCHAR(500);
            """))
            
            # Add background_picture_path field to companies table
            conn.execute(text("""
                ALTER TABLE companies 
                ADD COLUMN IF NOT EXISTS background_picture_path VARCHAR(500);
            """))
            
            print("✅ Companies table updated successfully!")
            
            print("🔧 Adding profile picture fields to candidates table...")
            
            # Add profile_picture_path field to candidates table
            conn.execute(text("""
                ALTER TABLE candidates 
                ADD COLUMN IF NOT EXISTS profile_picture_path VARCHAR(500);
            """))
            
            # Add background_picture_path field to candidates table
            conn.execute(text("""
                ALTER TABLE candidates 
                ADD COLUMN IF NOT EXISTS background_picture_path VARCHAR(500);
            """))
            
            print("✅ Candidates table updated successfully!")
            
            conn.commit()
            print("\n🎉 Successfully added profile picture fields to both tables!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    add_profile_pictures() 