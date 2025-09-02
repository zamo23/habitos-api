from flask import Blueprint
from controllers.system_controller import health, get_stats

system_bp = Blueprint('system', __name__, url_prefix='/api/v1/system')

system_bp.add_url_rule('/health', view_func=health, methods=['GET'])
system_bp.add_url_rule('/stats', view_func=get_stats, methods=['GET'])