from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import uvicorn
import sqlite3
from pydantic import BaseModel
import os

class PaisFavorito(BaseModel):
    id: str
    nombre: str

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect("datamundi.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favoritos (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

app = FastAPI(title="Datamundi API Elite")


templates = Jinja2Templates(directory="templates")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def leer_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- SERVICIO DE DATOS EXTERNOS (REST COUNTRIES) ---
@app.get("/pais/{nombre}")
async def get_pais(nombre: str):
    url = f"https://restcountries.com/v3.1/name/{nombre}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Destino no encontrado en el radar.")
                
            response.raise_for_status()
            data = response.json()
            p = data[0] 
            
            # Formatear datos para el frontend
            poblacion_raw = p.get("population", 0)
            poblacion_fmt = "{:,}".format(poblacion_raw).replace(",", ".")
            
            area_raw = p.get("area", 0)
            area_fmt = "{:,}".format(area_raw).replace(",", ".") + " km²"
            
            idiomas = ", ".join(p.get("languages", {}).values()) if p.get("languages") else "No registrado"
            
            curr_dict = p.get("currencies", {})
            monedas = []
            for code, info in curr_dict.items():
                monedas.append(f"{info.get('name')} ({info.get('symbol', code)})")
            moneda_str = ", ".join(monedas) if monedas else "N/A"

            return {
                "id": p.get("cca3", "N/A"),
                "nombre": p.get("translations", {}).get("spa", {}).get("common", p.get("name", {}).get("common", "Desconocido")),
                "nombreOficial": p.get("translations", {}).get("spa", {}).get("official", "N/A"),
                "capital": p.get("capital", ["N/A"])[0],
                "region": p.get("region", "N/A"),
                "poblacion": poblacion_fmt,
                "idiomas": idiomas,
                "moneda": moneda_str,
                "area": area_fmt,
                "zonaHoraria": p.get("timezones", ["UTC"])[0],
                "bandera": p.get("flags", {}).get("png", ""),
                "mapa": p.get("maps", {}).get("googleMaps", "")
            }
            
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Error de conexión con el servicio global.")

# --- PERSISTENCIA (FAVORITOS) ---
@app.post("/favoritos")
async def guardar_favorito(pais: PaisFavorito):
    try:
        conn = sqlite3.connect("datamundi.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO favoritos (id, nombre) VALUES (?, ?)", (pais.id, pais.nombre))
        conn.commit()
        conn.close()
        return {"mensaje": f"¡{pais.nombre} guardado en su bitácora!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Este destino ya forma parte de su colección.")
    except Exception:
        raise HTTPException(status_code=500, detail="Error en la base de datos local.")

@app.get("/favoritos")
async def obtener_favoritos():
    conn = sqlite3.connect("datamundi.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM favoritos")
    filas = cursor.fetchall()
    conn.close()
    return [dict(fila) for fila in filas]

@app.delete("/favoritos/{id}")
async def eliminar_favorito(id: str):
    conn = sqlite3.connect("datamundi.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favoritos WHERE id = ?", (id,))
    conn.commit()
    eliminados = cursor.rowcount
    conn.close()
    
    if eliminados == 0:
        raise HTTPException(status_code=404, detail="Destino no encontrado.")
    return {"mensaje": "Eliminado de la bitácora correctamente."}

# --- INFORMACIÓN DEL EQUIPO ---
@app.get("/Nosotros")
async def obtener_nosotros():
    equipo = [
        {
            "nombre": "Rebeca Gómez González"
        },
        {
            "nombre": "Karla Rocío Leal Rangel"
        },
        {
            "nombre": "Duncan Ricardo Sansón Pérez ",
            
        },
        {
            "nombre": "Raúl Miguel Valverde Palacios",
            
        },

    ]

    return equipo

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=1800, reload=True)