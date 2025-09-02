import os
import pytz

def configure_timezone(app):
    """Configurar zona horaria y formatos de fecha/hora"""
    app.config['TIMEZONE_DEFAULT'] = 'UTC'
    app.config['DATETIME_FORMAT'] = '%Y-%m-%d %H:%M:%S'
    app.config['DATE_FORMAT'] = '%Y-%m-%d'
    app.config['TIME_FORMAT'] = '%H:%M:%S'
    app.config['DEFAULT_CLOSURE_HOUR'] = 0
