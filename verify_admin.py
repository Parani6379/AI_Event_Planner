from app import create_app
from app.extensions import db
from app.models.admin import Admin

app = create_app()
with app.app_context():
    a = Admin.query.first()
    if a:
        print("Admin ID:", a.id)
        print("Email:", a.email)
        print("Username:", a.username)
        print("Password OK:", a.check_password('admin123'))
    else:
        print("No admin found!")
