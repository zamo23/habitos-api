from flask import Blueprint
from controllers.habit_controller import (
    get_habits, create_habit, get_habit, get_habit_details, update_habit, delete_habit,
    get_habit_entries, create_habit_entry, delete_habit_entry, get_habit_streak,
    get_habits_dashboard, get_habit_stats, get_streaks_overview, get_weekly_progress
)

habit_bp = Blueprint('habits', __name__, url_prefix='/api/v1/habits')

habit_bp.add_url_rule('', view_func=get_habits, methods=['GET'])
habit_bp.add_url_rule('', view_func=create_habit, methods=['POST'])
habit_bp.add_url_rule('/<string:habit_id>', view_func=get_habit, methods=['GET'])
habit_bp.add_url_rule('/<string:habit_id>/details', view_func=get_habit_details, methods=['GET'])
habit_bp.add_url_rule('/<string:habit_id>', view_func=update_habit, methods=['PATCH'])
habit_bp.add_url_rule('/<string:habit_id>', view_func=delete_habit, methods=['DELETE'])
habit_bp.add_url_rule('/<string:habit_id>/entries', view_func=get_habit_entries, methods=['GET'])
habit_bp.add_url_rule('/<string:habit_id>/entries', view_func=create_habit_entry, methods=['POST'])
habit_bp.add_url_rule('/<string:habit_id>/entries/<string:entry_id>', view_func=delete_habit_entry, methods=['DELETE'])
habit_bp.add_url_rule('/<string:habit_id>/streak', view_func=get_habit_streak, methods=['GET'])
habit_bp.add_url_rule('/dashboard', view_func=get_habits_dashboard, methods=['GET'])
habit_bp.add_url_rule('/<string:habit_id>/stats', view_func=get_habit_stats, methods=['GET'])
habit_bp.add_url_rule('/streaks/overview', view_func=get_streaks_overview, methods=['GET'])
habit_bp.add_url_rule('/weekly-progress', view_func=get_weekly_progress, methods=['GET'])