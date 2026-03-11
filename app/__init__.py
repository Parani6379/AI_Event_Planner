from flask import Flask
from app.config import Config
from app.extensions import db, jwt, cors
import os


def create_app():
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='static'          # serves app/static/ at /static/
    )
    app.config.from_object(Config)

    # ── Init Extensions ──────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # ── Ensure Upload Directories inside app/static/ ─
    # Flask auto-serves app/static/ at /static/ — no custom route needed
    upload_base = os.path.join(app.root_path, 'static', 'uploads')
    for folder in ['designs', 'labour_photos', 'logo',
                   'receipts', 'ai_results', 'ai_uploads', 'invoices']:
        os.makedirs(os.path.join(upload_base, folder), exist_ok=True)

    app.config['UPLOAD_FOLDER'] = upload_base

    # ── Register API Blueprints ──────────────────────
    from app.routes.auth_routes     import auth_bp
    from app.routes.admin_routes    import admin_bp
    from app.routes.labour_routes   import labour_bp
    from app.routes.expense_routes  import expense_bp
    from app.routes.booking_routes  import booking_bp
    from app.routes.billing_routes  import billing_bp
    from app.routes.design_routes   import design_bp
    from app.routes.ai_routes       import ai_bp
    from app.routes.customer_routes import customer_bp, customer_pages_bp

    app.register_blueprint(auth_bp,     url_prefix='/api/auth')
    app.register_blueprint(admin_bp,    url_prefix='/api/admin')
    app.register_blueprint(labour_bp,   url_prefix='/api/labour')
    app.register_blueprint(expense_bp,  url_prefix='/api/expenses')
    app.register_blueprint(booking_bp,  url_prefix='/api/bookings')
    app.register_blueprint(billing_bp,  url_prefix='/api/billing')
    app.register_blueprint(design_bp,   url_prefix='/api/designs')
    app.register_blueprint(ai_bp,       url_prefix='/api/ai')
    app.register_blueprint(customer_bp, url_prefix='/api/customer')

    # ── Register Page Blueprints ─────────────────────
    from app.routes.page_routes     import pages_bp
    app.register_blueprint(pages_bp)
    app.register_blueprint(customer_pages_bp)

    # ── Create DB + Seed ─────────────────────────────
    with app.app_context():
        from app.models import (
            admin, customer, booking, labour,
            attendance, expense, billing, design
        )
        db.create_all()

        from app.models.admin import Admin
        if not Admin.query.first():
            default_admin = Admin(
                username      = 'admin',
                email         = 'admin@eventplanner.com',
                business_name = 'Event Planner Pro',
                phone         = '8610000718'
            )
            default_admin.set_password('admin123')
            db.session.add(default_admin)
            db.session.commit()
            print("✅ Default admin created: admin / admin123")

    return app
