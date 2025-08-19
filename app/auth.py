# auth.py
from flask import Blueprint, request, jsonify, session, current_app
import bcrypt
from db import get_connection  # adjust to ".db" only if you're using a package

bp = Blueprint("auth", __name__, url_prefix="")

def _get_user(conn, username: str):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT username, password FROM users WHERE username = %s LIMIT 1",
            (username,),
        )
        return cur.fetchone()

@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").encode("utf-8")
    if not username or not password:
        return jsonify({"success": False, "message": "Missing credentials"}), 400

    dsn = current_app.config["DATABASE_URL"]
    try:
        with get_connection(dsn) as conn:
            row = _get_user(conn, username)
            if not row:
                return jsonify({"success": False, "message": "Invalid user or password"}), 401

            stored_hash = row["password"] or ""
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode("utf-8")

            if not bcrypt.checkpw(password, stored_hash):
                return jsonify({"success": False, "message": "Invalid user or password"}), 401

            session["uid"] = row["username"]
            session["uname"] = row["username"]
            return jsonify({"success": True})
    except Exception:
        return jsonify({"success": False, "message": "Auth error"}), 500

@bp.post("/logout")
def logout():
    session.clear()
    return jsonify({"success": True})
