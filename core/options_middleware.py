import os
from flask import Flask, Response, request, jsonify

def handle_options_requests(app: Flask, allowed_origins):
    """
    Middleware para manejar solicitudes OPTIONS directamente
    """
    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            origin = request.headers.get('Origin')
            # Verificar si el origen está permitido
            if origin and (origin in allowed_origins):
                response = Response('')
                response.headers.add('Access-Control-Allow-Origin', origin)
                response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,PATCH,DELETE,OPTIONS')
                response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin')
                response.headers.add('Access-Control-Allow-Credentials', 'true')
                response.headers.add('Access-Control-Max-Age', '86400')
                return response
