import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
def get_connection():
    """Establece la conexión con PostgreSQL estrictamente desde el .env."""
    
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    
    # Previene el inicio del servidor si faltan datos críticos
    if not all([db_name, db_user, db_pass]):
        raise ValueError("CRÍTICO: Faltan credenciales de base de datos en el archivo .env")

    return psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_pass,
        host=os.getenv("DB_HOST", "localhost"), # Host y Port sí pueden tener fallbacks locales
        port=os.getenv("DB_PORT", "5432")
    )
def init_db():
    """Inicializa el esquema y aplica migraciones."""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Tabla de países (con coordenadas incluidas)
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

     # Tabla de favoritos (Fase 3)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS favoritos (
                id VARCHAR(3) PRIMARY KEY REFERENCES paises(id) ON DELETE CASCADE,
                nombre VARCHAR(100)
            );
        """)
        
        # Fallback automático: Si la tabla ya existía sin la columna 'nombre', la añade
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name='favoritos' AND column_name='nombre') THEN 
                    ALTER TABLE favoritos ADD COLUMN nombre VARCHAR(100); 
                END IF; 
            END $$;
        """)
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"!!! Error de inicialización DB: {e}")