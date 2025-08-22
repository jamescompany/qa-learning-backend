#!/bin/bash

# Development environment migration script
echo "==================================="
echo "Running migrations for DEVELOPMENT"
echo "==================================="

# Set environment
export ENVIRONMENT=development

# Run migration
python migrate.py development "$@"

# If no arguments provided, show help
if [ $# -eq 0 ]; then
    echo ""
    echo "Common commands:"
    echo "  ./migrate-dev.sh upgrade head        # Apply all migrations"
    echo "  ./migrate-dev.sh current              # Show current revision"
    echo "  ./migrate-dev.sh history              # Show migration history"
    echo "  ./migrate-dev.sh revision --autogenerate -m 'description'  # Create new migration"
    echo "  ./migrate-dev.sh downgrade -1         # Rollback one migration"
fi