from app.extensions import db
from datetime import datetime


class Billing(db.Model):
    __tablename__ = 'billings'

    id             = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(30), unique=True, nullable=False)
    booking_id     = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)

    # Customer snapshot
    customer_name    = db.Column(db.String(200))
    customer_phone   = db.Column(db.String(20))
    customer_email   = db.Column(db.String(120))
    customer_address = db.Column(db.Text)

    # Event snapshot
    event_type         = db.Column(db.String(50))
    event_date         = db.Column(db.String(20))
    event_duration     = db.Column(db.Integer, default=1)
    decoration_package = db.Column(db.String(50))

    # Labour
    number_of_labours = db.Column(db.Integer, default=0)
    labour_daily_wage = db.Column(db.Float, default=0)
    labour_days       = db.Column(db.Integer, default=1)
    total_labour_cost = db.Column(db.Float, default=0)

    # Materials
    flower_cost               = db.Column(db.Float, default=0)
    cloth_banner_cost         = db.Column(db.Float, default=0)
    electrical_materials_cost = db.Column(db.Float, default=0)
    rental_items_cost         = db.Column(db.Float, default=0)
    other_material_cost       = db.Column(db.Float, default=0)

    # Totals
    subtotal       = db.Column(db.Float, default=0)
    discount       = db.Column(db.Float, default=0)
    tax_rate       = db.Column(db.Float, default=0)
    tax_amount     = db.Column(db.Float, default=0)
    grand_total    = db.Column(db.Float, default=0)
    advance_paid   = db.Column(db.Float, default=0)
    pending_amount = db.Column(db.Float, default=0)

    billing_status = db.Column(db.String(30), default='Pending')
    payment_mode   = db.Column(db.String(30), default='Cash')
    notes          = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    # Relationships
    items   = db.relationship(
        'BillingItem',
        backref='billing',
        cascade='all, delete-orphan',
        lazy=True
    )

    def to_dict(self):
        return {
            'id':             self.id,
            'invoice_number': self.invoice_number,
            'booking_id':     self.booking_id,

            'customer_name':    self.customer_name,
            'customer_phone':   self.customer_phone,
            'customer_email':   self.customer_email,
            'customer_address': self.customer_address,

            'event_type':         self.event_type,
            'event_date':         self.event_date,
            'event_duration':     self.event_duration,
            'decoration_package': self.decoration_package,

            'number_of_labours': self.number_of_labours,
            'labour_daily_wage': self.labour_daily_wage,
            'labour_days':       self.labour_days,
            'total_labour_cost': float(self.total_labour_cost or 0),

            'flower_cost':               float(self.flower_cost or 0),
            'cloth_banner_cost':         float(self.cloth_banner_cost or 0),
            'electrical_materials_cost': float(self.electrical_materials_cost or 0),
            'rental_items_cost':         float(self.rental_items_cost or 0),
            'other_material_cost':       float(self.other_material_cost or 0),

            'subtotal':       float(self.subtotal or 0),
            'discount':       float(self.discount or 0),
            'tax_rate':       float(self.tax_rate or 0),
            'tax_amount':     float(self.tax_amount or 0),
            'grand_total':    float(self.grand_total or 0),
            'advance_paid':   float(self.advance_paid or 0),
            'pending_amount': float(self.pending_amount or 0),

            'billing_status': self.billing_status,
            'payment_mode':   self.payment_mode,
            'notes':          self.notes,

            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class BillingItem(db.Model):
    __tablename__ = 'billing_items'

    id           = db.Column(db.Integer, primary_key=True)
    billing_id   = db.Column(db.Integer,
                              db.ForeignKey('billings.id', ondelete='CASCADE'),
                              nullable=False)
    service_name = db.Column(db.String(200), nullable=False)
    quantity     = db.Column(db.Float, default=1)
    unit_price   = db.Column(db.Float, default=0)
    total_price  = db.Column(db.Float, default=0)

    def to_dict(self):
        return {
            'id':           self.id,
            'billing_id':   self.billing_id,
            'service_name': self.service_name,
            'quantity':     float(self.quantity or 1),
            'unit_price':   float(self.unit_price or 0),
            'total_price':  float(self.total_price or 0),
        }