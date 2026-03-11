from flask import Blueprint
from app.controllers.labour_controller import LabourController
from app.utils.decorators import admin_required

labour_bp = Blueprint('labour', __name__)

@labour_bp.route('/', methods=['POST'])
@admin_required
def add():
    return LabourController.add_labour()

@labour_bp.route('/', methods=['GET'])
@admin_required
def get_all():
    return LabourController.get_all_labour()

@labour_bp.route('/<int:labour_id>', methods=['GET'])
@admin_required
def get_one(labour_id):
    return LabourController.get_labour(labour_id)

@labour_bp.route('/<int:labour_id>', methods=['PUT'])
@admin_required
def update(labour_id):
    return LabourController.update_labour(labour_id)

@labour_bp.route('/<int:labour_id>', methods=['DELETE'])
@admin_required
def delete(labour_id):
    return LabourController.delete_labour(labour_id)

@labour_bp.route('/attendance', methods=['POST'])
@admin_required
def mark_attendance():
    return LabourController.mark_attendance()

@labour_bp.route('/attendance/bulk', methods=['POST'])
@admin_required
def bulk_attendance():
    return LabourController.bulk_attendance()

@labour_bp.route('/<int:labour_id>/attendance', methods=['GET'])
@admin_required
def get_attendance(labour_id):
    return LabourController.get_attendance(labour_id)

@labour_bp.route('/attendance/daily-summary', methods=['GET'])
@admin_required
def daily_summary():
    return LabourController.get_daily_summary()

@labour_bp.route('/<int:labour_id>/statement', methods=['GET'])
@admin_required
def statement(labour_id):
    return LabourController.get_statement(labour_id)

@labour_bp.route('/<int:labour_id>/advance', methods=['POST'])
@admin_required
def add_advance(labour_id):
    return LabourController.add_advance(labour_id)