from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, get_jwt
from app.extensions import db
from app.models.admin import Admin
from app.models.customer import Customer
from app.utils.jwt_helper import (
    generate_admin_tokens,
    generate_customer_tokens
)


class AuthController:

    # ════════════════════════════════════════════════
    # ADMIN AUTH
    # ════════════════════════════════════════════════

    @staticmethod
    def admin_login():
        try:
            data     = request.get_json()
            username = (data.get('username') or data.get('email') or '').strip()
            password = (data.get('password') or '').strip()

            if not username or not password:
                return jsonify({
                    'success': False,
                    'message': 'Username and password are required.'
                }), 400

            admin = Admin.query.filter(
                (Admin.username == username) | (Admin.email == username)
            ).first()

            if not admin or not admin.check_password(password):
                return jsonify({
                    'success': False,
                    'message': 'Invalid credentials.'
                }), 401

            access_token, refresh_token = generate_admin_tokens(
                admin.id,
                {'username': admin.username, 'email': admin.email}
            )

            return jsonify({
                'success': True,
                'message': 'Login successful.',
                'data': {
                    'access_token':  access_token,
                    'refresh_token': refresh_token,
                    'admin': {
                        'id':            admin.id,
                        'username':      admin.username,
                        'email':         admin.email,
                        'business_name': admin.business_name
                    }
                }
            })

        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ════════════════════════════════════════════════
    # CUSTOMER AUTH
    # ════════════════════════════════════════════════

    @staticmethod
    def customer_register():
        try:
            data      = request.get_json()
            full_name = (data.get('full_name') or '').strip()
            phone     = (data.get('phone') or '').strip()
            email     = (data.get('email') or '').strip().lower()
            password  = (data.get('password') or '').strip()
            address   = (data.get('address') or '').strip()

            # Validate
            if not all([full_name, phone, email, password]):
                return jsonify({
                    'success': False,
                    'message': 'Full name, phone, email and password are required.'
                }), 400

            if len(password) < 6:
                return jsonify({
                    'success': False,
                    'message': 'Password must be at least 6 characters.'
                }), 400

            if Customer.query.filter_by(email=email).first():
                return jsonify({
                    'success': False,
                    'message': 'Email already registered.'
                }), 409

            if Customer.query.filter_by(phone=phone).first():
                return jsonify({
                    'success': False,
                    'message': 'Phone number already registered.'
                }), 409

            customer = Customer(
                full_name=full_name,
                phone=phone,
                email=email,
                address=address
            )
            customer.set_password(password)
            db.session.add(customer)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Account created successfully!',
                'data': {'customer_id': customer.id}
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def customer_login():
        try:
            data     = request.get_json()
            email    = (data.get('email') or '').strip().lower()
            password = (data.get('password') or '').strip()

            if not email or not password:
                return jsonify({
                    'success': False,
                    'message': 'Email and password are required.'
                }), 400

            customer = Customer.query.filter_by(email=email).first()

            if not customer or not customer.check_password(password):
                return jsonify({
                    'success': False,
                    'message': 'Invalid email or password.'
                }), 401

            if not customer.is_active:
                return jsonify({
                    'success': False,
                    'message': 'Your account has been deactivated. Contact admin.'
                }), 403

            access_token, refresh_token = generate_customer_tokens(
                customer.id,
                {'full_name': customer.full_name, 'email': customer.email}
            )

            return jsonify({
                'success': True,
                'message': 'Login successful.',
                'data': {
                    'access_token':  access_token,
                    'refresh_token': refresh_token,
                    'customer': {
                        'id':        customer.id,
                        'full_name': customer.full_name,
                        'email':     customer.email,
                        'phone':     customer.phone
                    }
                }
            })

        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_me():
        try:
            claims  = get_jwt()
            role    = claims.get('role')
            user_id = int(get_jwt_identity())

            if role == 'admin':
                admin = Admin.query.get(user_id)
                if not admin:
                    return jsonify({'success': False, 'message': 'Admin not found.'}), 404
                return jsonify({
                    'success': True,
                    'data': {**admin.to_dict(), 'role': 'admin'}
                })
            else:
                customer = Customer.query.get(user_id)
                if not customer:
                    return jsonify({'success': False, 'message': 'Customer not found.'}), 404
                return jsonify({
                    'success': True,
                    'data': {**customer.to_dict(), 'role': 'customer'}
                })

        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def change_password():
        try:
            claims      = get_jwt()
            role        = claims.get('role')
            user_id     = int(get_jwt_identity())
            data        = request.get_json()
            old_password= (data.get('old_password') or '').strip()
            new_password= (data.get('new_password') or '').strip()

            if not old_password or not new_password:
                return jsonify({
                    'success': False,
                    'message': 'Old and new passwords are required.'
                }), 400

            if len(new_password) < 6:
                return jsonify({
                    'success': False,
                    'message': 'New password must be at least 6 characters.'
                }), 400

            if role == 'admin':
                user = Admin.query.get(user_id)
            else:
                user = Customer.query.get(user_id)

            if not user or not user.check_password(old_password):
                return jsonify({
                    'success': False,
                    'message': 'Current password is incorrect.'
                }), 401

            user.set_password(new_password)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Password changed successfully.'
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def health_check():
        return jsonify({
            'success': True,
            'message': 'API is running.',
            'version': '1.0.0'
        })