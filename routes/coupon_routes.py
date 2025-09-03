from flask import Blueprint
from controllers.coupon_controller import create_coupon, verify_coupon, list_coupons, redeem_free_coupon

coupon_bp = Blueprint('coupon', __name__, url_prefix='/api/v1')

coupon_bp.add_url_rule('/cupones/verificar', view_func=verify_coupon, methods=['POST', 'OPTIONS'])
coupon_bp.add_url_rule('/cupones/redimir', view_func=redeem_free_coupon, methods=['POST', 'OPTIONS'])
