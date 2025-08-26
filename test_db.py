#!/usr/bin/env python3
"""
Database connection test script
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

def test_connection():
    """Test database connection and basic queries"""
    try:
        from app.db import get_connection
        from app.config import Config
        
        config = Config()
        dsn = config.DATABASE_URL
        
        print(f"Database URL: {dsn[:20]}..." if dsn else "No DATABASE_URL found")
        
        if not dsn:
            print("ERROR: DATABASE_URL environment variable is not set")
            return False
            
        # Test connection
        print("Testing database connection...")
        with get_connection(dsn) as conn:
            print("✓ Database connection successful")
            
            # Test basic query
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()
                print(f"✓ PostgreSQL version: {version['version']}")
                
                # Test table existence
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cur.fetchall()
                print(f"✓ Available tables: {[t['table_name'] for t in tables]}")
                
                # Test data in key tables
                for table in ['ubis', 'partido', 'metadata', 'voto']:
                    cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cur.fetchone()
                    print(f"✓ {table}: {count['count']} rows")
                
                # Test specific queries from the API
                print("\nTesting API queries...")
                
                # Test departments query
                cur.execute("""
                    SELECT DISTINCT dept_name
                    FROM ubis
                    WHERE dept_name IS NOT NULL AND dept_name <> ''
                    ORDER BY dept_name
                    LIMIT 5
                """)
                depts = cur.fetchall()
                print(f"✓ Departments (first 5): {[d['dept_name'] for d in depts]}")
                
                # Test parties query
                cur.execute("""
                    SELECT partido_name
                    FROM partido
                    WHERE partido_name IS NOT NULL AND partido_name <> ''
                    ORDER BY partido_name
                    LIMIT 5
                """)
                parties = cur.fetchall()
                print(f"✓ Parties (first 5): {[p['partido_name'] for p in parties]}")
                
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Database Connection Test")
    print("=" * 40)
    success = test_connection()
    if success:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Tests failed!")
        sys.exit(1)

