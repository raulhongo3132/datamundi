from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # CUMPLIMIENTO FASE 1: CORS permitiendo todos los orígenes (*)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Importar y registrar rutas
    from .routes import api_bp
    app.register_blueprint(api_bp)
    
    # Inicializar Base de Datos dentro del contexto
    from .database import init_db
    with app.app_context():
        init_db()
        
    return app