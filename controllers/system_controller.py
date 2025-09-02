from flask import jsonify
from datetime import datetime
from services.auth_service import auth_required
from services.stats_service import get_system_stats

@auth_required
def health():
    """Verificar el estado del sistema"""
    return jsonify({
        'ok': True,
        'time': datetime.utcnow().isoformat()
    })

@auth_required
def get_stats():
    """Obtener estadísticas del sistema"""
    try:
        stats = get_system_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': {'code': 'server_error', 'message': str(e)}}), 500