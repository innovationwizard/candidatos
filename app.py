from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
import pymysql
import bcrypt
import secrets
import logging
import os

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
logging.basicConfig(filename='users_are_mean.txt', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# MariaDB Configuration from Environment Variables
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME"),
    'charset': 'utf8mb4'
}

# Create MariaDB connection
def get_db():
    conn = pymysql.connect(**DB_CONFIG)
    return conn

# Routes (updated for MariaDB)
@app.route('/')
def health_check():
    return "API is live", 200  # ✅ This works

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    password_is = 'not empty' if password else 'empty'

    if not username or not password:
        logging.info(f"Login Input: username={username}, password={password_is} - FAIL: Missing credentials")
        return jsonify({'success': False, 'message': 'ACCESS DENIED'}), 401

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        session['username'] = username
        logging.info(f"Login Input: username={username}, password={password_is} - OK: Login successful")
        return jsonify({'success': True})
    else:
        logging.info(f"Login Input: username={username}, password={password_is} - FAIL: Invalid credentials")
        return jsonify({'success': False, 'message': 'ACCESS DENIED'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/departments', methods=['GET'])
def get_departments():
    if 'username' not in session:
        return jsonify({'error': 'ACCESS DENIED'}), 401

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT DISTINCT dept_name FROM UBIS ORDER BY dept_name')
    departments = [row['dept_name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(departments)

@app.route('/municipalities', methods=['GET'])
def get_municipalities():
    if 'username' not in session:
        return jsonify({'error': 'ACCESS DENIED'}), 401

    dept_name = request.args.get('dept_name')
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT DISTINCT muni_name FROM UBIS WHERE dept_name = %s ORDER BY muni_name', (dept_name,))
    municipalities = [row['muni_name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(municipalities)

@app.route('/parties', methods=['GET'])
def get_parties():
    if 'username' not in session:
        return jsonify({'error': 'ACCESS DENIED'}), 401

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT part_name FROM PART ORDER BY part_name')
    parties = [row['part_name'] for row in cursor.fetchall()]
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
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute('SELECT mesa FROM UBIS WHERE dept_name = %s AND muni_name = %s', (dept_name, muni_name))
    mesa_list = [row['mesa'] for row in cursor.fetchall()]
    if not mesa_list:
        conn.close()
        return jsonify({'error': 'NO HAY MESAS'}), 404
    placeholder = ','.join('%s' for _ in mesa_list)

    cursor.execute('SELECT part_id FROM PART WHERE part_name = %s', (part_name,))
    part_id = cursor.fetchone()
    if not part_id:
        conn.close()
        return jsonify({'error': 'NO HAY PARTIDO'}), 404
    part_id = part