from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt
)
from datetime import timedelta


def generate_admin_tokens(admin_id, admin_data=None):
    """Generate access + refresh tokens for admin."""
    additional_claims = {
        'role': 'admin',
        'user_id': admin_id
    }
    if admin_data:
        additional_claims.update(admin_data)

    access_token = create_access_token(
        identity=str(admin_id),
        additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(
        identity=str(admin_id),
        additional_claims=additional_claims
    )
    return access_token, refresh_token


def generate_customer_tokens(customer_id, customer_data=None):
    """Generate access + refresh tokens for customer."""
    additional_claims = {
        'role': 'customer',
        'user_id': customer_id
    }
    if customer_data:
        additional_claims.update(customer_data)

    access_token = create_access_token(
        identity=str(customer_id),
        additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(
        identity=str(customer_id),
        additional_claims=additional_claims
    )
    return access_token, refresh_token


def get_current_user_id():
    """Get current user's ID from JWT."""
    try:
        identity = get_jwt_identity()
        return int(identity) if identity else None
    except Exception:
        return None


def get_current_role():
    """Get current user's role from JWT."""
    try:
        claims = get_jwt()
        return claims.get('role')
    except Exception:
        return None