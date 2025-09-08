from flask import Blueprint
from controllers.notification_controller import get_notifications, mark_notification_read, delete_notification

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')

notification_bp.add_url_rule('', view_func=get_notifications, methods=['GET'])
notification_bp.add_url_rule('/<string:notification_id>/read', view_func=mark_notification_read, methods=['POST'])
notification_bp.add_url_rule('/<string:notification_id>', view_func=delete_notification, methods=['DELETE'])
