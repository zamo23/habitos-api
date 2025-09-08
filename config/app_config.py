# -*- coding: utf-8 -*-
import os

def configure_app(app):
    # Configuración de entorno
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['FLASK_DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    
    app.config['SECRET_KEY'] = os.getenv('CLERK_SECRET_KEY')
    app.config['CLERK_API_KEY'] = os.getenv('CLERK_SECRET_KEY') 
    db_uri = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?charset=utf8mb4&collation=utf8mb4_general_ci"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }
    
    app.config['CLERK_JWKS_URL'] = os.getenv('CLERK_JWKS_URL')
    app.config['CLERK_JWT_TEMPLATE_ID'] = os.getenv('CLERK_JWT_TEMPLATE_ID')
    app.config['CLERK_API_BASE'] = os.getenv('CLERK_API_BASE')
    app.config['TIMEZONE_DEFAULT'] = os.getenv('TIMEZONE_DEFAULT', 'UTC')
    app.config['DEFAULT_CLOSURE_HOUR'] = int(os.getenv('DEFAULT_CLOSURE_HOUR', '0')) 
    
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
    
    app.config['FRONTEND_URL'] = os.getenv('FRONTEND_URL', 'https://habitos.cvpx.lat')
