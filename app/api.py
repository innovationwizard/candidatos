from flask import Blueprint, request, jsonify, session, current_app
from .db import get_connection

bp = Blueprint("api", __name__, url_prefix="")

# Canonical mapping from UI ballot keys to DB "tipo" values
BALLOT_MAP = {
    "MUNI": "CORPORACION_MUNICIPAL",
    "D_LN": "DIPUTADOS_NACIONAL",
    "D_DI": "DIPUTADOS_DISTRITAL",
    "D_PA": "PARLAMENTO_CENTROAMERICANO",
    "PRES": "PRESIDENTE",
}
BALLOT_KEYS = list(BALLOT_MAP.keys())


def _require_login():
    return bool(session.get("uid"))


@bp.get("/departments")
def departments():
    if not _require_login():
        return jsonify({"error": "Unauthorized"}), 401
    dsn = current_app.config["DATABASE_URL"]
    with get_connection(dsn) as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT dept_name
            FROM ubis
            WHERE dept_name IS NOT NULL AND dept_name <> ''
            ORDER BY dept_name
        """)
        rows = cur.fetchall()
    return jsonify([r["dept_name"] for r in rows])


@bp.get("/municipalities")
def municipalities():
    if not _require_login():
        return jsonify({"error": "Unauthorized"}), 401
    dept_name = (request.args.get("dept_name") or "").strip()
    if not dept_name:
        return jsonify([])
    dsn = current_app.config["DATABASE_URL"]
    with get_connection(dsn) as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT muni_name
            FROM ubis
            WHERE dept_name = %s
            ORDER BY muni_name
        """, (dept_name,))
        rows = cur.fetchall()
    return jsonify([r["muni_name"] for r in rows])


@bp.get("/parties")
def parties():
    if not _require_login():
        return jsonify({"error": "Unauthorized"}), 401
    dsn = current_app.config["DATABASE_URL"]
    with get_connection(dsn) as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT partido_name
            FROM partido
            WHERE partido_name IS NOT NULL AND partido_name <> ''
            ORDER BY partido_name
        """)
        rows = cur.fetchall()
    return jsonify([r["partido_name"] for r in rows])


@bp.get("/results")
def results():
    """
    Returns structure:
    {
      "dept_name": "...",
      "muni_name": "...",
      "part_name": "...",
      "results": {
        "MUNI": {...},
        "D_LN": {...},
        "D_DI": {...},
        "D_PA": {...},
        "PRES": {...},
        "TEAM": {...}
      }
    }
    Each ballot map contains keys:
      empadronados, votos_totales, votos_recibidos, participacion, eficiencia
    """
    if not _require_login():
        return jsonify({"error": "Unauthorized"}), 401

    dept = (request.args.get("dept_name") or "").strip()
    muni = (request.args.get("muni_name") or "").strip()
    part = (request.args.get("part_name") or "").strip()
    if not (dept and muni and part):
        return jsonify({"error": "Missing parameters"}), 400

    dsn = current_app.config["DATABASE_URL"]
    with get_connection(dsn) as conn, conn.cursor() as cur:
        # 1) mesas in the selected municipality
        cur.execute("""
            SELECT mesa
            FROM ubis
            WHERE dept_name = %s AND muni_name = %s
        """, (dept, muni))
        mesas = [r["mesa"] for r in cur.fetchall()]
        if not mesas:
            return jsonify({
                "dept_name": dept, "muni_name": muni, "part_name": part,
                "results": {k: _zero_metrics() for k in (BALLOT_KEYS + ["TEAM"])}
            })

        # 2) partido_id
        cur.execute("SELECT partido_id FROM partido WHERE partido_name = %s", (part,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": f"Partido not found: {part}"}), 404
        partido_id = row["partido_id"]

        # 3) Aggregate metadata (padron, validos, emitidos) by tipo
        cur.execute("""
            SELECT tipo,
                   COALESCE(SUM(padron), 0)   AS padron,
                   COALESCE(SUM(validos), 0)  AS validos,
                   COALESCE(SUM(emitidos), 0) AS emitidos
            FROM metadata
            WHERE mesa = ANY(%s)
            GROUP BY tipo
        """, (mesas,))
        meta = {r["tipo"]: r for r in cur.fetchall()}

        # 4) Aggregate party votes by tipo
        cur.execute("""
            SELECT tipo, COALESCE(SUM(voto), 0) AS votos
            FROM voto
            WHERE mesa = ANY(%s) AND partido_id = %s
            GROUP BY tipo
        """, (mesas, partido_id))
        votes = {r["tipo"]: r["votos"] for r in cur.fetchall()}

    # 5) Build response per ballot
    results = {}
    team_acc = {"padron": 0, "validos": 0, "emitidos": 0, "recibidos": 0}

    for key, tipo in BALLOT_MAP.items():
        m = meta.get(tipo, {"padron": 0, "validos": 0, "emitidos": 0})
        padron = int(m.get("padron") or 0)
        validos = int(m.get("validos") or 0)
        emitidos = int(m.get("emitidos") or 0)
        recibidos = int(votes.get(tipo) or 0)

        results[key] = _format_metrics(padron, validos, emitidos, recibidos)

        # team accumulators
        team_acc["padron"] += padron
        team_acc["validos"] += validos
        team_acc["emitidos"] += emitidos
        team_acc["recibidos"] += recibidos

    # 6) TEAM = cross-ballot totals
    results["TEAM"] = _format_metrics(
        team_acc["padron"], team_acc["validos"], team_acc["emitidos"], team_acc["recibidos"]
    )

    return jsonify({
        "dept_name": dept,
        "muni_name": muni,
        "part_name": part,
        "results": results
    })


def _zero_metrics():
    return {
        "empadronados": 0,
        "votos_totales": 0,
        "votos_recibidos": 0,
        "participacion": 0.0,
        "eficiencia": 0.0,
    }


def _format_metrics(padron: int, validos: int, emitidos: int, recibidos: int):
    # PARTICIPACIÓN = emitidos / padron * 100
    participacion = (emitidos / padron * 100.0) if padron > 0 else 0.0
    # EFICIENCIA = validos / emitidos * 100
    eficiencia = (validos / emitidos * 100.0) if emitidos > 0 else 0.0

    return {
        "empadronados": padron,          # total registered
        "votos_totales": validos,        # total valid votes
        "votos_recibidos": recibidos,    # votes received by selected party
        "participacion": participacion,  # % turnout
        "eficiencia": eficiencia,        # % valid of emitted
    }
