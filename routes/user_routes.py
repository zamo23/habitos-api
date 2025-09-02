from flask import Blueprint
from controllers.user_controller import me, update_me, get_local_time, get_recent_activity, get_timezones, detect_timezone, get_activity_heatmap, get_habit_summary, get_weekly_progress

user_bp = Blueprint('users', __name__, url_prefix='/api/v1')

user_bp.add_url_rule('/me', view_func=me, methods=['GET'])
user_bp.add_url_rule('/me', view_func=update_me, methods=['PATCH'])
user_bp.add_url_rule('/me/local-time', view_func=get_local_time, methods=['GET'])
user_bp.add_url_rule('/me/recent-activity', view_func=get_recent_activity, methods=['GET'])
user_bp.add_url_rule('/timezones', view_func=get_timezones, methods=['GET'])
user_bp.add_url_rule('/detect-timezone', view_func=detect_timezone, methods=['POST'])
user_bp.add_url_rule('/me/activity-heatmap', view_func=get_activity_heatmap, methods=['GET'])
user_bp.add_url_rule('/me/habit-summary', view_func=get_habit_summary, methods=['GET'])
user_bp.add_url_rule('/me/weekly-progress', view_func=get_weekly_progress, methods=['GET'])