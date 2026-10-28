import os
import socket

from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

REGNO = os.getenv("REGNO", "202401100200321")
APP_VERSION = os.getenv("APP_VERSION", "dev")


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "festpass"),
        user=os.getenv("DB_USER", "festpass"),
        password=os.getenv("DB_PASSWORD", "FestPass-Change-Me-2026"),
        port=os.getenv("DB_PORT", "5432"),
        connect_timeout=3,
    )


def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL
            )
        """)

        conn.commit()
        cur.close()
        conn.close()

    except Exception as error:
        print("Database initialization failed:", error)


@app.route("/api/health", methods=["GET"])
def health():
    database_status = False

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()

        database_status = True

        cur.close()
        conn.close()

    except Exception as error:
        print("Database connection failed:", error)

    return jsonify({
        "status": "ok",
        "regno": REGNO,
        "version": APP_VERSION,
        "container": socket.gethostname(),
        "database": database_status,
    })


@app.route("/api/registrations", methods=["GET"])
def get_registrations():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            "SELECT id, name, email FROM registrations ORDER BY id"
        )

        registrations = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify(registrations)

    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/registrations", methods=["POST"])
def create_registration():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return jsonify({
            "error": "Name and email are required"
        }), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO registrations (name, email)
            VALUES (%s, %s)
            RETURNING id
            """,
            (name, email),
        )

        registration_id = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "id": registration_id,
            "name": name,
            "email": email,
        }), 201

    except Exception as error:
        return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)