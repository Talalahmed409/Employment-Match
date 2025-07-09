#!/usr/bin/env python3
"""
Dedicated script to migrate Google OAuth fields to Neon database
"""

import os
import sys

# Add the employment_match directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'employment_match'))

from migrations.add_google_oauth_fields_neon import add_google_oauth_fields_neon

if __name__ == "__main__":
    print("🌐 Google OAuth Migration for Neon Database")
    print("============================================")
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not set.")
        print("Please set your Neon database URL:")
        print("export DATABASE_URL='your-neon-database-url'")
        sys.exit(1)
    
    if 'neon' not in database_url.lower():
        print("⚠️  Warning: DATABASE_URL doesn't appear to be a Neon URL")
        print(f"Current URL: {database_url}")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("Migration cancelled.")
            sys.exit(0)
    
    try:
        add_google_oauth_fields_neon()
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Deploy your updated code to production")
        print("2. Test the Google OAuth endpoint: POST /auth/google")
        print("3. Verify with your frontend integration")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1) 