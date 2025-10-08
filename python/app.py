from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from threading import Thread

# Import services
from services.finder_service import run_finder_validation
from services.scraper_service import run_scraper
from services.enrichment_service import run_agent_enrichment
from services.cache_service import load_finder_cache
from utils.export_utils import export_to_csv

# Import database routes
from routes.db_routes import db_bp

# Import models
from models.status_models import scraping_status, validation_status, agent_status
from models.db_models import init_db

# Import config
from config import BUSINESS_LINES

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize database
print("Initializing database...")
try:
    init_db()
    print("✓ Database initialized successfully")
except Exception as e:
    print(f"⚠ Warning: Database initialization failed: {e}")
    print("  Database features will not be available")

# Register database blueprint
app.register_blueprint(db_bp)

# Add debug logging
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    """Start scraping with given parameters"""
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping already in progress'}), 400
    
    params = request.json
    
    # Start scraping in background thread
    thread = Thread(target=run_scraper, args=(params, scraping_status))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scraping started', 'status': 'running'})


@app.route('/api/validate', methods=['POST'])
def validate_with_finder():
    """Validate leads with finder.fi"""
    if validation_status['is_running']:
        return jsonify({'error': 'Validation already running'}), 400
    
    data = request.json
    leads = data.get('leads', [])
    config = data.get('config', {})  # Get optional config
    
    if not leads:
        return jsonify({'error': 'No leads provided'}), 400
    
    # Start validation in background thread
    thread = Thread(target=run_finder_validation, args=(leads, validation_status, scraping_status, config))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Validation started', 'status': 'running'})


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current scraping status"""
    print("Status endpoint called")
    return jsonify({
        'scraping': scraping_status,
        'agent': agent_status,
        'validation': validation_status
    })


@app.route('/api/results', methods=['GET'])
def get_results():
    """Get current results"""
    return jsonify(scraping_status['results'])


@app.route('/api/enrich', methods=['POST'])
def enrich_with_agent():
    """Enrich leads with ChatGPT agent"""
    if agent_status['is_running']:
        return jsonify({'error': 'Agent already running'}), 400
    
    data = request.json
    leads = data.get('leads', [])
    openai_api_key = data.get('openai_api_key')
    
    if not openai_api_key:
        return jsonify({'error': 'OpenAI API key required'}), 400
    
    # Start agent in background thread
    thread = Thread(target=run_agent_enrichment, args=(leads, openai_api_key, agent_status, scraping_status))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Agent enrichment started', 'status': 'running'})


@app.route('/api/download', methods=['GET'])
def download_results():
    """Download results as JSON file"""
    filename = request.args.get('filename', 'companies_leads.json')
    
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404


@app.route('/api/download-csv', methods=['GET'])
def download_csv():
    """Download results as CSV file"""
    filename = request.args.get('filename', 'companies_leads.csv')
    
    # If CSV doesn't exist but JSON does, create it
    json_filename = filename.replace('.csv', '.json')
    if not os.path.exists(filename) and os.path.exists(json_filename):
        with open(json_filename, 'r', encoding='utf-8') as f:
            leads = json.load(f)
        export_to_csv(leads, filename)
    
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True, mimetype='text/csv')
    else:
        return jsonify({'error': 'File not found'}), 404


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear Finder.fi cache"""
    try:
        cache_file = 'finder_cache.json'
        if os.path.exists(cache_file):
            os.remove(cache_file)
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics"""
    cache = load_finder_cache()
    return jsonify({
        'entries': len(cache),
        'size_kb': os.path.getsize('finder_cache.json') / 1024 if os.path.exists('finder_cache.json') else 0
    })


@app.route('/api/business-lines', methods=['GET'])
def get_business_lines():
    """Get business line codes from TOL 2025"""
    return jsonify(BUSINESS_LINES)


if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5001")
    app.run(debug=True, port=5001, host='0.0.0.0')
    