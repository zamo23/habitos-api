# -*- coding: utf-8 -*-
import os
import sys

def configure_encoding(app):
    """Configure character encoding and handling"""
    # Forzar UTF-8 para todo el sistema
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LANG'] = 'en_US.UTF-8'
    os.environ['LC_ALL'] = 'en_US.UTF-8'
    
    if sys.version_info >= (3, 7):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    
    app.config['JSON_AS_ASCII'] = False 
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False 
    
    @app.after_request
    def add_headers(response):
        if 'Content-Type' in response.headers and 'charset' not in response.headers['Content-Type']:
            if response.headers['Content-Type'].startswith('text/'):
                response.headers['Content-Type'] = f"{response.headers['Content-Type']}; charset=utf-8"
            elif response.headers['Content-Type'] == 'application/json':
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
        
        response.headers['X-Content-Type-Options'] = 'nosniff'  
        return response
        
    app.config['JSON_SORT_KEYS'] = False 
    app.jinja_env.encoding = 'utf-8' if hasattr(app, 'jinja_env') else None