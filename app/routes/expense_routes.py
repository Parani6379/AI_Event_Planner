from flask import Blueprint
from app.controllers.expense_controller import ExpenseController
from app.utils.decorators import admin_required

expense_bp = Blueprint('expense', __name__)

@expense_bp.route('/', methods=['POST'])
@admin_required
def add():
    return ExpenseController.add_expense()

@expense_bp.route('/', methods=['GET'])
@admin_required
def get_all():
    return ExpenseController.get_all_expenses()

@expense_bp.route('/today', methods=['GET'])
@admin_required
def today():
    return ExpenseController.get_today_expenses()

@expense_bp.route('/monthly-statement', methods=['GET'])
@admin_required
def monthly():
    return ExpenseController.get_monthly_statement()

@expense_bp.route('/types', methods=['GET'])
@admin_required
def types():
    return ExpenseController.get_expense_types()

@expense_bp.route('/<int:expense_id>', methods=['GET'])
@admin_required
def get_one(expense_id):
    return ExpenseController.get_expense(expense_id)

@expense_bp.route('/<int:expense_id>', methods=['PUT'])
@admin_required
def update(expense_id):
    return ExpenseController.update_expense(expense_id)

@expense_bp.route('/<int:expense_id>', methods=['DELETE'])
@admin_required
def delete(expense_id):
    return ExpenseController.delete_expense(expense_id)