import unicodedata
import psycopg2
import requests
import os
from dotenv import load_dotenv

from flask import Flask, jsonify, render_template, request





app = Flask(__name__)

load_dotenv()

# --- CONFIGURACIÓN DE BASE DE DATOS ---
#DB_NAME = "datamundi_db"
#DB_USER = "postgres"
#DB_PASSWORD = "admin123"
#DB_HOST = "localhost"
#DB_PORT = "5432"


# --- DICCIONARIOS DE TRADUCCIÓN ---
TRADUCCION_REGIONES = {
    "Americas": "América",
    "Europe": "Europa",
    "Africa": "África",
    "Oceania": "Oceanía",
    "Asia": "Asia",
    "Antarctic": "Antártida",
}

TRADUCCION_IDIOMAS = {
    "Spanish": "Español",
    "English": "Inglés",
    "French": "Francés",
    "Portuguese": "Portugués",
    "German": "Alemán",
    "Italian": "Italiano",
    "Chinese": "Chino",
    "Japanese": "Japonés",
    "Arabic": "Árabe",
    "Russian": "Ruso",
    "Dutch": "Neerlandés",
    "Hindi": "Hindi",
    "Korean": "Coreano",
    "Greek": "Griego",
    "Turkish": "Turco",
    "Vietnamese": "Vietnamita",
    "Thai": "Tailandés",
    "Māori": "Maorí",
    "Danish": "Danés",
    "Greenlandic": "Groenlandés",
    "Mandarin": "Mandarín",
}

TRADUCCION_CAPITALES = {
    "Mexico City": "Ciudad de México",
    "Guatemala City": "Ciudad de Guatemala",
    "Panama City": "Ciudad de Panamá",
    "Brasília": "Brasilia",
    "Washington, D.C.": "Washington D.C.",
    "Beijing": "Pekín",
    "London": "Londres",
    "Nuuk": "Nuuk (Godthåb)",
}

# Sinónimos para normalizar búsquedas que la API no procesa bien en español
SINONIMOS_ESPANOL = {
    "eeuu": "estados unidos",
    "usa": "estados unidos",
    "holanda": "países bajos",
    "inglaterra": "reino unido",
    "corea": "corea del sur",
    "groelandia": "groenlandia",
    "china": "china",
}


