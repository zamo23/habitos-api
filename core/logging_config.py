import logging.config
import os

def configure_logging():
    """Configura el sistema de logging para la aplicación"""
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'json': {
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': 'INFO'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join('logs', 'app.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'json',
                'level': 'INFO'
            }
        },
        'loggers': {
            '': { 
                'handlers': ['console', 'file'],
                'level': 'INFO'
            }
        }
    }
    
    os.makedirs('logs', exist_ok=True)
    logging.config.dictConfig(config)
