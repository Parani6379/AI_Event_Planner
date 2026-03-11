from flask import Blueprint
from app.controllers.design_controller import DesignController
from app.utils.decorators import admin_required

design_bp = Blueprint('design', __name__)

@design_bp.route('/', methods=['POST'])
@admin_required
def add():
    return DesignController.add_design()

@design_bp.route('/', methods=['GET'])
@admin_required
def get_all():
    return DesignController.get_all_designs()

@design_bp.route('/public', methods=['GET'])
def public():
    return DesignController.get_public_designs()

@design_bp.route('/stats', methods=['GET'])
@admin_required
def stats():
    return DesignController.get_stats()

@design_bp.route('/<int:design_id>', methods=['GET'])
def get_one(design_id):
    return DesignController.get_design(design_id)

@design_bp.route('/<int:design_id>', methods=['PUT'])
@admin_required
def update(design_id):
    return DesignController.update_design(design_id)

@design_bp.route('/<int:design_id>', methods=['DELETE'])
@admin_required
def delete(design_id):
    return DesignController.delete_design(design_id)

@design_bp.route('/<int:design_id>/toggle-featured', methods=['PUT'])
@admin_required
def toggle_featured(design_id):
    return DesignController.toggle_featured(design_id)

@design_bp.route('/<int:design_id>/toggle-active', methods=['PUT'])
@admin_required
def toggle_active(design_id):
    return DesignController.toggle_active(design_id)