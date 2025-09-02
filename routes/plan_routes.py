from flask import Blueprint
from controllers.plan_controller import get_plans, get_my_subscription, create_subscription, get_habits_usage

plan_bp = Blueprint('plans', __name__, url_prefix='/api/v1')

plan_bp.add_url_rule('/plans', view_func=get_plans, methods=['GET'])
plan_bp.add_url_rule('/subscriptions/mine', view_func=get_my_subscription, methods=['GET'])
plan_bp.add_url_rule('/subscriptions', view_func=create_subscription, methods=['POST'])
plan_bp.add_url_rule('/usage/habits', view_func=get_habits_usage, methods=['GET', 'OPTIONS'])