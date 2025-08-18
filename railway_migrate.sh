#!/bin/bash

# Railway deployment migration script
# This script applies database migrations when deploying to Railway

echo "Starting database migration..."

# Check if location and website columns exist
python -c "
import os
import psycopg2
from urllib.parse import urlparse

database_url = os.getenv('DATABASE_URL')
if database_url:
    parsed = urlparse(database_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute(\"\"\"
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name IN ('location', 'website')
    \"\"\")
    
    existing = [row[0] for row in cursor.fetchall()]
    
    if len(existing) < 2:
        print('Applying migration to add location and website columns...')
        cursor.execute(\"\"\"
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS location VARCHAR,
            ADD COLUMN IF NOT EXISTS website VARCHAR
        \"\"\")
        conn.commit()
        print('Migration applied successfully!')
    else:
        print('Columns already exist, skipping migration.')
    
    cursor.close()
    conn.close()
"

echo "Migration check complete."