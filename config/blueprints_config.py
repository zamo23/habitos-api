import os
from flask import Flask
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
        coupon_bp
    ]
    
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

def configure_extensions(app: Flask):
    """Configurar las extensiones de Flask"""
    db.init_app(app)
    Migrate(app, db)

def configure_cors(app: Flask):
    """Configurar CORS para la aplicación según el entorno"""
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'development':
        # Configuración para desarrollo (permite todo)
        CORS(
            app,
            resources={r"/*": {"origins": "*"}},
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers="*",
            expose_headers="*",
            supports_credentials=False,
            send_wildcard=True,
            max_age=86400,  # cache del preflight 24h
        )
    else:
        # Configuración para producción (más restrictiva)
        allowed_origins = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
        allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        allowed_headers = [
            'Content-Type',
            'Authorization',
            'X-Requested-With',
            'Accept',
            'Origin'
        ]
        
        CORS(
            app,
            resources={r"/*": {"origins": allowed_origins}},
            methods=allowed_methods,
            allow_headers=allowed_headers,
            expose_headers=['Content-Range', 'X-Total-Count'],
            supports_credentials=True,
            max_age=86400
        )
