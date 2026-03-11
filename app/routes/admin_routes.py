from flask import Blueprint, render_template
from app.controllers.admin_controller import AdminController
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)


# ── Dashboard Stats ───────────────────────────────────
@admin_bp.route('/dashboard/stats', methods=['GET'])
@admin_required
def dashboard_stats():
    return AdminController.get_dashboard_stats()


# ── Chart Data ────────────────────────────────────────
@admin_bp.route('/dashboard/revenue', methods=['GET'])
@admin_required
def dashboard_revenue():
    return AdminController.get_revenue_chart()


@admin_bp.route('/dashboard/expenses', methods=['GET'])
@admin_required
def dashboard_expenses():
    return AdminController.get_expense_chart()


@admin_bp.route('/dashboard/booking-trends', methods=['GET'])
@admin_required
def dashboard_booking_trends():
    return AdminController.get_booking_trends()


@admin_bp.route('/dashboard/profit', methods=['GET'])
@admin_required
def dashboard_profit():
    return AdminController.get_profit_chart()


@admin_bp.route('/dashboard/recent-activity', methods=['GET'])
@admin_required
def dashboard_recent_activity():
    return AdminController.get_recent_activity()


# ── Profile ───────────────────────────────────────────
@admin_bp.route('/profile', methods=['GET'])
@admin_required
def get_profile():
    return AdminController.get_profile()


@admin_bp.route('/profile', methods=['PUT'])
@admin_required
def update_profile():
    return AdminController.update_profile()


# ── Customers ─────────────────────────────────────────
@admin_bp.route('/customers', methods=['GET'])
@admin_required
def get_customers():
    return AdminController.get_all_customers()


@admin_bp.route('/customers/<int:customer_id>/toggle', methods=['PUT'])
@admin_required
def toggle_customer(customer_id):
    return AdminController.toggle_customer_status(customer_id)


@admin_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@admin_required
def delete_customer(customer_id):
    return AdminController.delete_customer(customer_id)