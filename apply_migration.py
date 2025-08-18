#!/usr/bin/env python3
"""
Apply migration to add location and website fields to users table.
This script can be run locally or on Railway.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse

def apply_migration():
    # Get database URL from environment or command line
    database_url = os.getenv('DATABASE_URL')
    if not database_url and len(sys.argv) > 1:
        database_url = sys.argv[1]
    
    if not database_url:
        print("Error: DATABASE_URL not found in environment or as argument")
        print("Usage: python apply_migration.py [DATABASE_URL]")
        sys.exit(1)
    
    # Parse database URL
    parsed = urlparse(database_url)
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Check current schema
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Current columns in users table: {existing_columns}")
        
        # Apply migration if needed
        if 'location' not in existing_columns or 'website' not in existing_columns:
            print("Adding missing columns...")
            
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS location VARCHAR,
                ADD COLUMN IF NOT EXISTS website VARCHAR
            """)
            
            print("Migration applied successfully!")
            
            # Verify changes
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('location', 'website')
            """)
            new_columns = [row[0] for row in cursor.fetchall()]
            print(f"Added columns: {new_columns}")
        else:
            print("Columns already exist, no migration needed")
        
        cursor.close()
        conn.close()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error applying migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()