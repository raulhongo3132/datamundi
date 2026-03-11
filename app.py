from flask import Flask, jsonify, request
import psycopg2, requests
from psycopg2 import sql
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_NAME = "datamundi"
DB_USER = "mapamundi"
DB_PASSWORD = "mundi123"
DB_HOST = "localhost"

# --- CREAR BASE DE DATOS SI NO EXISTE ---
def create_database():
    conn = psycopg2.connect(
        dbname="postgres",  # base administrativa
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cur.fetchone()

    if not exists:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(DB_NAME)
        ))
        print("Base de datos creada.")

    cur.close()
    conn.close()


# --- CREAR TABLAS SI NO EXISTEN ---
def create_tables():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS paises (
            id VARCHAR(3) PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            capital VARCHAR(100),
            moneda VARCHAR(10),
            recurso_visual TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS favoritos (
            id VARCHAR(3) PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Tabla verificada/creada.")


# --- CONEXIÓN NORMAL A LA BD ---
def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )


# --- RUTAS ---
@app.route("/")
def home():
    return jsonify({"mensaje": "API con Flask y PostgreSQL funcionando"})


@app.route("/pais", methods=["POST"])
def insertar_pais():
    data = request.json

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO paises (id, nombre, capital, moneda, recurso_visual)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data["id"],
            data["nombre"],
            data["capital"],
            data["moneda"],
            data["recurso_visual"]
        ))

        conn.commit()
        return jsonify({"mensaje": "País insertado correctamente"}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cur.close()
        conn.close()


@app.route("/agregarFav/<nombre>", methods=["POST"])
def agregar_favorito(nombre):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # 1️⃣ Verificar que exista en paises
        cur.execute("""
            SELECT id, nombre
            FROM paises
            WHERE LOWER(nombre) LIKE %s
        """, (f"%{nombre.lower()}%",))

        pais = cur.fetchone()

        if not pais:
            return jsonify({"error": "El país no existe en la base de datos"}), 404

        # 2️⃣ Insertar en favoritos
        cur.execute("""
            INSERT INTO favoritos (id, nombre)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (pais[0], pais[1]))

        conn.commit()

        return jsonify({
            "mensaje": "País agregado a favoritos",
            "id": pais[0],
            "nombre": pais[1]
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()


@app.route("/pais/<nombre>", methods=["GET"])
def obtener_pais(nombre):
    conn = get_connection()
    cur = conn.cursor()
    is_favorite = False # Inicializamos la bandera

    # 1️⃣ Buscar en base de datos
    cur.execute("""
        SELECT id, nombre, capital, moneda, recurso_visual
        FROM paises
        WHERE LOWER(nombre) = %s
    """, (nombre.lower(),))

    pais = cur.fetchone()

    if pais:
        # Si el país se encontró en la base de datos, verificamos si es favorito
        cur.execute("""
            SELECT 1 FROM favoritos WHERE id = %s
        """, (pais[0],))
        if cur.fetchone():
            is_favorite = True

        cur.close()
        conn.close()
        return jsonify({
            "id": pais[0],
            "nombre": pais[1],
            "capital": pais[2],
            "moneda": pais[3],
            "recurso_visual": pais[4],
            "fuente": "base de datos",
            "is_favorite": is_favorite # ¡Agregamos esta nueva propiedad!
        })

    # 2️⃣ Si no existe → consultar API externa
    try:
        response = requests.get(
            f"https://restcountries.com/v3.1/name/{nombre}?fields=name,capital,currencies,cca3,flags"
        )

        if response.status_code != 200:
            cur.close()
            conn.close()
            return jsonify({"error": "País no encontrado"}), 404

        data = response.json()[0]

        # Limpieza de datos
        capital = data.get("capital", ["Desconocida"])[0]
        moneda = list(data.get("currencies", {}).keys())[0] if data.get("currencies") else "N/A"
        nombre_limpio = data.get("name", {}).get("common", "Desconocido")
        codigo = data.get("cca3", "N/A")
        bandera = data.get("flags", {}).get("png", "")

        # 3️⃣ Guardar en PostgreSQL
        cur.execute("""
            INSERT INTO paises (id, nombre, capital, moneda, recurso_visual)
            VALUES (%s, %s, %s, %s, %s)
        """, (codigo, nombre_limpio, capital, moneda, bandera))

        conn.commit()

        # Después de insertar, verificamos si es favorito (en este caso, no lo es aún)
        is_favorite = False # Por defecto, un país recién traído de la API externa no es favorito

        cur.close()
        conn.close()

        return jsonify({
            "id": codigo,
            "nombre": nombre_limpio,
            "capital": capital,
            "moneda": moneda,
            "recurso_visual": bandera,
            "fuente": "api externa",
            "is_favorite": is_favorite # ¡Agregamos esta nueva propiedad!
        })

    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ... (tu código anterior, justo después de @app.route("/agregarFav/<nombre>", methods=["POST"])) ...

@app.route("/removerFav/<nombre>", methods=["DELETE"])
def remover_favorito(nombre):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # 1️⃣ Verificar que exista en paises para obtener el ID
        cur.execute("""
            SELECT id
            FROM paises
            WHERE LOWER(nombre) LIKE %s
        """, (f"%{nombre.lower()}%",))

        pais_id_tuple = cur.fetchone()

        if not pais_id_tuple:
            return jsonify({"error": "El país no existe en la base de datos de países"}), 404

        pais_id = pais_id_tuple[0]

        # 2️⃣ Eliminar de favoritos
        cur.execute("""
            DELETE FROM favoritos
            WHERE id = %s;
        """, (pais_id,))

        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({"mensaje": "El país no estaba en favoritos para remover"}), 200 # O 404 si prefieres

        conn.commit()
        return jsonify({
            "mensaje": "País removido de favoritos",
            "id": pais_id
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_database()
    create_tables()
    app.run(debug=True, port=8000)
