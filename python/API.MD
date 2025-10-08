# YTJ Scraper API Documentation

## Base URL
```
http://localhost:5001/api
```

## Database Endpoints

### Sessions

#### GET /db/sessions
Get all scrape sessions.

**Query Parameters:**
- `limit` (optional): Number of sessions to return (default: 50)

**Response:**
```json
{
  "success": true,
  "count": 5,
  "sessions": [
    {
      "id": 1,
      "timestamp": "2025-10-06T10:30:00",
      "business_line": "6201",
      "business_line_name": "Ohjelmistojen suunnittelu ja valmistus",
      "location": "Kuopio",
      "company_form": "OY",
      "total_companies": 15,
      "status": "completed",
      "created_at": "2025-10-06T10:30:00"
    }
  ]
}
```

#### GET /db/sessions/:id
Get a specific session by ID.

**Response:**
```json
{
  "success": true,
  "session": {
    "id": 1,
    "timestamp": "2025-10-06T10:30:00",
    ...
  }
}
```

#### GET /db/sessions/latest
Get the most recent scrape session.

**Response:**
```json
{
  "success": true,
  "session": {
    "id": 5,
    ...
  }
}
```

#### DELETE /db/sessions/:id
Delete a session and all its companies.

**Response:**
```json
{
  "success": true,
  "message": "Session 1 deleted successfully"
}
```

### Companies

#### GET /db/companies
Get all companies with pagination.

**Query Parameters:**
- `limit` (optional): Number of companies (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "count": 50,
  "limit": 100,
  "offset": 0,
  "companies": [...]
}
```

#### GET /db/companies/session/:session_id
Get all companies from a specific session.

**Response:**
```json
{
  "success": true,
  "session_id": 1,
  "count": 15,
  "companies": [...]
}
```

#### GET /db/companies/business-line/:code
Get companies by business line code.

**Query Parameters:**
- `limit` (optional): Number of companies (default: 100)

**Example:**
```
GET /db/companies/business-line/6201?limit=50
```

**Response:**
```json
{
  "success": true,
  "business_line_code": "6201",
  "count": 25,
  "companies": [...]
}
```

#### GET /db/companies/latest
Get latest scraping results (from most recent session).

**Query Parameters:**
- `limit` (optional): Number of companies (default: 50)

**Response:**
```json
{
  "success": true,
  "count": 15,
  "companies": [...]
}
```

#### GET /db/companies/search
Search companies by name or business ID.

**Query Parameters:**
- `q` (required): Search query
- `limit` (optional): Number of results (default: 50)

**Example:**
```
GET /db/companies/search?q=software&limit=20
```

**Response:**
```json
{
  "success": true,
  "query": "software",
  "count": 8,
  "companies": [...]
}
```

#### PUT /db/companies/:id
Update a company's information.

**Request Body:**
```json
{
  "website": "https://newwebsite.com",
  "contact_info": {
    "emails": ["new@email.com"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Company updated successfully",
  "company": {
    "id": 123,
    "name": "Example Oy",
    ...
  }
}
```

#### POST /db/save-results
Save current scraping results to database.

**Request Body:**
```json
{
  "companies": [...],
  "business_line": "6201",
  "business_line_name": "Ohjelmistojen suunnittelu",
  "location": "Kuopio",
  "company_form": "OY"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Saved 15 companies",
  "session_id": 1,
  "timestamp": "2025-10-06T10:30:00",
  "count": 15
}
```

## Existing Endpoints

### GET /api/status
Get current scraping, validation, and enrichment status.

### POST /api/scrape
Start scraping with parameters.

### POST /api/validate
Validate leads with Finder.fi.

### POST /api/enrich
Enrich leads with AI agent.

### GET /api/download
Download results as JSON.

### GET /api/download-csv
Download results as CSV.

### POST /api/cache/clear
Clear Finder.fi cache.

### GET /api/cache/stats
Get cache statistics.

### GET /api/business-lines
Get all business line codes.

## Error Responses

All endpoints return errors in this format:

```json
{
  "success": false,
  "error": "Error message here"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad request
- `404`: Not found
- `500`: Server error

## Usage Examples

### Save Current Results
```bash
curl -X POST http://localhost:5001/api/db/save-results \
  -H "Content-Type: application/json" \
  -d '{
    "companies": [...],
    "business_line": "6201",
    "location": "Kuopio"
  }'
```

### Get Latest Results
```bash
curl http://localhost:5001/api/db/companies/latest?limit=10
```

### Search Companies
```bash
curl "http://localhost:5001/api/db/companies/search?q=software&limit=20"
```

### Delete Old Session
```bash
curl -X DELETE http://localhost:5001/api/db/sessions/1
```