from flask import Blueprint
from controllers.report_controller import get_reports_overview, get_reports_weekly, get_reports_heatmap, get_streaks_overview

report_bp = Blueprint('reports', __name__, url_prefix='/api/v1/reports')

report_bp.add_url_rule('/overview', view_func=get_reports_overview, methods=['GET'])
report_bp.add_url_rule('/weekly', view_func=get_reports_weekly, methods=['GET'])
report_bp.add_url_rule('/heatmap', view_func=get_reports_heatmap, methods=['GET'])
report_bp.add_url_rule('/streaks-overview', view_func=get_streaks_overview, methods=['GET'])