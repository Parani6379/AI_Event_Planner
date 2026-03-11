from app.extensions import db
from datetime import datetime


class Expense(db.Model):
    __tablename__ = 'expenses'

    id           = db.Column(db.Integer, primary_key=True)
    expense_type = db.Column(db.String(100), nullable=False)
    category     = db.Column(db.String(20), default='Other')  # Labour / Other
    amount       = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.String(20), nullable=False)
    description  = db.Column(db.Text)
    notes        = db.Column(db.Text)
    receipt_path = db.Column(db.String(300))
    booking_id   = db.Column(db.Integer, db.ForeignKey('bookings.id'),  nullable=True)
    labour_id    = db.Column(db.Integer, db.ForeignKey('labours.id'),   nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':           self.id,
            'expense_type': self.expense_type,
            'category':     self.category,
            'amount':       float(self.amount),
            'expense_date': self.expense_date,
            'description':  self.description,
            'notes':        self.notes,
            'receipt_path': self.receipt_path,
            'booking_id':   self.booking_id,
            'labour_id':    self.labour_id,
            'created_at':   self.created_at.isoformat() if self.created_at else None
        }