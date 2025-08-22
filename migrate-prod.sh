#!/bin/bash

# Production environment migration script
echo "=================================="
echo "Running migrations for PRODUCTION"
echo "=================================="
echo "⚠️  WARNING: This will modify the PRODUCTION database!"
echo ""

# Confirmation prompt
read -p "Are you sure you want to continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Migration cancelled."
    exit 1
fi

# Set environment
export ENVIRONMENT=production

# Run migration
python migrate.py production "$@"

# If no arguments provided, show help
if [ $# -eq 0 ]; then
    echo ""
    echo "Common commands:"
    echo "  ./migrate-prod.sh upgrade head       # Apply all migrations"
    echo "  ./migrate-prod.sh current             # Show current revision"
    echo "  ./migrate-prod.sh history             # Show migration history"
    echo "  ./migrate-prod.sh downgrade -1        # Rollback one migration (USE WITH CAUTION)"
fi