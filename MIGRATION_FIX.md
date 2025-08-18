# Fix for 500 Error on Signup - Database Schema Migration

## Problem
The production database is missing the `location` and `website` columns in the `users` table, causing a 500 error during user signup.

## Solution
The following scripts have been created to fix this issue:

### Option 1: Automatic Migration (Recommended)
The `database.py` file has been updated to automatically add missing columns when the application starts. Simply redeploy the backend to Railway and the schema will be updated automatically.

### Option 2: Manual Migration Script
Run the migration script directly on Railway:

```bash
# Connect to Railway project
railway run python apply_migration.py
```

Or provide the DATABASE_URL directly:
```bash
python apply_migration.py "postgresql://user:pass@host:port/dbname"
```

### Option 3: Direct SQL
Connect to your Railway PostgreSQL database and run:

```sql
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS location VARCHAR,
ADD COLUMN IF NOT EXISTS website VARCHAR;
```

## Files Created/Modified

1. **database.py** - Updated `init_db()` to automatically add missing columns
2. **apply_migration.py** - Standalone script to apply migration
3. **ensure_schema.py** - Script to ensure schema is up to date
4. **railway_migrate.sh** - Shell script for Railway deployment
5. **fix_user_schema.sql** - Raw SQL migration
6. **alembic/** - Alembic migration configuration for future migrations

## Deployment Steps

1. Commit the changes:
```bash
git add .
git commit -m "Fix database schema: add location and website columns to users table"
```

2. Push to your repository:
```bash
git push origin main
```

3. Railway will automatically redeploy and the schema will be updated during startup.

## Verification

After deployment, you can verify the fix by:
1. Attempting to sign up a new user
2. Checking the logs for "Added location and website columns to users table"
3. Running a test query against the database to confirm columns exist