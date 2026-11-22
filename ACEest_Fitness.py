import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, jsonify, render_template, request


PROGRAMS = {
    "Fat Loss": {
        "workout": "Full-body strength training and cardio, 5 days per week.",
        "diet": "Balanced meals with a moderate calorie deficit.",
    },
    "Muscle Gain": {
        "workout": "Progressive strength training, 4-5 days per week.",
        "diet": "Protein-rich meals with a moderate calorie surplus.",
    },
    "Beginner": {
        "workout": "Full-body strength and mobility, 3 days per week.",
        "diet": "Balanced meals matched to activity level.",
    },
}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "ACEEST_DATABASE",
            str(Path(app.instance_path) / "aceest.sqlite"),
        )
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    init_db(app)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/programs")
    def list_programs():
        return jsonify(PROGRAMS)

    @app.get("/api/clients")
    def list_clients():
        with get_db(app) as db:
            clients = db.execute(
                "SELECT id, name, age, program FROM clients ORDER BY name"
            ).fetchall()
        return jsonify([dict(client) for client in clients])

    @app.post("/api/clients")
    def create_client():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Request body must be a JSON object."), 400

        name = payload.get("name")
        if not isinstance(name, str) or not name.strip():
            return jsonify(error="A non-empty name is required."), 400
        name = name.strip()

        age = payload.get("age")
        if age is not None and (
            isinstance(age, bool) or not isinstance(age, int) or age < 1 or age > 120
        ):
            return jsonify(error="Age must be a whole number between 1 and 120."), 400

        program = payload.get("program")
        if program is not None and (
            not isinstance(program, str) or program not in PROGRAMS
        ):
            return jsonify(error="Program must be one of the listed programs."), 400

        try:
            with get_db(app) as db:
                cursor = db.execute(
                    "INSERT INTO clients (name, age, program) VALUES (?, ?, ?)",
                    (name, age, program),
                )
                client = db.execute(
                    "SELECT id, name, age, program FROM clients WHERE id = ?",
                    (cursor.lastrowid,),
                ).fetchone()
        except sqlite3.IntegrityError:
            return jsonify(error="A client with that name already exists."), 409

        return jsonify(dict(client)), 201

    return app


@contextmanager
def get_db(app):
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


def init_db(app):
    with get_db(app) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                age INTEGER,
                program TEXT
            )
            """
        )


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
