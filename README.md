# 🌐 Datamundi | First Class Global

Datamundi es una aplicación web de página única (SPA) que funciona como un agregador demográfico y turístico a nivel global. Empleando una arquitectura modularizada bajo el patrón **Backend-For-Frontend (BFF)**, la plataforma procesa, traduce y centraliza datos de múltiples fuentes externas para servirlos dinámicamente al cliente web.

## 🚀 Arquitectura y Características Principales

* **Buscador Inteligente y Caché Local:** Búsqueda localizada de países utilizando la API de REST Countries como llenado automático, manteniéndose en caché dentro de la base de datos PostgreSQL para reducir tiempos de respuesta en consultas futuras.
* **Módulo de Turismo Inteligente:** Integración como proxy seguro hacia la API de Geoapify para localizar atracciones cercanas (radio de 15km) con un diccionario de traducción expansivo manejado de forma nativa por el backend.
* **Gestión de Bitácora (Favoritos):** Interfaz rápida para archivar destinos mediante llamadas asíncronas de la Fetch API, respaldadas por un modelo relacional seguro en PostgreSQL.
* **Arquitectura Backend MVC-like:** Implementación del patrón *Application Factory* en Flask y uso de *Blueprints*. Existe una división clara de responsabilidades entre el enrutamiento (`routes.py`), la lógica de conexión (`database.py`) y la sanitización de datos (`utils.py`).
* **API RESTful Segura:** El servidor expone una API estructurada con políticas CORS configuradas globalmente, permitiendo el consumo externo de los recursos.
* **Sistema de Diseño Consistente:** Uso de **Tailwind CSS local** compilado vía Node.js (`tailwind.config.js`). Esto previene inyecciones forzosas en línea, establece semántica visual (`brand: '#27dae0'`) y soporta nativamente el Modo Claro/Oscuro.

## 🛠️ Stack Tecnológico

**Backend:**
* Python 3.10+ / Flask 3.x
* PostgreSQL (psycopg2 - sentencias preparadas nativas)
* Flask-CORS
* Requests (Consumo de APIs de terceros)

**Frontend:**
* Vanilla JavaScript (DOM Fetch API)
* Tailwind CSS CLI v3.4.x (Compilador Node.js)
* HTML5 / CSS3

## 📂 Estructura del Directorio

```text
/datamundi
├── backend/                 # Capa de abstracción del servidor y modelo de datos
│   ├── __init__.py          # Flask App Factory (create_app) + Configuración CORS
│   ├── database.py          # Conexión principal PSQL y Schema builder automatizado
│   ├── routes.py            # Endpoints (Blueprint) RESTFul
│   └── utils.py             # Funciones de sanitización y diccionarios estáticos
├── node_modules/            # Dependencias Javascript asociadas a compiladores locales
├── src/                     # Estilos de origen Tailwind (input.css)
├── static/                  # Archivos entregables pre-compilados
│   ├── css/                 # Hoja de estilos final minificada por Tailwind (style.css)
│   └── js/                  # Interacciones del DOM reactivas (javita.js)
├── templates/               # Motor de plantillas UI
│   └── index.html           # Vista principal
├── .env                     # Tokens y claves API
├── run.py                   # Script de desarrollo y ejecución directa (WSGI wrapper)
├── tailwind.config.js       # Configuraciones y paletas visuales (theme extensibility)
├── package.json             # NPM dependencies (Tailwind)
└── requirements.txt         # Entorno base Python
```

## 🗺️ Guía para Colaboradores (Despliegue Local)

Para ejecutar este proyecto en tu entorno de desarrollo local, sigue cuidadosamente estos pasos. El proyecto requiere la ejecución paralela del servidor Python y el compilador de diseño Node.js.

### 1. Requisitos Previos
* **Python 3.10+**
* **Node.js (LTS)**
* **PostgreSQL** instalado y operando en el puerto local `5432`.

### 2. Configuración de Base de Datos y Entorno
En tu gestor local de PostgreSQL (Ej. pgAdmin), crea una base de datos vacía llamada `datamundi`. El servidor construirá las tablas y relaciones automáticamente en el primer arranque.

En la raíz del repositorio, crea un archivo `.env` configurando los accesos:

```env
# Configuración Servidor
PORT=8000
DEBUG=True

# Configuración Base de Datos
DB_USER=tu_usuario_postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=datamundi

# Tokens de Servicios Externos
GEOAPIFY_KEY=tu_api_key
```

### 3. Instalación de Dependencias
Abre la terminal en la raíz del proyecto para inicializar ambos ecosistemas:

**Entorno Backend (Python):**
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

**Entorno Frontend (Node.js):**
```bash
npm install 
```

### 4. Ejecución del Entorno de Desarrollo
Necesitarás dos instancias de terminal corriendo simultáneamente:

**Terminal 1 (Vigía del motor Tailwind):**
```bash
npx tailwindcss -i ./src/input.css -o ./static/css/style.css --watch
```

**Terminal 2 (Servidor API de Flask):**
```bash
python run.py
```

Accede a la interfaz interactiva navegando a `http://localhost:8000/app`. 
Para auditar el estado del servidor web y las políticas CORS, navega a la ruta raíz `http://localhost:8000/`.

---

## 📝 Estado del Proyecto y Deuda Técnica (Refactorizaciones Pendientes)

A continuación se detalla la deuda técnica identificada y priorizada para futuros ciclos de desarrollo:

### 🔴 Impacto Alto: Inyección y Administración Raw de SQL
Actualmente las operaciones CRUD (`routes.py`) y la creación de esquemas (`database.py`) se efectúan ejecutando sentencias SQL en texto plano y sentencias condicionadas de PostgreSQL.
* **Acción sugerida:** Integrar el ORM `SQLAlchemy` para otorgar validación de tipos nativos, facilitar la gestión de migraciones y reducir drásticamente las líneas de código.

### 🟡 Impacto Medio: Delegación de Renderizado al Frontend mediante Template Literals
Fragmentos extensos del sitio (`javita.js`) contienen ciclos lógicos que mezclan cadenas de HTML puro con Javascript asíncrono.
* **Acción sugerida:** Transferir el renderizado HTML al motor Jinja de Flask y utilizar HTMX para transferencia de fragmentos, o evaluar transicionar el frontend hacia un entorno basado en componentes (React/Vue + Vite).

### 🟡 Impacto Medio: Manejo Global de Errores Amortiguado
En los endpoints principales, los bloques Try/Catch genéricos interceptan errores del servidor devolviendo mensajes por defecto ("Error interno"), silenciando la salida de depuración estándar de Python.
* **Acción sugerida:** Implementar el manejador global `@api_bp.errorhandler(Exception)` apoyado por el módulo `logging` de Python para garantizar trazabilidad.

### 🟢 Impacto Bajo: Inconsistencias y Vestigios Visuales
Tras la transición a Tailwind CLI, permanecen etiquetas huérfanas en el motor de plantillas y pequeños vestigios de estilos en línea (Ej. `style=""`).
* **Acción sugerida:** Ejecutar un análisis de limpieza formal (Linting HTML) sobre `index.html` para unificar definitivamente todo el control visual hacia las nuevas utilidades Tailwind (`bg-brand`, `text-brand`).