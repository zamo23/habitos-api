from flask import Blueprint
from controllers.group_habit_controller import create_group_habit, get_group_habits, get_group_habits_for_user, get_group_habit_details

group_habit_bp = Blueprint('group_habits', __name__, url_prefix='/api/v1/groups')

group_habit_bp.add_url_rule('/<string:group_id>/habits', view_func=create_group_habit, methods=['POST'])
group_habit_bp.add_url_rule('/<string:group_id>/habits', view_func=get_group_habits, methods=['GET'])
group_habit_bp.add_url_rule('/habits', view_func=get_group_habits_for_user, methods=['GET'])
group_habit_bp.add_url_rule('/habits/<string:habit_id>/details', view_func=get_group_habit_details, methods=['GET'])