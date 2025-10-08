"""
Database models for PostgreSQL
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class ScrapeSession(Base):
    """Represents a scraping session with timestamp"""
    __tablename__ = 'scrape_sessions'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    business_line = Column(String(10), index=True)
    business_line_name = Column(String(255))
    location = Column(String(100))
    company_form = Column(String(50))
    total_companies = Column(Integer, default=0)
    status = Column(String(50), default='completed')  # completed, failed, running
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    companies = relationship("Company", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'business_line': self.business_line,
            'business_line_name': self.business_line_name,
            'location': self.location,
            'company_form': self.company_form,
            'total_companies': self.total_companies,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Company(Base):
    """Company information"""
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('scrape_sessions.id'), nullable=False, index=True)
    
    # Basic info
    business_id = Column(String(20), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    company_form = Column(String(100))
    main_business_line = Column(String(255))
    main_business_line_code = Column(String(10), index=True)
    website = Column(String(500))
    registration_date = Column(String(50))
    status = Column(String(50))
    
    # Address (stored as JSON for flexibility)
    address = Column(JSON)
    
    # Contact info (stored as JSON)
    contact_info = Column(JSON)
    
    # Finder.fi data (stored as JSON)
    # Structure: {
    #   'verified_on_finder': bool,
    #   'finder_url': str,
    #   'basic_info': {'employees': str, 'founded': str},
    #   'financials': {'revenue': str, 'operating_profit': str, 'financial_year': str},
    #   'contact': {'address': str, 'phone': str, 'email': str},
    #   'key_people': [{'name': str, 'title': str, 'email': str}]
    # }
    finder_data = Column(JSON)
    
    # AI insights (stored as JSON)
    ai_insights = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ScrapeSession", back_populates="companies")
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'business_id': self.business_id,
            'name': self.name,
            'company_form': self.company_form,
            'main_business_line': self.main_business_line,
            'main_business_line_code': self.main_business_line_code,
            'website': self.website,
            'registration_date': self.registration_date,
            'status': self.status,
            'address': self.address,
            'contact_info': self.contact_info,
            'finder_data': self.finder_data,
            'ai_insights': self.ai_insights,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Database connection
def get_db_url():
    """Get database URL from environment or use default"""
    return os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/ytj_scraper'
    )


def init_db():
    """Initialize database and create tables"""
    engine = create_engine(get_db_url())
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Get database session"""
    engine = create_engine(get_db_url())
    Session = sessionmaker(bind=engine)
    return Session()
