#!/usr/bin/env python3
"""
Comprehensive Database Debugging Script
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

def check_environment():
    """Check environment variables and configuration"""
    print("=== Environment Check ===")
    
    # Check for .env file
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print("✓ .env file found")
    else:
        print("✗ .env file not found")
        print("  Create a .env file with your DATABASE_URL")
    
    # Check DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"✓ DATABASE_URL is set: {database_url[:30]}...")
    else:
        print("✗ DATABASE_URL is not set")
        print("  Set DATABASE_URL environment variable or add it to .env file")
    
    # Check other environment variables
    flask_env = os.getenv('FLASK_ENV', 'production')
    print(f"✓ FLASK_ENV: {flask_env}")
    
    secret_key = os.getenv('SECRET_KEY')
    if secret_key:
        print("✓ SECRET_KEY is set")
    else:
        print("✗ SECRET_KEY is not set")
    
    return database_url is not None

def test_database_connection(database_url):
    """Test the database connection"""
    print("\n=== Database Connection Test ===")
    
    try:
        import psycopg2
        import psycopg2.extras
        print("✓ psycopg2 is available")
    except ImportError as e:
        print(f"✗ psycopg2 not available: {e}")
        return False
    
    try:
        # Test connection
        print("Attempting to connect to database...")
        conn = psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)
        print("✓ Database connection successful")
        
        # Test basic query
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()
            print(f"✓ PostgreSQL version: {version['version']}")
            
            # Check if tables exist
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            table_names = [t['table_name'] for t in tables]
            print(f"✓ Available tables: {table_names}")
            
            # Check if required tables exist
            required_tables = ['ubis', 'partido', 'metadata', 'voto']
            missing_tables = [table for table in required_tables if table not in table_names]
            if missing_tables:
                print(f"✗ Missing required tables: {missing_tables}")
            else:
                print("✓ All required tables exist")
            
            # Check data in tables
            for table in required_tables:
                if table in table_names:
                    cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cur.fetchone()
                    print(f"✓ {table}: {count['count']} rows")
                else:
                    print(f"✗ {table}: table not found")
        
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        print("  Check your DATABASE_URL format and network connectivity")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_app_configuration():
    """Test the Flask app configuration"""
    print("\n=== App Configuration Test ===")
    
    try:
        from app.config import Config
        config = Config()
        
        print(f"✓ Config class loaded successfully")
        print(f"✓ DATABASE_URL from config: {'Set' if config.DATABASE_URL else 'Not set'}")
        print(f"✓ SECRET_KEY from config: {'Set' if config.SECRET_KEY else 'Not set'}")
        print(f"✓ CORS_ALLOW_ORIGINS: {config.CORS_ALLOW_ORIGINS}")
        
        return True
    except Exception as e:
        print(f"✗ App configuration error: {e}")
        return False

def test_api_queries():
    """Test the API queries"""
    print("\n=== API Query Test ===")
    
    try:
        from app.db import get_connection
        from app.config import Config
        
        config = Config()
        if not config.DATABASE_URL:
            print("✗ Cannot test API queries - DATABASE_URL not set")
            return False
        
        with get_connection(config.DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Test departments query
                cur.execute("""
                    SELECT DISTINCT dept_name
                    FROM ubis
                    WHERE dept_name IS NOT NULL AND dept_name <> ''
                    ORDER BY dept_name
                    LIMIT 5
                """)
                depts = cur.fetchall()
                print(f"✓ Departments query: {len(depts)} results")
                if depts:
                    print(f"  Sample: {[d['dept_name'] for d in depts[:3]]}")
                
                # Test parties query
                cur.execute("""
                    SELECT partido_name
                    FROM partido
                    WHERE partido_name IS NOT NULL AND partido_name <> ''
                    ORDER BY partido_name
                    LIMIT 5
                """)
                parties = cur.fetchall()
                print(f"✓ Parties query: {len(parties)} results")
                if parties:
                    print(f"  Sample: {[p['partido_name'] for p in parties[:3]]}")
        
        return True
        
    except Exception as e:
        print(f"✗ API query test failed: {e}")
        return False

def main():
    """Main debugging function"""
    print("Database Debugging Tool")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    
    # Test app configuration
    config_ok = test_app_configuration()
    
    # Test database connection if DATABASE_URL is available
    database_url = os.getenv('DATABASE_URL')
    db_ok = False
    if database_url:
        db_ok = test_database_connection(database_url)
        
        # Test API queries if database connection is ok
        if db_ok:
            api_ok = test_api_queries()
        else:
            api_ok = False
    else:
        print("\n=== API Query Test ===")
        print("✗ Skipped - DATABASE_URL not set")
        api_ok = False
    
    # Summary
    print("\n=== Summary ===")
    print(f"Environment: {'✓' if env_ok else '✗'}")
    print(f"Configuration: {'✓' if config_ok else '✗'}")
    print(f"Database Connection: {'✓' if db_ok else '✗'}")
    print(f"API Queries: {'✓' if api_ok else '✗'}")
    
    if not env_ok:
        print("\n🔧 To fix environment issues:")
        print("1. Create a .env file in the project root")
        print("2. Add your DATABASE_URL to the .env file")
        print("3. Example: DATABASE_URL=postgresql://user:pass@host:5432/dbname")
    
    if not db_ok and database_url:
        print("\n🔧 To fix database connection issues:")
        print("1. Check your DATABASE_URL format")
        print("2. Ensure the database server is running")
        print("3. Verify network connectivity")
        print("4. Check database credentials")
    
    if not api_ok and db_ok:
        print("\n🔧 To fix API query issues:")
        print("1. Check if tables have data")
        print("2. Verify table structure matches schema.sql")
        print("3. Check for any data loading issues")

if __name__ == "__main__":
    main()
