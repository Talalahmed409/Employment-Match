#!/usr/bin/env python3
"""
Script to run the database migration for Google OAuth fields
"""

import sys
import os

# Add the employment_match directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'employment_match'))

def run_local_migration():
    """Run migration for local database"""
    from migrations.add_google_oauth_fields import add_google_oauth_fields
    add_google_oauth_fields()

def run_neon_migration():
    """Run migration for Neon database"""
    from migrations.add_google_oauth_fields_neon import add_google_oauth_fields_neon
    add_google_oauth_fields_neon()

if __name__ == "__main__":
    print("🚀 Google OAuth Database Migration")
    print("==================================")
    
    # Check if DATABASE_URL is set (indicates Neon)
    database_url = os.getenv('DATABASE_URL')
    
    if database_url and 'neon' in database_url.lower():
        print("🌐 Detected Neon database URL")
        print("Running Neon-specific migration...")
        try:
            run_neon_migration()
            print("✅ Neon migration completed successfully!")
        except Exception as e:
            print(f"❌ Neon migration failed: {e}")
            sys.exit(1)
    else:
        print("🏠 Running local database migration...")
        try:
            run_local_migration()
            print("✅ Local migration completed successfully!")
        except Exception as e:
            print(f"❌ Local migration failed: {e}")
            sys.exit(1) 