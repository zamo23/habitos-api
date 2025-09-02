from flask import Blueprint
from controllers.subscription_controller import get_current_subscription

subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/v1')

subscription_bp.add_url_rule('/suscripcion/actual', view_func=get_current_subscription, methods=['GET'])