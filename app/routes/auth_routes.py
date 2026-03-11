from flask import Blueprint
from app.controllers.auth_controller import AuthController
from app.utils.decorators import any_authenticated

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/health', methods=['GET'])
def health():
    return AuthController.health_check()


@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    return AuthController.admin_login()


@auth_bp.route('/customer/register', methods=['POST'])
def customer_register():
    return AuthController.customer_register()


@auth_bp.route('/customer/login', methods=['POST'])
def customer_login():
    return AuthController.customer_login()


@auth_bp.route('/me', methods=['GET'])
@any_authenticated
def get_me():
    return AuthController.get_me()


@auth_bp.route('/change-password', methods=['POST'])
@any_authenticated
def change_password():
    return AuthController.change_password()