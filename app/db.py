
import os
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse

def get_connection(dsn: str):
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set")
    # psycopg2 supports the full URL; keep sslmode=require if provided by Render
    conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn
