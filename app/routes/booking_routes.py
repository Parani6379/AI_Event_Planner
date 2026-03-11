from flask import Blueprint
from app.controllers.booking_controller import BookingController
from app.utils.decorators import admin_required, customer_required, any_authenticated

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/', methods=['POST'])
@any_authenticated
def create():
    return BookingController.create_booking()

@booking_bp.route('/', methods=['GET'])
@admin_required
def get_all():
    return BookingController.get_all_bookings()

@booking_bp.route('/stats', methods=['GET'])
@admin_required
def stats():
    return BookingController.get_stats()

@booking_bp.route('/today', methods=['GET'])
@admin_required
def today():
    return BookingController.get_today_bookings()

@booking_bp.route('/upcoming', methods=['GET'])
@admin_required
def upcoming():
    return BookingController.get_upcoming_bookings()

@booking_bp.route('/my-bookings', methods=['GET'])
@customer_required
def my_bookings():
    return BookingController.get_my_bookings()

@booking_bp.route('/<int:booking_id>', methods=['GET'])
@any_authenticated
def get_one(booking_id):
    return BookingController.get_booking(booking_id)

@booking_bp.route('/<int:booking_id>', methods=['PUT'])
@admin_required
def update(booking_id):
    return BookingController.update_booking(booking_id)

@booking_bp.route('/<int:booking_id>/status', methods=['PUT'])
@admin_required
def update_status(booking_id):
    return BookingController.update_status(booking_id)

@booking_bp.route('/<int:booking_id>/payment', methods=['PUT'])
@admin_required
def update_payment(booking_id):
    return BookingController.update_payment(booking_id)

@booking_bp.route('/<int:booking_id>/assign-labour', methods=['POST'])
@admin_required
def assign_labour(booking_id):
    return BookingController.assign_labour(booking_id)

@booking_bp.route('/<int:booking_id>/remove-labour/<int:labour_id>', methods=['DELETE'])
@admin_required
def remove_labour(booking_id, labour_id):
    return BookingController.remove_labour(booking_id, labour_id)

@booking_bp.route('/<int:booking_id>/cancel', methods=['PUT'])
@customer_required
def cancel(booking_id):
    return BookingController.cancel_booking(booking_id)