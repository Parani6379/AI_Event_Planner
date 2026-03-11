from flask import Blueprint
from app.controllers.billing_controller import BillingController
from app.utils.decorators import admin_required

billing_bp = Blueprint('billing', __name__)


@billing_bp.route('/', methods=['POST'])
@admin_required
def create():
    return BillingController.create_billing()


@billing_bp.route('/', methods=['GET'])
@admin_required
def get_all():
    return BillingController.get_all_billings()


@billing_bp.route('/<int:billing_id>', methods=['GET'])
@admin_required
def get_one(billing_id):
    return BillingController.get_billing(billing_id)


@billing_bp.route('/by-booking/<int:booking_id>', methods=['GET'])
@admin_required
def get_by_booking(booking_id):
    return BillingController.get_billing_by_booking(booking_id)


@billing_bp.route('/booking/<int:booking_id>', methods=['GET'])
@admin_required
def get_booking_for_billing(booking_id):
    return BillingController.get_booking_for_billing(booking_id)


@billing_bp.route('/<int:billing_id>', methods=['PUT'])
@admin_required
def update(billing_id):
    return BillingController.update_billing(billing_id)


@billing_bp.route('/<int:billing_id>/payment', methods=['PUT'])
@admin_required
def update_payment(billing_id):
    return BillingController.update_payment(billing_id)


@billing_bp.route('/<int:billing_id>', methods=['DELETE'])
@admin_required
def delete(billing_id):
    return BillingController.delete_billing(billing_id)


@billing_bp.route('/<int:billing_id>/pdf', methods=['GET'])
@admin_required
def download_pdf(billing_id):
    return BillingController.download_pdf(billing_id)


@billing_bp.route('/payment-statement', methods=['GET'])
@admin_required
def payment_statement():
    return BillingController.get_payment_statement()