import os
import requests
from flask import Blueprint, jsonify, render_template, request
from .database import get_connection
from .utils import normalizar_texto, SINONIMOS_ESPANOL, TRADUCCION_REGIONES, TRADUCCION_CAPITALES, TRADUCCION_IDIOMAS

# Creamos un Blueprint (un paquete de rutas)
api_bp = Blueprint('api', __name__)

# --- CUMPLIMIENTO FASE 1: RUTA RAÍZ JSON (Lo que evaluará el profesor) ---
@api_bp.route("/")
def home_json():
    """Endpoint requerido por el profesor para verificar el estado y CORS."""
    return jsonify({"status": "Servidor Arriba", "message": "Datamundi API operando correctamente."})

# --- LA NUEVA RUTA PARA TU INTERFAZ WEB ---
@api_bp.route("/app")
def web_app():
    return render_template("index.html")

# --- RUTAS DE LA FASE 2, 3 Y 4 ---
@api_bp.route("/api/pais/<nombre>", methods=["GET"])
def obtener_pais(nombre):
    conn = get_connection()
    cur = conn.cursor()
    try:
        nombre_input = nombre.strip()
        nombre_clean = normalizar_texto(nombre_input)
        termino_busqueda = SINONIMOS_ESPANOL.get(nombre_clean, nombre_clean)

        # 1. Búsqueda local inteligente
        cur.execute("SELECT id, nombre, capital, moneda, recurso_visual, poblacion, region, area, mapa, idiomas, huso_horario, latitud, longitud FROM paises WHERE nombre_normalizado = %s OR LOWER(nombre) = %s", (normalizar_texto(termino_busqueda), termino_busqueda.lower()))
        p = cur.fetchone()

        if p and p[9] and all(idi not in p[9] for idi in ["Spanish", "English", "Danish"]):
            return jsonify({"id": p[0], "nombre": p[1], "capital": p[2], "moneda": p[3], "bandera": p[4], "poblacion": p[5], "region": p[6], "area": p[7], "mapa": p[8], "idiomas": p[9], "zonaHoraria": p[10], "latitud": p[11], "longitud": p[12]})

        # 2. Sincronización API externa
        url = f"https://restcountries.com/v3.1/translation/{termino_busqueda}"
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            url = f"https://restcountries.com/v3.1/name/{termino_busqueda}"
            res = requests.get(url, timeout=5)

        if res.status_code != 200: return jsonify({"error": "No se encontró el destino"}), 404
        
        target_data = res.json()[0]

        # Extracción segura (Null-Safe)
        translations = target_data.get("translations") or {}
        spa = translations.get("spa") or {}
        nombre_final = spa.get("common") or target_data.get("name", {}).get("common", "Desconocido")

        region_raw = target_data.get("region") or "N/A"
        capital_list = target_data.get("capital") or ["N/A"]
        
        coordenadas = (target_data.get("capitalInfo") or {}).get("latlng") or []
        lat = str(coordenadas[0]) if len(coordenadas) > 0 else ""
        lon = str(coordenadas[1]) if len(coordenadas) > 1 else ""

        idiomas_list = list((target_data.get("languages") or {}).values())
        currencies_dict = target_data.get("currencies") or {}

        pais_data = {
            "id": target_data.get("cca3", "UNK").upper(),
            "nombre": nombre_final,
            "nombre_normalizado": normalizar_texto(nombre_final),
            "capital": TRADUCCION_CAPITALES.get(capital_list[0], capital_list[0]),
            "moneda": ", ".join(currencies_dict.keys()) if currencies_dict else "N/A",
            "bandera": target_data.get("flags", {}).get("png"),
            "poblacion": f"{target_data.get('population', 0):,}",
            "idiomas": ", ".join([TRADUCCION_IDIOMAS.get(i, i) for i in idiomas_list]) or "N/A",
            "area": f"{target_data.get('area', 0):,} km²",
            "region": TRADUCCION_REGIONES.get(region_raw, region_raw),
            "zonaHoraria": ", ".join(target_data.get("timezones", ["N/A"])),
            "mapa": target_data.get("maps", {}).get("googleMaps"),
            "latitud": lat, "longitud": lon
        }

        # Guardar / Actualizar
        cur.execute("""
            INSERT INTO paises (id, nombre, nombre_normalizado, capital, moneda, recurso_visual, poblacion, region, area, mapa, idiomas, huso_horario, latitud, longitud)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE 
            SET nombre=EXCLUDED.nombre, capital=EXCLUDED.capital, latitud=EXCLUDED.latitud, longitud=EXCLUDED.longitud;
        """, tuple(pais_data.values()))
        conn.commit()
        return jsonify(pais_data)
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

