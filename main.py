from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import time

app = FastAPI(title="API de Países - Fase 2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    print(f"DEBUG: {request.method} {request.url.path} - Status: {response.status_code} - {process_time:.2f}ms")
    return response

@app.get("/")
async def root():
    return {"mensaje": "API de Países en funcionamiento"}

# 5. LÓGICA DEL PUENTE Y MAPEO DE DATOS
@app.get("/pais/{nombre}")
async def get_pais(nombre: str):
    # Usamos la URL que pediste, pero agregamos 'cca3' (ID) y 'flags' (Imagen) para cumplir tu rúbrica
    external_url = "https://restcountries.com/v3.1/all?fields=name,capital,currencies,cca3,flags"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(external_url)
            todos_los_paises = response.json()
            print(todos_los_paises)
            
            # 1. Filtramos la lista inmensa para encontrar solo el país que pidió el usuario
            pais_encontrado = None
            for pais in todos_los_paises:
                # Comparamos en minúsculas para evitar errores si el usuario escribe "MeXiCo"
                nombre_comun = pais.get("name", {}).get("common", "").lower()
                if nombre.lower() in nombre_comun:
                    pais_encontrado = pais
                    break
            
            # Si terminamos de revisar la lista y no lo encontramos, lanzamos error 404
            if not pais_encontrado:
                raise HTTPException(
                    status_code=404,
                    detail=f"El país '{nombre}' no existe en la base de datos."
                )
            
            # Extraemos la primera capital y la primera moneda de forma segura
            capitales = pais_encontrado.get("capital", ["Desconocida"])
            capital_str = capitales[0] if capitales else "Desconocida"
            
            monedas = list(pais_encontrado.get("currencies", {}).keys())
            moneda_str = monedas[0] if monedas else "Desconocida"

            # 2. Data Cleaning: Entregamos el JSON limpio con los 4 campos exactos del PDF
            pais_limpio = {
                "id": pais_encontrado.get("cca3", "N/A"),                                # 
                "nombre": pais_encontrado.get("name", {}).get("common", "Desconocido"),  # [cite: 19]
                "categoria": f"Capital: {capital_str} | Moneda: {moneda_str}",           # [cite: 20]
                "recurso_visual": pais_encontrado.get("flags", {}).get("png", "")        # 
            }
            
            return pais_limpio
            
        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="El servicio de Rest Countries falló."
            )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)