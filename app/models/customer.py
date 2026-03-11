from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class Customer(db.Model):
    __tablename__ = 'customers'

    id         = db.Column(db.Integer, primary_key=True)
    full_name  = db.Column(db.String(200), nullable=False)
    phone      = db.Column(db.String(20), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    address    = db.Column(db.Text)
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings   = db.relationship('Booking', backref='customer', lazy=True)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def to_dict(self):
        return {
            'id':        self.id,
            'full_name': self.full_name,
            'phone':     self.phone,
            'email':     self.email,
            'address':   self.address,
            'is_active': self.is_active,
            'created_at':self.created_at.isoformat() if self.created_at else None
        }