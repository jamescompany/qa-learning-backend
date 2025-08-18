#!/usr/bin/env python3
"""
Ensure database schema is up to date.
This script should be run before starting the application in production.
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))

from database import init_db, check_database_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Checking database connection...")
    if not check_database_connection():
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    logger.info("Ensuring database schema is up to date...")
    try:
        init_db()
        logger.info("Database schema updated successfully")
    except Exception as e:
        logger.error(f"Failed to update database schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()