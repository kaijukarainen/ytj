"""
Database service for storing and retrieving scraping results
"""
from models.db_models import ScrapeSession, Company, get_session
from datetime import datetime
from sqlalchemy import desc


class DatabaseService:
    """Service for database operations"""
    
    @staticmethod
    def create_session(business_line=None, business_line_name=None, 
                      location=None, company_form=None):
        """Create a new scrape session"""
        db = get_session()
        try:
            session = ScrapeSession(
                timestamp=datetime.utcnow(),
                business_line=business_line,
                business_line_name=business_line_name,
                location=location,
                company_form=company_form,
                status='running'
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        finally:
            db.close()
    
    @staticmethod
    def complete_session(session_id, total_companies, status='completed'):
        """Mark session as completed"""
        db = get_session()
        try:
            session = db.query(ScrapeSession).filter_by(id=session_id).first()
            if session:
                session.total_companies = total_companies
                session.status = status
                db.commit()
        finally:
            db.close()
    
    @staticmethod
    def save_companies(session_id, companies_data):
        """Save companies to database"""
        db = get_session()
        try:
            saved_companies = []
            for company_data in companies_data:
                company = Company(
                    session_id=session_id,
                    business_id=company_data.get('business_id'),
                    name=company_data.get('name'),
                    company_form=company_data.get('company_form'),
                    main_business_line=company_data.get('main_business_line'),
                    main_business_line_code=company_data.get('main_business_line_code'),
                    website=company_data.get('website'),
                    registration_date=company_data.get('registration_date'),
                    status=company_data.get('status'),
                    address=company_data.get('address'),
                    contact_info=company_data.get('contact_info'),
                    finder_data=company_data.get('finder_data'),
                    ai_insights=company_data.get('ai_insights')
                )
                db.add(company)
                saved_companies.append(company)
            
            db.commit()
            return [c.to_dict() for c in saved_companies]
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    @staticmethod
    def get_all_sessions(limit=50):
        """Get all scrape sessions"""
        db = get_session()
        try:
            sessions = db.query(ScrapeSession)\
                        .order_by(desc(ScrapeSession.timestamp))\
                        .limit(limit)\
                        .all()
            return [s.to_dict() for s in sessions]
        finally:
            db.close()
    
    @staticmethod
    def get_session_by_id(session_id):
        """Get a specific session"""
        db = get_session()
        try:
            session = db.query(ScrapeSession).filter_by(id=session_id).first()
            if session:
                return session.to_dict()
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_latest_session():
        """Get the most recent scrape session"""
        db = get_session()
        try:
            session = db.query(ScrapeSession)\
                        .order_by(desc(ScrapeSession.timestamp))\
                        .first()
            if session:
                return session.to_dict()
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_companies_by_session(session_id):
        """Get all companies from a specific session"""
        db = get_session()
        try:
            companies = db.query(Company)\
                         .filter_by(session_id=session_id)\
                         .all()
            return [c.to_dict() for c in companies]
        finally:
            db.close()
    
    @staticmethod
    def get_companies_by_business_line(business_line_code, limit=100):
        """Get companies by business line code from latest sessions"""
        db = get_session()
        try:
            companies = db.query(Company)\
                         .filter_by(main_business_line_code=business_line_code)\
                         .order_by(desc(Company.created_at))\
                         .limit(limit)\
                         .all()
            return [c.to_dict() for c in companies]
        finally:
            db.close()
    
    @staticmethod
    def get_latest_results(limit=50):
        """Get latest scraping results (companies from most recent session)"""
        db = get_session()
        try:
            # Get latest session
            latest_session = db.query(ScrapeSession)\
                              .order_by(desc(ScrapeSession.timestamp))\
                              .first()
            
            if not latest_session:
                return []
            
            # Get companies from that session
            companies = db.query(Company)\
                         .filter_by(session_id=latest_session.id)\
                         .limit(limit)\
                         .all()
            
            return [c.to_dict() for c in companies]
        finally:
            db.close()
    
    @staticmethod
    def get_all_companies(limit=100, offset=0):
        """Get all companies with pagination"""
        db = get_session()
        try:
            companies = db.query(Company)\
                         .order_by(desc(Company.created_at))\
                         .limit(limit)\
                         .offset(offset)\
                         .all()
            return [c.to_dict() for c in companies]
        finally:
            db.close()
    
    @staticmethod
    def delete_session(session_id):
        """Delete a session and all its companies"""
        db = get_session()
        try:
            session = db.query(ScrapeSession).filter_by(id=session_id).first()
            if session:
                db.delete(session)
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    @staticmethod
    def update_company(company_id, updates):
        """Update a company's information"""
        db = get_session()
        try:
            company = db.query(Company).filter_by(id=company_id).first()
            if company:
                for key, value in updates.items():
                    if hasattr(company, key):
                        setattr(company, key, value)
                company.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(company)
                return company.to_dict()
            return None
        finally:
            db.close()
    
    @staticmethod
    def search_companies(query, limit=50):
        """Search companies by name or business ID"""
        db = get_session()
        try:
            companies = db.query(Company)\
                         .filter(
                             (Company.name.ilike(f'%{query}%')) |
                             (Company.business_id.ilike(f'%{query}%'))
                         )\
                         .limit(limit)\
                         .all()
            return [c.to_dict() for c in companies]
        finally:
            db.close()
            