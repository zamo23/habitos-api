import os
from flask import Flask, request
from flask_cors import CORS
from flask_migrate import Migrate

from models import db
from routes.habit_routes import habit_bp
from routes.subscription_routes import subscription_bp
from routes.user_routes import user_bp
from routes.group_routes import group_bp
from routes.plan_routes import plan_bp
from routes.payment_routes import payment_bp
from routes.report_controller import report_bp
from routes.coupon_routes import coupon_bp
from routes.notification_routes import notification_bp
from routes.group_habit_routes import group_habit_bp

debug_bp = None


def register_blueprints(app: Flask):
    """Registrar todos los blueprints de la aplicación"""
    blueprints = [
        habit_bp,
        subscription_bp,
        user_bp,
        group_bp,
        plan_bp,
        payment_bp,
        report_bp,
        coupon_bp,
        notification_bp,
        group_habit_bp
    ]
    
    # Registrar blueprint de depuración solo en modo desarrollo
    is_development = os.getenv('FLASK_ENV') == 'development' or app.config.get('DEBUG', False)
    if is_development and debug_bp:
        blueprints.append(debug_bp)
        app.logger.warning("¡Modo depuración activado! El endpoint /api/v1/debug está habilitado.")
    
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

def configure_extensions(app: Flask):
    """Configurar las extensiones de Flask"""
    db.init_app(app)
    Migrate(app, db)

def configure_cors(app: Flask):
    """Configurar CORS para la aplicación según el entorno"""
    # Obtenemos la configuración de CORS directamente desde variable de entorno
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    
    # Procesamos los orígenes permitidos
    # Si es '*', permitimos todos los orígenes
    # Si no, separamos por comas
    origins = cors_origins
    if cors_origins != '*' and ',' in cors_origins:
        origins = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
    
    # Utilizamos Flask-CORS para una gestión completa de CORS
    CORS(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=True,
        automatic_options=True  # Habilitamos automatic_options para que Flask-CORS gestione todo
    )
