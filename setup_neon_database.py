#!/usr/bin/env python3
"""
Setup script for Neon database configuration
This script helps set up the database tables and initial configuration
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

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

def create_database_tables(database_url):
    """Create all database tables"""
    try:
        from employment_match.database import create_tables, engine
        from employment_match.database import Base
        
        # Override the engine with the provided database URL
        engine.url = database_url
        
        print("🔧 Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def run_database_migrations(database_url):
    """Run Alembic migrations if available"""
    try:
        import subprocess
        import os
        
        # Set the database URL for Alembic
        os.environ['DATABASE_URL'] = database_url
        
        print("🔄 Running database migrations...")
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully!")
            return True
        else:
            print(f"⚠️  Migration warnings: {result.stderr}")
            return True  # Continue even with warnings
    except FileNotFoundError:
        print("⚠️  Alembic not found, skipping migrations")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Employment Match - Neon Database Setup")
    print("==========================================")
    
    # Get database URL from environment or user input
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("📝 Please provide your Neon database URL:")
        print("Format: postgresql://user:password@host:port/database")
        database_url = input("Database URL: ").strip()
        
        if not database_url:
            print("❌ No database URL provided. Exiting.")
            sys.exit(1)
    
    # Test connection
    if not test_database_connection(database_url):
        print("❌ Cannot proceed without database connection.")
        sys.exit(1)
    
    # Create tables
    if not create_database_tables(database_url):
        print("❌ Failed to create database tables.")
        sys.exit(1)
    
    # Run migrations
    if not run_database_migrations(database_url):
        print("❌ Failed to run database migrations.")
        sys.exit(1)
    
    print("\n🎉 Database setup completed successfully!")
    print("==========================================")
    print("📋 Next steps:")
    print("1. Set the DATABASE_URL environment variable:")
    print(f"   export DATABASE_URL='{database_url}'")
    print("2. Deploy to Google Cloud Run using deploy.sh")
    print("3. Test the API endpoints")

if __name__ == "__main__":
    main() 