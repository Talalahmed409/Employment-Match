# Neon Database Migration Guide for Google OAuth

## Quick Migration Steps

### 1. Set Your Neon Database URL

```bash
export DATABASE_URL="your-neon-database-url-here"
```

### 2. Run the Migration

```bash
python migrate_neon_google_oauth.py
```

### 3. Verify the Migration

The script will automatically verify that the fields were added correctly.

## Alternative Methods

### Method 1: Automatic Detection

```bash
export DATABASE_URL="your-neon-database-url"
python run_migration.py
```

### Method 2: Manual Migration

```bash
export DATABASE_URL="your-neon-database-url"
python migrations/add_google_oauth_fields_neon.py
```

## What the Migration Does

1. **Adds new columns** to both `companies` and `candidates` tables:

   - `google_id` (VARCHAR(255), nullable, unique)
   - `is_google_user` (BOOLEAN, default FALSE)

2. **Creates indexes** for performance:

   - Unique index on `google_id` (where not null)
   - Index on `is_google_user`

3. **Verifies the changes** by checking the database schema

## Expected Output

```
🚀 Google OAuth Migration for Neon Database
============================================
✅ Database connection successful!
📊 PostgreSQL version: 15.x
🔧 Adding Google OAuth fields to companies table...
✅ Companies table updated successfully!
🔧 Adding Google OAuth fields to candidates table...
✅ Candidates table updated successfully!
🔍 Verifying changes...
✅ Companies table has Google OAuth fields:
   - google_id: character varying (NULL)
   - is_google_user: boolean (NOT NULL)
✅ Candidates table has Google OAuth fields:
   - google_id: character varying (NULL)
   - is_google_user: boolean (NOT NULL)

🎉 Successfully added Google OAuth fields to Neon database!
```

## Troubleshooting

### Connection Issues

- Verify your Neon database URL is correct
- Check that your IP is allowed in Neon's connection settings
- Ensure the database is active (not paused)

### Permission Issues

- Make sure your database user has ALTER TABLE permissions
- Check that you're connecting with the correct credentials

### Timeout Issues

- Neon may have connection limits; retry the migration if it times out
- The migration is idempotent, so it's safe to run multiple times

## After Migration

1. **Deploy your updated code** to production
2. **Test the Google OAuth endpoint**: `POST /auth/google`
3. **Verify with your frontend** Google Sign-In implementation

## Environment Variables for Production

Make sure these are set in your production environment:

```bash
DATABASE_URL=your-neon-database-url
GOOGLE_CLIENT_ID=248629291681-ep686slgour47ovifcr6pgvasagi1amb.apps.googleusercontent.com
SECRET_KEY=your-production-secret-key
```

## Support

If you encounter any issues:

1. Check the migration logs for specific error messages
2. Verify your Neon database connection
3. Ensure all required environment variables are set
4. Test with a simple database query first
