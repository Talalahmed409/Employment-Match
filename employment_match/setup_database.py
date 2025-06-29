#!/usr/bin/env python3
"""
Database setup script for Employment Match system
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from employment_match.database import create_tables, engine, Base
from sqlalchemy import text

def setup_database():
    """Setup the database and create all tables"""
    print("Setting up Employment Match database...")
    
    # Test database connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nPlease ensure PostgreSQL is running and the DATABASE_URL environment variable is set correctly.")
        print("Example DATABASE_URL: postgresql://username:password@localhost/employment_match")
        return False
    
    # Create all tables
    try:
        create_tables()
        print("✓ Database tables created successfully")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('companies', 'candidates', 'job_postings', 'applications', 'skill_matches')
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            if len(tables) == 5:
                print("✓ All required tables verified:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print(f"⚠ Warning: Expected 5 tables, found {len(tables)}")
                
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False
    
    print("\nDatabase setup completed successfully!")
    return True

def create_sample_data():
    """Create sample data for testing"""
    print("\nCreating sample data...")
    
    try:
        from employment_match.database import SessionLocal, Company, Candidate, JobPosting
        from employment_match.auth import get_password_hash
        
        db = SessionLocal()
        
        # Create sample company
        company = Company(
            name="TechCorp Inc.",
            email="hr@techcorp.com",
            password_hash=get_password_hash("password123"),
            description="Leading technology company",
            website="https://techcorp.com",
            location="San Francisco, CA",
            industry="Technology"
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        print(f"✓ Created sample company: {company.name}")
        
        # Create sample candidate
        candidate = Candidate(
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com",
            password_hash=get_password_hash("password123"),
            phone="+1-555-0123",
            location="New York, NY",
            current_title="Software Engineer",
            years_experience=3
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        print(f"✓ Created sample candidate: {candidate.first_name} {candidate.last_name}")
        
        # Create sample job posting
        job_posting = JobPosting(
            company_id=company.id,
            title="Senior Python Developer",
            description="We are looking for an experienced Python developer to join our team...",
            requirements="Python, FastAPI, PostgreSQL, 3+ years experience",
            location="San Francisco, CA",
            salary_min=80000,
            salary_max=120000,
            employment_type="full-time",
            experience_level="senior"
        )
        db.add(job_posting)
        db.commit()
        print(f"✓ Created sample job posting: {job_posting.title}")
        
        db.close()
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"✗ Error creating sample data: {e}")

if __name__ == "__main__":
    print("Employment Match Database Setup")
    print("=" * 40)
    
    # Check environment variables
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("⚠ DATABASE_URL environment variable not set")
        print("Using default: postgresql://user:password@localhost/employment_match")
        print("Set DATABASE_URL to override this default")
    
    # Setup database
    if setup_database():
        # Ask if user wants sample data
        response = input("\nWould you like to create sample data? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            create_sample_data()
        
        print("\nSetup complete! You can now run the API server.")
        print("Run: python API.py")
    else:
        print("\nSetup failed. Please check the error messages above.")
        sys.exit(1) 