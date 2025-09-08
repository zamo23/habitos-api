from flask import Blueprint
from controllers.group_controller import (
    get_groups, create_group, get_group, update_group, 
    add_member, remove_member, create_invite, accept_invite, 
    get_invites, get_group_invites, verify_invitation, create_batch_invites,
    leave_group
)

group_bp = Blueprint('groups', __name__, url_prefix='/api/v1/groups')

group_bp.add_url_rule('', view_func=get_groups, methods=['GET'])
group_bp.add_url_rule('', view_func=create_group, methods=['POST'])
group_bp.add_url_rule('/<string:group_id>', view_func=get_group, methods=['GET'])
group_bp.add_url_rule('/<string:group_id>', view_func=update_group, methods=['PATCH'])
group_bp.add_url_rule('/<string:group_id>/members', view_func=add_member, methods=['POST'])
group_bp.add_url_rule('/<string:group_id>/members/<string:member_id>', view_func=remove_member, methods=['DELETE'])
group_bp.add_url_rule('/<string:group_id>/leave', view_func=leave_group, methods=['POST'])
group_bp.add_url_rule('/<string:group_id>/invites', view_func=create_invite, methods=['POST'])
group_bp.add_url_rule('/<string:group_id>/invites', view_func=get_group_invites, methods=['GET'])
group_bp.add_url_rule('/<string:group_id>/invites/batch', view_func=create_batch_invites, methods=['POST'])
group_bp.add_url_rule('/invites', view_func=get_invites, methods=['GET'])
group_bp.add_url_rule('/invites/verify', view_func=verify_invitation, methods=['GET', 'OPTIONS'])
group_bp.add_url_rule('/invites/accept', view_func=accept_invite, methods=['POST', 'OPTIONS'])