#!/usr/bin/env python3
"""
Quick database check - what tables exist and have data
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

def quick_check():
    """Quick check of database state"""
    try:
        from app.db import get_connection
        from app.config import Config
        
        config = Config()
        dsn = config.DATABASE_URL
        
        if not dsn:
            print("❌ DATABASE_URL not set")
            return
        
        print("🔍 Quick Database Check")
        print("=" * 40)
        
        with get_connection(dsn) as conn:
            with conn.cursor() as cur:
                # Check what tables exist
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cur.fetchall()
                print(f"📋 Tables found: {[t['table_name'] for t in tables]}")
                
                # Check key tables for data
                key_tables = ['users', 'ubis', 'partido', 'metadata', 'voto']
                print(f"\n📊 Data check:")
                
                for table in key_tables:
                    if table in [t['table_name'] for t in tables]:
                        cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                        count = cur.fetchone()['count']
                        status = "✅" if count > 0 else "⚠️"
                        print(f"  {status} {table}: {count} rows")
                    else:
                        print(f"  ❌ {table}: table not found")
                
                # Quick sample from users table (auth)
                print(f"\n🔐 Auth check (users table):")
                cur.execute("SELECT username FROM users LIMIT 3")
                users = cur.fetchall()
                if users:
                    print(f"  Users found: {[u['username'] for u in users]}")
                else:
                    print("  No users found!")
                
                # Quick sample from ubis table (data)
                print(f"\n🗺️  Data check (ubis table):")
                cur.execute("SELECT dept_name, muni_name FROM ubis LIMIT 3")
                locations = cur.fetchall()
                if locations:
                    print(f"  Locations found: {len(locations)}")
                    for loc in locations:
                        print(f"    {loc['dept_name']} - {loc['muni_name']}")
                else:
                    print("  No location data found!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_check()
