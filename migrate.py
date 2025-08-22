#!/usr/bin/env python3
"""
Alembic migration runner for different environments
Usage: 
    python migrate.py development upgrade head
    python migrate.py production upgrade head
    python migrate.py development revision --autogenerate -m "message"
"""

import sys
import os
import subprocess
from pathlib import Path

def run_migration(environment, *alembic_args):
    """Run alembic migration for specified environment"""
    
    # Validate environment
    if environment not in ['development', 'production']:
        print(f"Error: Invalid environment '{environment}'. Use 'development' or 'production'")
        sys.exit(1)
    
    # Set environment variable
    os.environ['ENVIRONMENT'] = environment
    
    # Select appropriate config file
    config_file = f"alembic.{environment}.ini"
    
    if not Path(config_file).exists():
        print(f"Error: Config file '{config_file}' not found")
        sys.exit(1)
    
    # Build alembic command
    cmd = ['alembic', '-c', config_file] + list(alembic_args)
    
    print(f"Running migration for {environment} environment...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Execute alembic command
        result = subprocess.run(cmd, check=True)
        print(f"Migration completed successfully for {environment} environment")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Migration failed for {environment} environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python migrate.py <environment> <alembic_command> [options]")
        print("Example: python migrate.py development upgrade head")
        print("Example: python migrate.py production revision --autogenerate -m 'Add new table'")
        sys.exit(1)
    
    environment = sys.argv[1]
    alembic_args = sys.argv[2:]
    
    run_migration(environment, *alembic_args)