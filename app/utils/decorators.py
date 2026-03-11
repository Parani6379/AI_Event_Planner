from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt.exceptions import ExpiredSignatureError


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({
                    'success': False,
                    'message': 'Admin access required.'
                }), 403
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Authentication required.'
            }), 401
        return fn(*args, **kwargs)
    return wrapper


def customer_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != 'customer':
                return jsonify({
                    'success': False,
                    'message': 'Customer access required.'
                }), 403
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Authentication required.'
            }), 401
        return fn(*args, **kwargs)
    return wrapper


def any_authenticated(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Authentication required.'
            }), 401
        return fn(*args, **kwargs)
    return wrapper