import os
from flask import Flask
from dotenv import load_dotenv

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
        "default_timezone": app.config.get('TIMEZONE_DEFAULT', 'UTC')
    })
    app.container = container
    configure_application(app)
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