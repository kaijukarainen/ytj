# Database Setup Guide

## Overview

This application now includes PostgreSQL database integration for persistent storage of scraping results. Each scraping session is saved with a timestamp, allowing you to:

- Save and retrieve scraping results
- Query companies by business line
- Track scraping history
- Avoid duplicate work
- Access results via REST API

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Start all services including PostgreSQL
docker-compose up -d

# Database is automatically initialized
```

### Option 2: Local PostgreSQL

#### 1. Install PostgreSQL

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download and install from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)

#### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE ytj_scraper;

# Exit
\q
```

#### 3. Set Environment Variable (Optional)

```bash
# Default connection string (if different, set this):
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/ytj_scraper'
```

#### 4. Install Python Dependencies

```bash
cd python
pip install -r requirements.txt
```

#### 5. Initialize Database

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

✓ Database initialization complete!
```

#### 6. Start Application

```bash
python app.py
```

## Database Schema

### Table: `scrape_sessions`

Stores metadata about each scraping session.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| timestamp | DateTime | When scraping occurred |
| business_line | String(10) | Business line code filter |
| business_line_name | String(255) | Business line name |
| location | String(100) | Location filter |
| company_form | String(50) | Company form filter |
| total_companies | Integer | Number of companies in session |
| status | String(50) | completed, failed, running |
| created_at | DateTime | Record creation time |

### Table: `companies`

Stores individual company information.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| session_id | Integer | Foreign key to scrape_sessions |
| business_id | String(20) | Finnish business ID (Y-tunnus) |
| name | String(255) | Company name |
| company_form | String(100) | Company legal form |
| main_business_line | String(255) | Business line description |
| main_business_line_code | String(10) | Business line code |
| website | String(500) | Company website |
| registration_date | String(50) | Registration date |
| status | String(50) | Company status |
| address | JSON | Address information |
| contact_info | JSON | Contact details, emails, phones |
| finder_data | JSON | Finder.fi validation data |
| ai_insights | JSON | AI-generated insights |
| created_at | DateTime | Record creation time |
| updated_at | DateTime | Last update time |

## Using the Database

### From the UI

1. **Scrape companies** as usual
2. Click **"Save to DB"** button in the Database panel
3. View saved sessions in the Recent Sessions list
4. Click on a session to load and view its companies
5. Delete old sessions using the trash icon

### From the API

See [API.md](API.md) for complete documentation.

**Save current results:**
```bash
curl -X POST http://localhost:5001/api/db/save-results \
  -H "Content-Type: application/json" \
  -d '{"companies": [...], "business_line": "6201"}'
```

**Get latest results:**
```bash
curl http://localhost:5001/api/db/companies/latest
```

**Search companies:**
```bash
curl "http://localhost:5001/api/db/companies/search?q=software"
```

**Get companies by business line:**
```bash
curl http://localhost:5001/api/db/companies/business-line/6201
```

## Data Flow

```
Scraping → Results in Memory → Save to DB → Database Storage
                ↓
         Display in UI
                ↓
         Download JSON/CSV
```

After saving to database:
```
Database → Load Session → Display Results
        → Query by Business Line
        → Search Companies
        → Export to JSON/CSV
```

## Common Operations

### View All Sessions
```python
from services.db_service import DatabaseService

sessions = DatabaseService.get_all_sessions(limit=10)
for session in sessions:
    print(f"Session {session['id']}: {session['total_companies']} companies")
```

### Load Specific Session
```python
companies = DatabaseService.get_companies_by_session(session_id=1)
print(f"Found {len(companies)} companies")
```

### Search Companies
```python
results = DatabaseService.search_companies(query="software", limit=20)
for company in results:
    print(f"{company['name']} - {company['business_id']}")
```

### Query by Business Line
```python
companies = DatabaseService.get_companies_by_business_line("6201", limit=50)
print(f"Found {len(companies)} software companies")
```

## Maintenance

### Backup Database

```bash
# Docker
docker exec ytj-scraper-postgres pg_dump -U postgres ytj_scraper > backup.sql

# Local
pg_dump -U postgres ytj_scraper > backup.sql
```

### Restore Database

```bash
# Docker
docker exec -i ytj-scraper-postgres psql -U postgres ytj_scraper < backup.sql

# Local
psql -U postgres ytj_scraper < backup.sql
```

### Clear All Data

```bash
# Connect to database
psql -U postgres ytj_scraper

# Delete all data (keeps schema)
DELETE FROM companies;
DELETE FROM scrape_sessions;

# Or drop and recreate
DROP DATABASE ytj_scraper;
CREATE DATABASE ytj_scraper;
```

Then re-run:
```bash
python init_db.py
```

## Troubleshooting

### Connection Error

**Error:** `could not connect to server`

**Solution:**
1. Check PostgreSQL is running: `pg_isready`
2. Verify connection string in DATABASE_URL
3. Check PostgreSQL is listening: `netstat -an | grep 5432`

### Authentication Error

**Error:** `password authentication failed`

**Solution:**
1. Check username/password in DATABASE_URL
2. Update PostgreSQL password: `ALTER USER postgres WITH PASSWORD 'newpassword';`

### Tables Not Created

**Error:** Tables missing

**Solution:**
```bash
cd python
python init_db.py
```

### Port Already in Use

**Error:** `port 5432 already in use`

**Solution:**
1. Stop other PostgreSQL instance
2. Or use different port in DATABASE_URL

## Performance Tips

1. **Indexes:** Business ID, business line code, and session ID are automatically indexed
2. **Pagination:** Use `limit` and `offset` for large result sets
3. **Cleanup:** Periodically delete old sessions you don't need
4. **Backup:** Regular backups recommended for production use

## Security Notes

1. **Production:** Change default PostgreSQL password
2. **Network:** Don't expose PostgreSQL port publicly
3. **Environment:** Use environment variables for credentials
4. **SSL:** Enable SSL for remote connections

## Next Steps

- Set up automated backups
- Configure connection pooling for high load
- Add full-text search indexes
- Implement data retention policies
- Set up monitoring and alerts