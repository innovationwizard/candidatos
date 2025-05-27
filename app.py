from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import bcrypt
import secrets
import logging
import os
from urllib.parse import urlparse

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

# CORS for Namecheap frontend
CORS(app, supports_credentials=True, origins=[
    'https://ndor.co',
    'https://www.ndor.co'
])

# Logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# PostgreSQL Configuration from Environment Variables
DATABASE_URL = os.getenv("postgresql://postgres:AfzCdlJXGrviGQPnAEMmSOhuNFrCNHke@gondola.proxy.rlwy.net:38834/railway")
if DATABASE_URL:
    url = urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': url.hostname,
        'port': url.port,
        'user': url.username,
        'password': url.password,
        'dbname': url.path[1:],
        'sslmode': 'require'
    }
else:
    DB_CONFIG = {
        'host': os.getenv("postgres.railway.internal"),
        'user': os.getenv("postgres"),
        'password': os.getenv("AfzCdlJXGrviGQPnAEMmSOhuNFrCNHke"),
        'dbname': os.getenv("railway"),
        'port': os.getenv("5432"),
        'sslmode': 'require'
    }

# Create PostgreSQL connection
def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

# Routes
@app.route('/')
def health_check():
    return "API is live", 200

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if data is None:
            logging.warning("Login request missing or invalid JSON")
            return jsonify(success=False, message="Missing JSON body"), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify(success=False, message="Missing username or password"), 400

        logging.info(f"Login attempt: username={username}")

        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'] = username
            conn.commit()
            conn.close()
            return jsonify(success=True)

        conn.close()
        return jsonify(success=False, message="Invalid credentials"), 401

    except Exception as e:
        logging.exception("Login route failed")
        return jsonify(success=False, message="Server error"), 500

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/departments', methods=['GET'])
def get_departments():
    if 'username' not in session:
        return jsonify({'error': 'ACCESS DENIED'}), 401

    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT DISTINCT dept_name FROM ubis ORDER BY dept_name')
    departments = [row['dept_name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(departments)

@app.route('/municipalities', methods=['GET'])
def get_municipalities():
    if 'username' not in session:
        return jsonify({'error': 'ACCESS DENIED'}), 401

    dept_name = request.args.get('dept_name')
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT DISTINCT muni_name FROM ubis WHERE dept_name = %s ORDER BY muni_name', (dept_name,))
    municipalities = [row['muni_name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(municipalities)

@app.route('/parties', methods=['GET'])
def get_parties():
    if 'username' not in session:
        return jsonify({'error': 'ACCESS DENIED'}), 401

    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT partido_name FROM partido ORDER BY partido_name')
    parties = [row['partido_name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(parties)

@app.route('/results', methods=['GET'])
def get_results():
    if 'username' not in session:
        return jsonify({'error': 'ACCESS DENIED'}), 401

    dept_name = request.args.get('dept_name')
    muni_name = request.args.get('muni_name')
    part_name = request.args.get('part_name')

    if not all([dept_name, muni_name, part_name]):
        logging.info(f"Input: dept_name={dept_name}, muni_name={muni_name}, part_name={part_name} - FAIL: Missing parameters")
        return jsonify({'error': 'ERROR'}), 400

    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Get mesas for the department and municipality
    cursor.execute('SELECT mesa FROM ubis WHERE dept_name = %s AND muni_name = %s', (dept_name, muni_name))
    mesa_list = [row['mesa'] for row in cursor.fetchall()]
    if not mesa_list:
        conn.close()
        return jsonify({'error': 'NO HAY MESAS'}), 404

    # Get partido_id for the party
    cursor.execute('SELECT partido_id FROM partido WHERE partido_name = %s', (part_name,))
    party = cursor.fetchone()
    if not party:
        conn.close()
        return jsonify({'error': 'NO HAY PARTIDO'}), 404
    partido_id = party['partido_id']

    # Get vote counts from voto table
    placeholder = ','.join('%s' for _ in mesa_list)
    query = f"""
        SELECT v.mesa, v.tipo, v.voto
        FROM voto v
        WHERE v.mesa IN ({placeholder}) AND v.partido_id = %s
    """
    cursor.execute(query, (*mesa_list, partido_id))
    results = [
        {'mesa': row['mesa'], 'tipo': row['tipo'], 'votos': row['voto']}
        for row in cursor.fetchall()
    ]

    # Get metadata for additional context (e.g., validos, nulos)
    cursor.execute(f"""
        SELECT m.mesa, m.validos, m.nulos, m.en_blanco, m.emitidos
        FROM metadata m
        WHERE m.mesa IN ({placeholder})
    """, mesa_list)
    metadata = [
        {
            'mesa': row['mesa'],
            'validos': row['validos'],
            'nulos': row['nulos'],
            'en_blanco': row['en_blanco'],
            'emitidos': row['emitidos']
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return jsonify({
        'partido': part_name,
        'dept_name': dept_name,
        'muni_name': muni_name,
        'results': results,
        'metadata': metadata
    })

@app.route('/schema', methods=['GET'])
def get_schema():
    if 'username' not in session:
        return jsonify({'error': 'ACCESS DENIED'}), 401
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row['table_name'] for row in cursor.fetchall()]
        schema = {}
        for table in tables:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
            """, (table,))
            schema[table] = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(schema)
    except Exception as e:
        logging.exception("Schema route failed")
        return jsonify({'error': str(e)}), 500