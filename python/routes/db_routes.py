"""
REST API routes for database operations
"""
from flask import Blueprint, request, jsonify
from services.db_service import DatabaseService

db_bp = Blueprint('db', __name__, url_prefix='/api/db')


@db_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """GET all scrape sessions
    Query params:
        - limit: number of sessions to return (default: 50)
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        sessions = DatabaseService.get_all_sessions(limit=limit)
        return jsonify({
            'success': True,
            'count': len(sessions),
            'sessions': sessions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """GET a specific session by ID"""
    try:
        session = DatabaseService.get_session_by_id(session_id)
        if session:
            return jsonify({
                'success': True,
                'session': session
            })
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/sessions/latest', methods=['GET'])
def get_latest_session():
    """GET the most recent scrape session"""
    try:
        session = DatabaseService.get_latest_session()
        if session:
            return jsonify({
                'success': True,
                'session': session
            })
        return jsonify({'success': False, 'error': 'No sessions found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """DELETE a session and all its companies"""
    try:
        success = DatabaseService.delete_session(session_id)
        if success:
            return jsonify({
                'success': True,
                'message': f'Session {session_id} deleted successfully'
            })
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/companies', methods=['GET'])
def get_companies():
    """GET all companies with pagination
    Query params:
        - limit: number of companies to return (default: 100)
        - offset: pagination offset (default: 0)
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        companies = DatabaseService.get_all_companies(limit=limit, offset=offset)
        return jsonify({
            'success': True,
            'count': len(companies),
            'limit': limit,
            'offset': offset,
            'companies': companies
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/companies/session/<int:session_id>', methods=['GET'])
def get_companies_by_session(session_id):
    """GET all companies from a specific session"""
    try:
        companies = DatabaseService.get_companies_by_session(session_id)
        return jsonify({
            'success': True,
            'session_id': session_id,
            'count': len(companies),
            'companies': companies
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/companies/business-line/<business_line_code>', methods=['GET'])
def get_companies_by_business_line(business_line_code):
    """GET companies by business line code
    Query params:
        - limit: number of companies to return (default: 100)
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        companies = DatabaseService.get_companies_by_business_line(
            business_line_code, 
            limit=limit
        )
        return jsonify({
            'success': True,
            'business_line_code': business_line_code,
            'count': len(companies),
            'companies': companies
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/companies/latest', methods=['GET'])
def get_latest_results():
    """GET latest scraping results (from most recent session)
    Query params:
        - limit: number of companies to return (default: 50)
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        companies = DatabaseService.get_latest_results(limit=limit)
        return jsonify({
            'success': True,
            'count': len(companies),
            'companies': companies
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/companies/search', methods=['GET'])
def search_companies():
    """Search companies by name or business ID
    Query params:
        - q: search query
        - limit: number of results (default: 50)
    """
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 50, type=int)
        
        if not query:
            return jsonify({
                'success': False, 
                'error': 'Search query (q) is required'
            }), 400
        
        companies = DatabaseService.search_companies(query, limit=limit)
        return jsonify({
            'success': True,
            'query': query,
            'count': len(companies),
            'companies': companies
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/companies/<int:company_id>', methods=['PUT'])
def update_company(company_id):
    """UPDATE a company's information"""
    try:
        updates = request.json
        if not updates:
            return jsonify({
                'success': False, 
                'error': 'No updates provided'
            }), 400
        
        company = DatabaseService.update_company(company_id, updates)
        if company:
            return jsonify({
                'success': True,
                'message': 'Company updated successfully',
                'company': company
            })
        return jsonify({'success': False, 'error': 'Company not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@db_bp.route('/save-results', methods=['POST'])
def save_current_results():
    """POST current scraping results to database
    Body should contain:
        - companies: list of company objects
        - business_line: optional
        - business_line_name: optional
        - location: optional
        - company_form: optional
    """
    try:
        data = request.json
        companies_data = data.get('companies', [])
        
        if not companies_data:
            return jsonify({
                'success': False,
                'error': 'No companies to save'
            }), 400
        
        # Create session
        session = DatabaseService.create_session(
            business_line=data.get('business_line'),
            business_line_name=data.get('business_line_name'),
            location=data.get('location'),
            company_form=data.get('company_form')
        )
        
        # Save companies
        saved_companies = DatabaseService.save_companies(
            session.id, 
            companies_data
        )
        
        # Mark session as completed
        DatabaseService.complete_session(
            session.id, 
            len(saved_companies),
            status='completed'
        )
        
        return jsonify({
            'success': True,
            'message': f'Saved {len(saved_companies)} companies',
            'session_id': session.id,
            'timestamp': session.timestamp.isoformat(),
            'count': len(saved_companies)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    