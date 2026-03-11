from app.extensions import db
from datetime import datetime


class Booking(db.Model):
    __tablename__ = 'bookings'

    id             = db.Column(db.Integer, primary_key=True)
    booking_number = db.Column(db.String(30), unique=True, nullable=False)

    # Customer reference + snapshot (snapshot so data stays even if customer deleted)
    customer_id    = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_name  = db.Column(db.String(200), nullable=False, default='')
    customer_phone = db.Column(db.String(20),  nullable=False, default='')
    customer_email = db.Column(db.String(120), default='')

    # Event details
    event_type           = db.Column(db.String(100), nullable=False)
    event_date           = db.Column(db.String(20),  nullable=False)  # stored as 'YYYY-MM-DD'
    event_location       = db.Column(db.Text,        nullable=False)
    event_duration       = db.Column(db.Integer, default=1)
    design_id            = db.Column(db.Integer, db.ForeignKey('designs.id'), nullable=True)
    decoration_package   = db.Column(db.String(100), default='')
    special_requirements = db.Column(db.Text, default='')

    # Status
    status      = db.Column(db.String(30), default='Pending')
    admin_notes = db.Column(db.Text, default='')

    # Payment
    total_amount   = db.Column(db.Float, default=0.0)
    advance_paid   = db.Column(db.Float, default=0.0)
    pending_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(30), default='Pending')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    billing         = db.relationship('Billing', backref='booking', uselist=False, lazy=True)
    assigned_labours= db.relationship('BookingLabour', backref='booking', lazy=True,
                                       cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':                   self.id,
            'booking_number':       self.booking_number,
            'customer_id':          self.customer_id,
            'customer_name':        self.customer_name or '',
            'customer_phone':       self.customer_phone or '',
            'customer_email':       self.customer_email or '',
            'event_type':           self.event_type,
            'event_date':           self.event_date,
            'event_location':       self.event_location,
            'event_duration':       self.event_duration,
            'design_id':            self.design_id,
            'decoration_package':   self.decoration_package,
            'special_requirements': self.special_requirements,
            'status':               self.status,
            'total_amount':         float(self.total_amount or 0),
            'advance_paid':         float(self.advance_paid or 0),
            'pending_amount':       float(self.pending_amount or 0),
            'payment_status':       self.payment_status,
            'admin_notes':          self.admin_notes,
            'created_at':           self.created_at.isoformat() if self.created_at else None,
        }


class BookingLabour(db.Model):
    __tablename__ = 'booking_labours'

    id            = db.Column(db.Integer, primary_key=True)
    booking_id    = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    labour_id     = db.Column(db.Integer, db.ForeignKey('labours.id'),  nullable=False)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':            self.id,
            'booking_id':    self.booking_id,
            'labour_id':     self.labour_id,
            'assigned_date': self.assigned_date.isoformat() if self.assigned_date else None,
        }
