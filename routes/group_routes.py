from flask import Blueprint
from controllers.group_controller import get_groups, create_group, get_group, update_group, add_member, remove_member, create_invite

group_bp = Blueprint('groups', __name__, url_prefix='/api/v1/groups')

group_bp.add_url_rule('', view_func=get_groups, methods=['GET'])
group_bp.add_url_rule('', view_func=create_group, methods=['POST'])
group_bp.add_url_rule('/<string:group_id>', view_func=get_group, methods=['GET'])
group_bp.add_url_rule('/<string:group_id>', view_func=update_group, methods=['PATCH'])
group_bp.add_url_rule('/<string:group_id>/members', view_func=add_member, methods=['POST'])
group_bp.add_url_rule('/<string:group_id>/members/<string:member_id>', view_func=remove_member, methods=['DELETE'])
group_bp.add_url_rule('/<string:group_id>/invites', view_func=create_invite, methods=['POST'])