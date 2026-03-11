from app.extensions import db
from datetime import datetime


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id             = db.Column(db.Integer, primary_key=True)
    labour_id      = db.Column(db.Integer, db.ForeignKey('labours.id'), nullable=False)
    date           = db.Column(db.String(20), nullable=False)
    is_present     = db.Column(db.Boolean, default=False)
    half_day       = db.Column(db.Boolean, default=False)
    wage_amount    = db.Column(db.Float, default=0)
    advance_amount = db.Column(db.Float, default=0)
    notes          = db.Column(db.Text)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':             self.id,
            'labour_id':      self.labour_id,
            'date':           self.date,
            'is_present':     self.is_present,
            'half_day':       self.half_day,
            'wage_amount':    float(self.wage_amount or 0),
            'advance_amount': float(self.advance_amount or 0),
            'notes':          self.notes,
            'created_at':     self.created_at.isoformat() if self.created_at else None
        }