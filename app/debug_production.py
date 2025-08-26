#!/usr/bin/env python3
"""
Production Database Debug Script for Render
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def debug_production():
    """Debug production database connection"""
    print("=== Production Database Debug ===")
    
    # Check environment variables
    database_url = os.getenv('DATABASE_URL')
    flask_env = os.getenv('FLASK_ENV', 'production')
    secret_key = os.getenv('SECRET_KEY')
    
    print(f"FLASK_ENV: {flask_env}")
    print(f"DATABASE_URL set: {'Yes' if database_url else 'No'}")
    print(f"SECRET_KEY set: {'Yes' if secret_key else 'No'}")
    
    if not database_url:
        print("❌ DATABASE_URL is not set in Render environment variables")
        print("   Go to Render dashboard → Environment Variables → Add DATABASE_URL")
        return False
    
    try:
        import psycopg2
        import psycopg2.extras
        
        # Test connection
        print(f"Testing connection to: {database_url[:30]}...")
        conn = psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)
        
        with conn.cursor() as cur:
            # Check tables
            cur.execute("""
                SELECT table_name, COUNT(*) as row_count
                FROM information_schema.tables t
                LEFT JOIN (
                    SELECT 'ubis' as table_name, COUNT(*) as cnt FROM ubis
                    UNION ALL
                    SELECT 'partido' as table_name, COUNT(*) as cnt FROM partido
                    UNION ALL
                    SELECT 'metadata' as table_name, COUNT(*) as cnt FROM metadata
                    UNION ALL
                    SELECT 'voto' as table_name, COUNT(*) as cnt FROM voto
                ) data ON t.table_name = data.table_name
                WHERE t.table_schema = 'public' AND t.table_name IN ('ubis', 'partido', 'metadata', 'voto')
                ORDER BY t.table_name
            """)
            
            tables = cur.fetchall()
            print("\nTable Status:")
            for table in tables:
                print(f"  {table['table_name']}: {table['row_count']} rows")
        
        conn.close()
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = debug_production()
    sys.exit(0 if success else 1)
