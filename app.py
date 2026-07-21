from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from db import get_connection
import os

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# --- Rotas principais ---

# @app.route("/")
# def serve_frontend():
#     return send_from_directory(app.static_folder, "index.html")

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/commands", methods=["GET"])
def list_commands():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM commands ORDER BY id DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@app.route("/commands", methods=["POST"])
def add_command():
    data = request.json
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    category_name = data.get("category_name")
    

    # Verifica se a categoria já existe
    cur.execute("SELECT id FROM categories WHERE name = %s;", (category_name,))
    existing = cur.fetchone()
    category_id = 0

    if existing:
        category_id = existing["id"]
    else:
        # Só cria se realmente não existir
        cur.execute(
            "INSERT INTO categories (name) VALUES (%s) RETURNING id;",
            (category_name,)
        )
        category_id = cur.fetchone()["id"]

    cur.execute(
        """
        INSERT INTO commands (title, command_text, description, tags, category_id)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            data.get("title"),
            data.get("command_text"),
            data.get("description"),
            data.get("tags"),
            category_id,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok", "message": "Comando salvo com sucesso!"})

@app.route("/categories", methods=["GET"])
def get_categories():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@app.route("/commands/<int:category_id>", methods=["GET"])
def get_commands_by_category(category_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM commands WHERE category_id = %s ORDER BY id DESC", (category_id,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)

@app.route("/categories", methods=["POST"])
def create_category():
    data = request.json
    name = data.get("name")

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "INSERT INTO categories (name) " \
        "VALUES (%s) " \
        "RETURNING id, name;",
        (name,)
    )
    new_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok", "id": new_id})

@app.route("/commands/<int:cmd_id>", methods=["PUT"])
def update_command(cmd_id):
    data = request.json
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Atualiza os dados
    cur.execute("""
        UPDATE commands
        SET title = %s,
            command_text = %s,
            description = %s,
            category_id = %s,
            tags = %s
        WHERE id = %s
    """, (
        data.get("title"),
        data.get("command_text"),
        data.get("description"),
        data.get("category_id"),
        data.get("tags"),
        cmd_id
    ))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "ok", "message": "Comando atualizado com sucesso!"})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
