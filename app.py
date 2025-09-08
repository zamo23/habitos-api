import os
from flask import Flask, request, redirect
from dotenv import load_dotenv
import re

from models import db
from config import configure_application
from core.container import Container
from core.logging_config import configure_logging

load_dotenv()
configure_logging()

def create_app() -> Flask:

    app = Flask(__name__)

    container = Container()
    container.config.from_dict({
        "default_timezone": os.getenv('TIMEZONE_DEFAULT', 'UTC')
    })
    app.container = container
    configure_application(app)
    
    @app.before_request
    def normalize_url():
        path = request.path
        if path.startswith('/api/v1/api/v1/'):
            corrected_path = path.replace('/api/v1/api/v1/', '/api/v1/', 1)
            app.logger.warning(f"URL duplicada detectada: {path} → redirigiendo a {corrected_path}")
            return redirect(corrected_path, code=307) 
        
        import re
        pattern = r'^/api/v1/([^/]+)/([^/]+)/api/v1/\1$'
        match = re.match(pattern, path)
        if match:
            resource = match.group(1)
            resource_id = match.group(2)
            corrected_path = f"/api/v1/{resource}/{resource_id}"
            app.logger.warning(f"URL malformada detectada: {path} → redirigiendo a {corrected_path}")
            return redirect(corrected_path, code=307)
    
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'False').lower() == 'true'
    )