def normalizar_texto(texto):
    """Elimina acentos y convierte a minúsculas para comparaciones precisas."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto.lower().strip()


def get_connection():
    """Establece la conexión con PostgreSQL leyendo las variables de entorno."""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "datamundi_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "admin123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )


def init_db():
    """Inicializa el esquema y aplica migraciones de columnas faltantes."""
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS paises (
                id VARCHAR(3) PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                nombre_normalizado VARCHAR(100),
                capital VARCHAR(100),
                moneda VARCHAR(100),
                recurso_visual TEXT,
                poblacion VARCHAR(50),
                region VARCHAR(50),
                area VARCHAR(50),
                mapa TEXT,
                idiomas TEXT,
                huso_horario TEXT,
                latitud VARCHAR(50),
                longitud VARCHAR(50)
            );
        """)

        columnas = [
            ("idiomas", "TEXT"),
            ("huso_horario", "TEXT"),
            ("nombre_normalizado", "VARCHAR(100)"),
            ("poblacion", "VARCHAR(50)"),
            ("region", "VARCHAR(50)"),
            ("area", "VARCHAR(50)"),
            ("mapa", "TEXT"),
            ("latitud", "VARCHAR(50)"),
            ("longitud", "VARCHAR(50)"),
        ]

        for col, tipo in columnas:
            cur.execute(f"""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                    WHERE table_name='paises' AND column_name='{col}') THEN 
                        ALTER TABLE paises ADD COLUMN {col} {tipo}; 
                    END IF; 
                END $$;
            """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS favoritos (
                id VARCHAR(3) PRIMARY KEY REFERENCES paises(id) ON DELETE CASCADE
            );
        """)

        cur.execute("""
            DO $$ 
            BEGIN 
                IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name='favoritos' AND column_name='nombre') THEN 
                    ALTER TABLE favoritos DROP COLUMN nombre; 
                END IF; 
            END $$;
        """)

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"!!! Error de inicialización: {e}")


# --- RUTAS ---


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/pais/<nombre>", methods=["GET"])
def obtener_pais(nombre):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        nombre_input = nombre.strip()
        nombre_clean = normalizar_texto(nombre_input)

        # 0. Aplicar sinónimo si existe
        termino_busqueda = SINONIMOS_ESPANOL.get(nombre_clean, nombre_clean)

        # 1. Búsqueda local inteligente
        cur.execute(
            """
            SELECT id, nombre, capital, moneda, recurso_visual, poblacion, region, area, mapa, idiomas, huso_horario, latitud, longitud
            FROM paises WHERE nombre_normalizado = %s OR LOWER(nombre) = %s
        """,
            (normalizar_texto(termino_busqueda), termino_busqueda.lower()),
        )

        p = cur.fetchone()

        # Validamos si el registro local es válido (idiomas ya traducidos)
        if (
            p
            and p[9]
            and all(idi not in p[9] for idi in ["Spanish", "English", "Danish"])
        ):
            return jsonify(
                {
                    "id": p[0],
                    "nombre": p[1],
                    "capital": p[2],
                    "moneda": p[3],
                    "bandera": p[4],
                    "poblacion": p[5],
                    "region": p[6],
                    "area": p[7],
                    "mapa": p[8],
                    "idiomas": p[9],
                    "zonaHoraria": p[10],
                    "latitud": p[11] if len(p) > 11 else "",
                    "longitud": p[12] if len(p) > 12 else "",
                }
            )

        # 2. Sincronización con API externa
        # Intentamos endpoint de traducción primero
        url = f"https://restcountries.com/v3.1/translation/{termino_busqueda}"
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            url = f"https://restcountries.com/v3.1/name/{termino_busqueda}"
            res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return jsonify(
                {"error": f"No se encontró el destino '{nombre_input}'"}
            ), 404

        data_list = res.json()

        # Buscamos la mejor coincidencia en la lista
        target_data = None
        for item in data_list:
            nombre_es = (
                item.get("translations", {}).get("spa", {}).get("common", "").lower()
            )
            if normalizar_texto(nombre_es) == normalizar_texto(
                termino_busqueda
            ) or normalizar_texto(
                item.get("name", {}).get("common")
            ) == normalizar_texto(termino_busqueda):
                target_data = item
                break

        if not target_data:
            target_data = data_list[0]

        # Extraer nombre común en español (Mejor formateado para el Linter)
        nombre_final = target_data.get("translations", {}).get("spa", {}).get("common")
        if not nombre_final:
            nombre_final = target_data.get("name", {}).get("common", "Desconocido")

        # Validación estricta de idioma
        if (normalizar_texto(nombre_input) not in SINONIMOS_ESPANOL) and (normalizar_texto(nombre_input) != normalizar_texto(nombre_final)):
            return jsonify({
                "error": f"Búsqueda rechazada. Por favor use el nombre en español (ej. '{nombre_final}')"
            }), 400

        # Procesar datos traducidos
        region_raw = target_data.get("region", "N/A")
        region_spa = TRADUCCION_REGIONES.get(region_raw, region_raw)

        capital_raw = target_data.get("capital", ["N/A"])[0]
        capital_spa = TRADUCCION_CAPITALES.get(capital_raw, capital_raw)

        coordenadas = target_data.get("capitalInfo", {}).get("latlng", ["", ""])
        lat = str(coordenadas[0]) if len(coordenadas) > 0 else ""
        lon = str(coordenadas[1]) if len(coordenadas) > 1 else ""

        idiomas_list = list(target_data.get("languages", {}).values())
        idiomas_spa = ", ".join([TRADUCCION_IDIOMAS.get(i, i) for i in idiomas_list])
        
        # Corrección del ternario de monedas que causaba error en el diccionario
        monedas_dic = target_data.get("currencies")
        moneda_str = ", ".join(monedas_dic.keys()) if monedas_dic else "N/A"

        pais_data = {
            "id": target_data.get("cca3", "UNK").upper(),
            "nombre": nombre_final,
            "nombre_normalizado": normalizar_texto(nombre_final),
            "capital": capital_spa,
            "moneda": moneda_str,
            "bandera": target_data.get("flags", {}).get("png"),
            "poblacion": f"{target_data.get('population', 0):,}",
            "idiomas": idiomas_spa if idiomas_spa else "N/A",
            "area": f"{target_data.get('area', 0):,} km²",
            "region": region_spa,
            "zonaHoraria": ", ".join(target_data.get("timezones", ["N/A"])),
            "mapa": target_data.get("maps", {}).get("googleMaps"),
            "latitud": lat,
            "longitud": lon,
        }

        # Guardar / Actualizar
        cur.execute(
            """
            INSERT INTO paises (id, nombre, nombre_normalizado, capital, moneda, recurso_visual, poblacion, region, area, mapa, idiomas, huso_horario, latitud, longitud)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE 
            SET nombre = EXCLUDED.nombre, nombre_normalizado = EXCLUDED.nombre_normalizado, capital = EXCLUDED.capital, 
                region = EXCLUDED.region, idiomas = EXCLUDED.idiomas, huso_horario = EXCLUDED.huso_horario, latitud = EXCLUDED.latitud, longitud = EXCLUDED.longitud;
        """,
            (
                pais_data["id"],
                pais_data["nombre"],
                pais_data["nombre_normalizado"],
                pais_data["capital"],
                pais_data["moneda"],
                pais_data["bandera"],
                pais_data["poblacion"],
                pais_data["region"],
                pais_data["area"],
                pais_data["mapa"],
                pais_data["idiomas"],
                pais_data["zonaHoraria"],
                pais_data["latitud"],
                pais_data["longitud"],
            ),
        )

        conn.commit()
        return jsonify(pais_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/favoritos", methods=["GET", "POST"])
def gestionar_favoritos():
    conn = get_connection()
    cur = conn.cursor()
    try:
        if request.method == "POST":
            pid = request.json.get("id", "").upper()
            cur.execute(
                "INSERT INTO favoritos (id) VALUES (%s) ON CONFLICT DO NOTHING", (pid,)
            )
            conn.commit()
            return jsonify({"status": "ok"})

        cur.execute(
            "SELECT p.id, p.nombre, p.recurso_visual FROM favoritos f JOIN paises p ON f.id = p.id ORDER BY p.nombre ASC"
        )
        favs = [{"id": r[0], "nombre": r[1], "bandera": r[2]} for r in cur.fetchall()]
        return jsonify(favs)
    finally:
        cur.close()
        conn.close()


@app.route("/api/favoritos/<id>", methods=["DELETE"])
def eliminar_favorito(id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM favoritos WHERE id = %s", (id.upper(),))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "eliminado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/turismo/<lat>/<lon>', methods=['GET'])
def obtener_lugares_turisticos(lat, lon):
    """
    Proxy optimizado hacia Geoapify con ordenamiento de proximidad y limpieza de datos.
    """
    api_key = os.environ.get("GEOAPIFY_KEY")
    if not api_key:
        return jsonify({"error": "Configuración de servidor incompleta"}), 500

    # OPTIMIZACIÓN 1, 2 y 3: Categorías selectas, Bias de proximidad y Lenguaje en Español
    categorias = "tourism.sights,heritage,entertainment.museum"
    
    url = f"https://api.geoapify.com/v2/places?categories={categorias}&filter=circle:{lon},{lat},15000&bias=proximity:{lon},{lat}&limit=8&lang=es&apiKey={api_key}"
    
    try:
        response = requests.get(url, timeout=15) 
        if response.status_code == 429:
            return jsonify({"error": "Límite de consultas alcanzado. Espera un minuto."}), 429
            
        response.raise_for_status()
        data = response.json()
        
        lugares = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            nombre = props.get("name")
            
            # Filtramos estrictamente lugares que no tengan nombre
            if nombre: 
                # OPTIMIZACIÓN 4: Sanitización de datos
                
                # 1. Limpiar categoría (Ej: pasa de "tourism.sights" a "Sights" o usa la proveída)
                cat_raw = props.get("categories", ["Desconocida"])[0]
                cat_limpia = cat_raw.split('.')[-1].replace('_', ' ').capitalize()

                # 2. Manejo seguro de la distancia para evitar el "NULLM"
                distancia_raw = props.get("distance")
                distancia_str = f"{int(distancia_raw)}m" if distancia_raw else "Centro"

                # 3. Mejor extracción de dirección (fallback a la calle o ciudad si 'formatted' falla)
                direccion = props.get("formatted") or props.get("street") or props.get("city") or "Ubicación general"

                lugares.append({
                    "nombre": nombre,
                    "categoria": cat_limpia,
                    "distancia": distancia_str, # Cambiamos de distancia_metros a distancia ya formateada
                    "direccion": direccion
                })
                
        return jsonify({"status": "success", "data": lugares}), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "La búsqueda está tomando mucho tiempo. Intenta de nuevo."}), 504
    except requests.exceptions.RequestException as e:
        print(f"Error consultando Geoapify: {e}")
        return jsonify({"error": "Servicio de turismo temporalmente no disponible"}), 503


# --- INFORMACIÓN DEL EQUIPO ---
@app.route("/Nosotros", methods=["GET"])
def obtener_nosotros():
    equipo = [
        {
            "nombre": "Rebeca Gómez González"
        },
        {
            "nombre": "Karla Rocío Leal Rangel"
        },
        {
            "nombre": "Duncan Ricardo Sansón Pérez"
        },
        {
            "nombre": "Raúl Miguel Valverde Palacios"
        }
    ]

    return jsonify(equipo)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5500)
