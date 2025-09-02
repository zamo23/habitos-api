from flask import Blueprint
from controllers.payment_controller import confirm_payment, verify_payment

payment_bp = Blueprint('payment', __name__, url_prefix='/api/v1')

payment_bp.add_url_rule('/pagos/confirmaciones', view_func=confirm_payment, methods=['POST'])
payment_bp.add_url_rule('/pagos/verificar', view_func=verify_payment, methods=['POST', 'OPTIONS'])