@api_bp.route("/api/favoritos", methods=["GET", "POST"])
def gestionar_favoritos():
    conn = get_connection()
    cur = conn.cursor()
    try:
        if request.method == "POST":
            pid = request.json.get("id", "").upper()
            nombre = request.json.get("nombre", "Desconocido") # Recuperamos el nombre
            
            # =====================================================================
            # NOTA(Bases de Datos):
            # Se almacena la columna 'nombre' por las indicaciones de la Fase 3.
            # Aunque segun los principios de Normalización de Bases de Datos
            # Relacionales(3NF), esta columna es redundante, 
            # ya que el nombre original siempre se puede obtener (y de hecho se 
            # obtiene en la petición GET) mediante un JOIN con la tabla 'paises'.
            # =====================================================================
            
            cur.execute(
                "INSERT INTO favoritos (id, nombre) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre", 
                (pid, nombre)
            )
            conn.commit()
            return jsonify({"status": "ok"})

        # Mantenemos el JOIN en el GET porque es la forma correcta de extraer la bandera y el nombre seguro
        cur.execute("SELECT p.id, p.nombre, p.recurso_visual FROM favoritos f JOIN paises p ON f.id = p.id ORDER BY p.nombre ASC")
        return jsonify([{"id": r[0], "nombre": r[1], "bandera": r[2]} for r in cur.fetchall()])
    finally:
        cur.close()
        conn.close()



@api_bp.route("/api/favoritos/<id>", methods=["DELETE"])
def eliminar_favorito(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM favoritos WHERE id = %s", (id.upper(),))
    conn.commit()
    return jsonify({"status": "eliminado"})

@api_bp.route('/api/turismo/<lat>/<lon>', methods=['GET'])
def obtener_lugares(lat, lon):
    api_key = os.environ.get("GEOAPIFY_KEY")
    url = f"https://api.geoapify.com/v2/places?categories=tourism.sights,heritage,entertainment.museum&filter=circle:{lon},{lat},15000&bias=proximity:{lon},{lat}&limit=8&lang=es&apiKey={api_key}"
    
    # Diccionario de traducción de categorías
    # Diccionario expansivo de traducción de categorías Geoapify
    TRADUCCION_TURISMO = {
        # Tourism & Sights
        "Sights": "Atracción Turística",
        "Attraction": "Atracción",
        "Museum": "Museo",
        "Monument": "Monumento",
        "Artwork": "Obra de Arte",
        "Gallery": "Galería",
        "Information": "Información Turística",
        "Theme_park": "Parque Temático",
        "Zoo": "Zoológico",
        "Aquarium": "Acuario",
        
        # Entertainment
        "Entertainment": "Entretenimiento",
        "Cinema": "Cine",
        "Theatre": "Teatro",
        "Water_park": "Parque Acuático",
        "Amusement_arcade": "Salón de Juegos",
        
        # Administrative & Heritage
        "Heritage": "Patrimonio Histórico",
        "Administrative": "Centro Administrativo",
        "Building": "Edificio Histórico",
        "Castle": "Castillo",
        "Palace": "Palacio",
        "Ruins": "Ruinas",
        "Archaeological_site": "Sitio Arqueológico",
        
        # Man Made & Infrastructure
        "Man_made": "Estructura",
        "Bridge": "Puente",
        "Tower": "Torre",
        "Lighthouse": "Faro",
        
        # Access & Highway
        "Access": "Punto de Acceso",
        "Access_limited": "Acceso Restringido",
        "Highway": "Carretera Histórica",
        "Pedestrian": "Paseo Peatonal",
        
        # Catering
        "Catering": "Gastronomía",
        "Restaurant": "Restaurante",
        "Cafe": "Cafetería",
        "Bar": "Bar",
        "Pub": "Pub Tradicional",
        "Fast_food": "Comida Rápida"
    }
    try:
        res = requests.get(url, timeout=15)
        data = res.json()
        lugares = []
        for f in data.get("features", []):
            p = f.get("properties", {})
            if p.get("name"):
                cat_raw = p.get("categories", [""])[0].split('.')[-1].capitalize()
                cat_traducida = TRADUCCION_TURISMO.get(cat_raw, cat_raw) # Traduce o deja original si no existe
                
                lugares.append({
                    "nombre": p.get("name"),
                    "categoria": cat_traducida,
                    "distancia": f"{int(p.get('distance', 0))}m",
                    "direccion": p.get("formatted", "Sin dirección")
                })
        return jsonify({"status": "success", "data": lugares})
    except Exception:
        return jsonify({"error": "Servicio no disponible"}), 503

# --- NUEVA RUTA INTEGRADA ---
@api_bp.route("/Nosotros", methods=["GET"])
def obtener_nosotros():
    equipo = [
        {"nombre": "Rebeca Gómez González"},
        {"nombre": "Karla Rocío Leal Rangel"},
        {"nombre": "Duncan Ricardo Sansón Pérez"},
        {"nombre": "Raúl Miguel Valverde Palacios"}
    ]
    return jsonify(equipo)