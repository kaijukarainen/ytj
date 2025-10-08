# Migration Guide - Adding Database Support

## Overview

This guide helps you migrate your existing YTJ Scraper installation to include PostgreSQL database support.

## What's New

- ✅ PostgreSQL database integration
- ✅ Persistent storage for scraping results
- ✅ REST API endpoints for data queries
- ✅ Session-based result tracking with timestamps
- ✅ Database management UI panel
- ✅ Search and filter capabilities

## Migration Steps

### Step 1: Backup Existing Data

Before updating, backup your current results:

```bash
# Backup JSON files
mkdir -p backup
cp *.json backup/
cp *.csv backup/

# Backup cache
cp finder_cache.json backup/ 2>/dev/null || true
```

### Step 2: Update Project Files

#### Option A: Pull Latest Changes (Git)

```bash
git pull origin main
```

#### Option B: Manual Update

Copy these new files to your project:

**New Files:**
- `python/models/db_models.py`
- `python/services/db_service.py`
- `python/routes/__init__.py`
- `python/routes/db_routes.py`
- `python/init_db.py`
- `frontend/src/components/DatabasePanel.jsx`
- `API.md`
- `DATABASE_SETUP.md`

**Updated Files:**
- `python/app.py` (register database blueprint)
- `python/requirements.txt` (add SQLAlchemy, psycopg2)
- `docker-compose.yaml` (add PostgreSQL service)
- `frontend/src/App.jsx` (import DatabasePanel)

### Step 3: Install Dependencies

#### Python Dependencies

```bash
cd python
pip install sqlalchemy==2.0.23 psycopg2-binary==2.9.9
```

Or:

```bash
pip install -r requirements.txt
```

#### Frontend (No Changes Needed)

The frontend dependencies remain the same.

### Step 4: Setup Database

#### Option A: Docker (Easiest)

```bash
# Start PostgreSQL automatically with other services
docker-compose up -d
```

Database is automatically initialized!

#### Option B: Local PostgreSQL

1. **Install PostgreSQL** (if not already installed):

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Windows - Download from postgresql.org
```

2. **Create Database:**

```bash
psql -U postgres
CREATE DATABASE ytj_scraper;
\q
```

3. **Initialize Tables:**

```bash
cd python
python init_db.py
```

You should see:
```
✓ Database connection successful
✓ Tables created successfully
Created 2 tables:
  - scrape_sessions (9 columns)
  - companies (15 columns)
```

### Step 5: Import Existing Data (Optional)

If you want to import your existing JSON results into the database:

```python
# import_existing.py
import json
from services.db_service import DatabaseService

# Load your existing results
with open('companies_leads.json', 'r', encoding='utf-8') as f:
    companies = json.load(f)

# Create a session for the import
session = DatabaseService.create_session(
    business_line='6201',  # Update with your actual business line
    location='Kuopio',     # Update with your location
    company_form='OY'
)

# Save companies
DatabaseService.save_companies(session.id, companies)
DatabaseService.complete_session(session.id, len(companies))

print(f"✓ Imported {len(companies)} companies to session #{session.id}")
```

Run it:
```bash
python import_existing.py
```

### Step 6: Verify Installation

1. **Start the application:**

```bash
# If using Docker
docker-compose up -d

# If running locally
cd python
python app.py
```

2. **Check database endpoints:**

```bash
# Get sessions
curl http://localhost:5001/api/db/sessions

# Get latest companies
curl http://localhost:5001/api/db/companies/latest
```

3. **Open UI:**

Navigate to `http://localhost:3000` and verify:
- ✅ Database panel is visible
- ✅ "Save to DB" button works
- ✅ Sessions list appears after saving
- ✅ Can load and view saved sessions

## Compatibility

### Backward Compatibility

The update is **fully backward compatible**:

- ✅ Existing scraping still works without database
- ✅ JSON/CSV export still available
- ✅ All original endpoints unchanged
- ✅ Finder.fi cache still works
- ✅ AI enrichment still works

### What Still Works Without Database

If you don't set up PostgreSQL, these features still work:

- Basic scraping
- Finder.fi validation
- AI enrichment
- JSON/CSV export
- File-based cache
- All original functionality

**Note:** Database features will show errors but won't break the app.

## Troubleshooting

### Issue: Database Connection Failed

**Error:**
```
⚠ Warning: Database initialization failed
```

**Solution:**
1. Check PostgreSQL is running: `pg_isready`
2. Verify DATABASE_URL environment variable
3. Check connection string format: `postgresql://user:pass@host:port/database`

### Issue: Tables Not Created

**Error:**
```
sqlalchemy.exc.ProgrammingError: relation "scrape_sessions" does not exist
```

**Solution:**
```bash
cd python
python init_db.py
```

### Issue: Port 5432 Already in Use

**Error:**
```
Error: port is already allocated
```

**Solution:**
1. Stop existing PostgreSQL: `brew services stop postgresql@15`
2. Or change port in docker-compose.yaml
3. Update DATABASE_URL accordingly

### Issue: Frontend Not Showing Database Panel

**Error:** Database panel not visible

**Solution:**
1. Clear browser cache
2. Rebuild frontend:
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

## Rollback

If you need to rollback to the previous version:

### Option 1: Keep Database, Remove from UI

1. Remove `DatabasePanel` import from `App.jsx`
2. Remove `<DatabasePanel />` component
3. App works without database features

### Option 2: Full Rollback

```bash
# Restore from backup
git checkout HEAD~1  # Or your previous commit

# Or restore files manually
cp backup/* .
```

### Option 3: Just Remove Database

```bash
# Stop PostgreSQL container
docker-compose stop postgres

# Or stop local PostgreSQL
brew services stop postgresql@15
```

App continues to work without database features.

## Performance Notes

### Database Size

Typical storage per company:
- Basic info: ~1 KB
- With contact info: ~2 KB
- With Finder.fi data: ~3-5 KB
- With AI insights: ~4-6 KB

For 1,000 companies: ~5 MB
For 10,000 companies: ~50 MB

### Query Performance

- Indexed queries (by business_id, session_id, business_line): < 10ms
- Full-text search: 10-100ms depending on dataset
- Pagination recommended for > 1,000 results

### Recommendations

1. **Regular cleanup:** Delete old sessions you don't need
2. **Use indexes:** Already configured for common queries
3. **Paginate:** Use limit/offset for large results
4. **Backup:** Regular backups for production

## Next Steps

After migration:

1. ✅ Run your first scrape and save to database
2. ✅ Test loading saved sessions
3. ✅ Try the search API
4. ✅ Set up automated backups
5. ✅ Read full API documentation (API.md)

## Support

If you encounter issues:

1. Check logs:
   ```bash
   # Docker
   docker-compose logs backend
   docker-compose logs postgres
   
   # Local
   tail -f app.log
   ```

2. Verify database connection:
   ```bash
   psql -U postgres ytj_scraper -c "SELECT COUNT(*) FROM scrape_sessions;"
   ```

3. Test API endpoints:
   ```bash
   curl http://localhost:5001/api/db/sessions
   ```

## Summary

**What You Get:**
- 📊 Persistent storage in PostgreSQL
- 🔍 Search and query capabilities
- 📅 Session-based versioning
- 🔄 REST API for integration
- 💾 Backup and restore support

**What Stays the Same:**
- ✅ All existing features work
- ✅ Same scraping process
- ✅ Same enrichment workflow
- ✅ JSON/CSV exports available
- ✅ No breaking changes

**Migration Time:** ~15 minutes

Happy scraping! 🚀