#!/usr/bin/env python3
"""
Database initialization script
Run this to create the database tables
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.db_models import init_db, get_db_url
from sqlalchemy import create_engine, text


def check_database_connection():
    """Check if database is accessible"""
    try:
        engine = create_engine(get_db_url())
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def create_tables():
    """Create all database tables"""
    try:
        print("\nCreating database tables...")
        engine = init_db()
        print("✓ Tables created successfully")
        
        # Print table info
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\nCreated {len(tables)} tables:")
        for table in tables:
            columns = inspector.get_columns(table)
            print(f"  - {table} ({len(columns)} columns)")
        
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_database_info():
    """Show current database configuration"""
    db_url = get_db_url()
    
    # Parse URL to hide password
    from urllib.parse import urlparse
    parsed = urlparse(db_url)
    safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port}{parsed.path}"
    
    print("\n" + "="*60)
    print("Database Configuration")
    print("="*60)
    print(f"Database URL: {safe_url}")
    print("="*60 + "\n")


if __name__ == '__main__':
    print("YTJ Scraper - Database Initialization")
    print("="*60)
    
    show_database_info()
    
    # Check connection
    if not check_database_connection():
        print("\n⚠ Please ensure PostgreSQL is running and accessible")
        print("  Default connection: postgresql://postgres:postgres@localhost:5432/ytj_scraper")
        print("\n  You can set a custom DATABASE_URL environment variable:")
        print("  export DATABASE_URL='postgresql://user:password@host:port/database'")
        sys.exit(1)
    
    # Create tables
    if create_tables():
        print("\n✓ Database initialization complete!")
        print("\nYou can now start the application:")
        print("  python app.py")
    else:
        print("\n✗ Database initialization failed")
        sys.exit(1)
        