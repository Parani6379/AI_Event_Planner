"""
Reset / recreate the admin account.
Run:  python reset_admin.py
"""
import sys
from app import create_app
from app.extensions import db
from app.models.admin import Admin

# ── Set your credentials here ──
ADMIN_EMAIL    = "parani6379@gmail.com"
ADMIN_PASSWORD = "admin123"
ADMIN_USERNAME = "parani"
# ────────────────────────────────

app = create_app()

with app.app_context():
    # Remove all existing admins
    Admin.query.delete()
    db.session.commit()

    # Create fresh admin
    new_admin = Admin(
        username      = ADMIN_USERNAME,
        email         = ADMIN_EMAIL,
        business_name = 'Event Planner Pro',
        phone         = '8610000718'
    )
    new_admin.set_password(ADMIN_PASSWORD)
    db.session.add(new_admin)
    db.session.commit()

    print("=" * 50)
    print("[OK] New admin account created!")
    print("=" * 50)
    print(f"   Email    : {ADMIN_EMAIL}")
    print(f"   Password : {ADMIN_PASSWORD}")
    print("=" * 50)
