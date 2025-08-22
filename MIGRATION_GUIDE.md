# Alembic Migration Guide

This guide explains how to manage database migrations for both development and production environments.

## Environment Setup

We have separate Alembic configurations for each environment:
- `alembic.development.ini` - Development database configuration
- `alembic.production.ini` - Production database configuration

## Migration Scripts

### Python Script (Recommended)
Use `migrate.py` for cross-platform compatibility:

```bash
# Development
python migrate.py development <command>

# Production
python migrate.py production <command>
```

### Shell Scripts (Unix/Linux/Mac)
Convenience scripts for Unix-based systems:

```bash
# Development
./migrate-dev.sh <command>

# Production (includes safety confirmation)
./migrate-prod.sh <command>
```

## Common Commands

### 1. Check Current Migration Status
```bash
# Development
python migrate.py development current

# Production
python migrate.py production current
```

### 2. Apply All Migrations
```bash
# Development
python migrate.py development upgrade head

# Production
python migrate.py production upgrade head
```

### 3. Create a New Migration
```bash
# Always create migrations in development first
python migrate.py development revision --autogenerate -m "Add new feature"
```

### 4. View Migration History
```bash
# Development
python migrate.py development history

# Production
python migrate.py production history
```

### 5. Rollback Migration
```bash
# Development (rollback one migration)
python migrate.py development downgrade -1

# Production (USE WITH EXTREME CAUTION)
python migrate.py production downgrade -1
```

## Workflow

### Development Workflow
1. Make model changes in your code
2. Create a new migration:
   ```bash
   python migrate.py development revision --autogenerate -m "Description of changes"
   ```
3. Review the generated migration file in `alembic/versions/`
4. Apply the migration:
   ```bash
   python migrate.py development upgrade head
   ```
5. Test your changes thoroughly

### Production Deployment
1. Ensure all migrations are tested in development
2. Commit migration files to version control
3. Deploy code to production server
4. Run production migration:
   ```bash
   python migrate.py production upgrade head
   ```
5. Verify the migration was successful:
   ```bash
   python migrate.py production current
   ```

## Environment Variables

The migration scripts automatically load the correct environment file:
- Development: `.env.development`
- Production: `.env.production`

You can override the database URL by setting the `DATABASE_URL` environment variable:
```bash
DATABASE_URL=postgresql://user:pass@host:port/db python migrate.py development upgrade head
```

## Safety Measures

### Production Safety
- The `migrate-prod.sh` script includes a confirmation prompt
- Always backup your production database before running migrations
- Test all migrations in development first
- Review migration files before applying to production

### Rollback Strategy
If a migration fails in production:
1. Note the current revision: `python migrate.py production current`
2. Rollback to previous revision: `python migrate.py production downgrade -1`
3. Fix the issue in development
4. Create a new migration with the fix
5. Test thoroughly before re-deploying

## Troubleshooting

### Connection Issues
- Verify database credentials in `.env.development` or `.env.production`
- Check network connectivity to database server
- Ensure database server is running

### Migration Conflicts
- If migrations are out of sync, check with: `python migrate.py <env> history`
- Resolve conflicts by carefully reviewing migration files
- Consider using `stamp` command to mark current state if needed

### Import Errors
- Ensure all model files are properly imported in `alembic/env.py`
- Check that python path includes the backend directory
- Verify all dependencies are installed: `pip install -r requirements.txt`

## Best Practices

1. **Always create migrations in development first**
2. **Never edit migration files after they've been applied to production**
3. **Keep migrations small and focused**
4. **Include both upgrade and downgrade operations**
5. **Test rollback procedures in development**
6. **Document complex migrations with comments**
7. **Backup production database before migrations**
8. **Monitor migration execution time for large databases**

## Support

For issues or questions about migrations:
1. Check migration history: `python migrate.py <env> history`
2. Review log output for error details
3. Consult Alembic documentation: https://alembic.sqlalchemy.org/