from flask import Blueprint, jsonify, request, render_template
from app.controllers.customer_controller import CustomerController

# ── API blueprint ─────────────────────────────────────
customer_bp = Blueprint('customer', __name__)

# ── Page blueprint (customer website pages) ───────────
customer_pages_bp = Blueprint('customer_pages', __name__)


# ════════════════════════════════════════════════════
# CUSTOMER PAGE ROUTES
# ════════════════════════════════════════════════════

@customer_pages_bp.route('/')
def index():
    return render_template('customer/index.html')


@customer_pages_bp.route('/services')
def services():
    return render_template('customer/services.html')


@customer_pages_bp.route('/gallery')
def gallery():
    return render_template('customer/gallery.html')


@customer_pages_bp.route('/booking')
def booking():
    return render_template('customer/booking.html')


@customer_pages_bp.route('/contact')
def contact():
    return render_template('customer/contact.html')


@customer_pages_bp.route('/login')
def login():
    return render_template('customer/login.html')


@customer_pages_bp.route('/register')
def register():
    return render_template('customer/register.html')


# ════════════════════════════════════════════════════
# CUSTOMER API ROUTES
# ════════════════════════════════════════════════════

@customer_bp.route('/home-data', methods=['GET'])
def home_data():
    return CustomerController.get_home_data()


@customer_bp.route('/contact-info', methods=['GET'])
def contact_info():
    return CustomerController.get_contact_info()