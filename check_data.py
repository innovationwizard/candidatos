#!/usr/bin/env python3
"""
Check if there's data in the database tables
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

def check_data():
    """Check if there's data in the database tables"""
    print("=== Database Data Check ===")
    
    try:
        from app.db import get_connection
        from app.config import Config
        
        config = Config()
        dsn = config.DATABASE_URL
        
        if not dsn:
            print("❌ DATABASE_URL not set")
            return
        
        print("Connecting to database...")
        with get_connection(dsn) as conn:
            with conn.cursor() as cur:
                # Check each table for data
                tables = ['ubis', 'partido', 'metadata', 'voto']
                
                for table in tables:
                    print(f"\n--- {table.upper()} TABLE ---")
                    
                    # Count rows
                    cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cur.fetchone()
                    print(f"Total rows: {count['count']}")
                    
                    if count['count'] > 0:
                        # Show sample data
                        cur.execute(f"SELECT * FROM {table} LIMIT 3")
                        sample = cur.fetchall()
                        print("Sample data:")
                        for i, row in enumerate(sample, 1):
                            print(f"  Row {i}: {dict(row)}")
                    else:
                        print("❌ No data in this table!")
                
                # Test the specific queries from your API
                print(f"\n--- API QUERY TESTS ---")
                
                # Test departments query
                cur.execute("""
                    SELECT DISTINCT dept_name
                    FROM ubis
                    WHERE dept_name IS NOT NULL AND dept_name <> ''
                    ORDER BY dept_name
                    LIMIT 5
                """)
                depts = cur.fetchall()
                print(f"Departments query returned: {len(depts)} results")
                if depts:
                    print(f"Sample departments: {[d['dept_name'] for d in depts]}")
                else:
                    print("❌ No departments found!")
                
                # Test parties query
                cur.execute("""
                    SELECT partido_name
                    FROM partido
                    WHERE partido_name IS NOT NULL AND partido_name <> ''
                    ORDER BY partido_name
                    LIMIT 5
                """)
                parties = cur.fetchall()
                print(f"Parties query returned: {len(parties)} results")
                if parties:
                    print(f"Sample parties: {[p['partido_name'] for p in parties]}")
                else:
                    print("❌ No parties found!")
                
                # Check if there are any non-null values at all
                print(f"\n--- NULL VALUE CHECK ---")
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) as count FROM {table} WHERE 1=1")
                    total = cur.fetchone()['count']
                    cur.execute(f"SELECT COUNT(*) as count FROM {table} WHERE dept_name IS NOT NULL OR partido_name IS NOT NULL OR mesa IS NOT NULL")
                    non_null = cur.fetchone()['count']
                    print(f"{table}: {total} total rows, {non_null} with non-null values")
        
        print("\n✅ Database connection and queries completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_data()
