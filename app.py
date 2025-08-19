from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import bcrypt
import secrets
import logging
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

# CORS for candidatos.app frontend
CORS(app, supports_credentials=True, origins=[
    'https://candidatos.app',
    'https://www.candidatos.app'
], methods=['GET', 'POST', 'OPTIONS'], allow_headers=['Content-Type'])

# Logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# PostgreSQL Configuration from Environment Variables
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    logging.info(f"Using DATABASE_URL: {DATABASE_URL[:50]}...")
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
        'host': os.getenv("DB_HOST"),
        'port': os.getenv("DB_PORT", "5432"),
        'user': os.getenv("DB_USER"),
        'password': os.getenv("DB_PASSWORD"),
        'dbname': os.getenv("DB_NAME"),
        'sslmode': 'require'
    }
    if not all([DB_CONFIG['host'], DB_CONFIG['user'], DB_CONFIG['password'], DB_CONFIG['dbname']]):
        logging.error("Missing required DB environment variables")
        raise ValueError("Missing required DB environment variables")

# Create PostgreSQL connection
def get_db():
    logging.info(f"Connecting to database with config: {DB_CONFIG}")
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

# Routes
@app.route('/')
def health_check():
    return "It's alive!", 200

@app.route('/favicon.ico')
def favicon():
    return send_file('static/favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/logo.png')
def logo():
    return send_file('static/candidatos_logo.png', mimetype='image/png')

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
    # if 'username' not in session:
    #    return jsonify({'error': 'ACCESS DENIED'}), 401

    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT DISTINCT dept_name FROM ubis ORDER BY dept_name')
    departments = [row['dept_name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(departments)

@app.route('/municipalities', methods=['GET'])
def get_municipalities():
    # if 'username' not in session:
    #    return jsonify({'error': 'ACCESS DENIED'}), 401

    dept_name = request.args.get('dept_name')
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT DISTINCT muni_name FROM ubis WHERE dept_name = %s ORDER BY muni_name', (dept_name,))
    municipalities = [row['muni_name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(municipalities)

@app.route('/parties', methods=['GET'])
def get_parties():
    # if 'username' not in session:
    #    return jsonify({'error': 'ACCESS DENIED'}), 401

    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT partido_name FROM partido ORDER BY partido_name')
    parties = [row['partido_name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(parties)

@app.route('/results', methods=['GET'])
def get_results():
    # Check for session
    # if 'username' not in session:
    #    return jsonify({'error': 'ACCESS DENIED'}), 401

    # Fetch parameters from request
    dept_name = request.args.get('dept_name')
    muni_name = request.args.get('muni_name')
    part_name = request.args.get('part_name')

    # Validate if NOT all parameters are provided
    if not all([dept_name, muni_name, part_name]):
        logging.info(f"Input: dept_name={dept_name}, muni_name={muni_name}, part_name={part_name} - FAIL: Missing parameters")
        return jsonify({'error': 'ERROR'}), 400

    # Ask the db
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # 1. For list of mesas in dept AND muni
    cursor.execute('SELECT mesa FROM UBIS WHERE dept_name = %s AND muni_name = %s', (dept_name, muni_name))
    mesa_list = [row['mesa'] for row in cursor.fetchall()]

    if not mesa_list:
        conn.close()
        return jsonify({'error': 'NO HAY MESAS'}), 404

    # Use dynamic placeholder for variable number of mesas
    placeholder = ','.join(['%s'] * len(mesa_list))

    # 2. For list of party id, provided party name
    cursor.execute('SELECT partido_id FROM PARTIDO WHERE partido_name = %s', (part_name,))
    part_id_row = cursor.fetchone()

    if not part_id_row:
        conn.close()
        return jsonify({'error': 'NO HAY PARTIDO'}), 404

    part_id = part_id_row['partido_id']

    results = {
        'MUNI': {'empadronados': 0, 'votos_totales': 0, 'votos_recibidos': 0},
        'D_LN': {'empadronados': 0, 'votos_totales': 0, 'votos_recibidos': 0},
        'D_DI': {'empadronados': 0, 'votos_totales': 0, 'votos_recibidos': 0},
        'D_PA': {'empadronados': 0, 'votos_totales': 0, 'votos_recibidos': 0},
        'PRES': {'empadronados': 0, 'votos_totales': 0, 'votos_recibidos': 0},
        'TEAM': {'empadronados': 0, 'votos_totales': 0, 'votos_recibidos': 0}
    }

    types = {
        'MUNI': 'CORPORACION_MUNICIPAL',
        'D_LN': 'DIPUTADOS_NACIONAL',
        'D_DI': 'DIPUTADOS_DISTRITAL',
        'D_PA': 'PARLAMENTO_CENTROAMERICANO',
        'PRES': 'PRESIDENTE'
    }

    for tipo_key, tipo in types.items():
        cursor.execute(
            f'SELECT COALESCE(SUM(padron), 0) as padron, COALESCE(SUM(validos), 0) as validos '
            f'FROM METADATA WHERE tipo = %s AND mesa IN ({placeholder})',
            [tipo] + mesa_list
        )
        row = cursor.fetchone()
        results[tipo_key]['empadronados'] = row['padron']
        results[tipo_key]['votos_totales'] = row['validos']

    for tipo_key, tipo in types.items():
        cursor.execute(
            f'SELECT COALESCE(SUM(voto), 0) as votos '
            f'FROM VOTO WHERE tipo = %s AND partido_id = %s AND mesa IN ({placeholder})',
            [tipo, part_id] + mesa_list
        )
        row = cursor.fetchone()
        results[tipo_key]['votos_recibidos'] = row['votos']

    cursor.execute(
        f'SELECT COALESCE(SUM(voto), 0) as votos '
        f'FROM VOTO '
        f'WHERE tipo IN (%s, %s, %s, %s) AND partido_id = %s AND mesa IN ({placeholder})',
        ['DIPUTADOS_NACIONAL', 'PARLAMENTO_CENTROAMERICANO', 'PRESIDENTE', 'DIPUTADOS_DISTRITAL', part_id] + mesa_list
    )
    row = cursor.fetchone()
    results['TEAM']['votos_recibidos'] = row['votos']
    results['TEAM']['empadronados'] = sum(results[b]['empadronados'] for b in ['D_LN', 'D_DI', 'D_PA', 'PRES'])
    results['TEAM']['votos_totales'] = sum(results[b]['votos_totales'] for b in ['D_LN', 'D_DI', 'D_PA', 'PRES'])

    for tipo_key in results:
        vt = results[tipo_key].get('votos_totales', 0)
        vr = results[tipo_key].get('votos_recibidos', 0)
        em = results[tipo_key].get('empadronados', 0)
        participacion = (vr / vt * 100) if vt > 0 else 0
        eficiencia = (vr / em * 100) if em > 0 else 0
        results[tipo_key]['participacion'] = participacion
        results[tipo_key]['eficiencia'] = eficiencia
        print(f"{tipo_key} - Votos recibidos: {vr}, Votos totales: {vt}, Empadronados: {em}, Participacion: {participacion}%, Eficiencia: {eficiencia}%")

    print("Response JSON:", jsonify({
        'dept_name': dept_name,
        'muni_name': muni_name,
        'part_name': part_name,
        'results': results
    }).get_data(as_text=True))

    logging.info(f"Input: dept_name={dept_name}, muni_name={muni_name}, part_name={part_name} - Results generated successfully!")
    return jsonify({
        'dept_name': dept_name,
        'muni_name': muni_name,
        'part_name': part_name,
        'results': results
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
