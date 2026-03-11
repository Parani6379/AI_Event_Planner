from app.extensions import db
from datetime import datetime


class Labour(db.Model):
    __tablename__ = 'labours'

    id                  = db.Column(db.Integer, primary_key=True)
    name                = db.Column(db.String(200), nullable=False)
    phone               = db.Column(db.String(20),  unique=True, nullable=False)
    age                 = db.Column(db.Integer)
    daily_wage          = db.Column(db.Float,  nullable=False)
    address             = db.Column(db.Text)
    photo_path          = db.Column(db.String(300))
    is_active           = db.Column(db.Boolean, default=True)
    bank_name           = db.Column(db.String(100))
    bank_account_number = db.Column(db.String(50))
    bank_account_name   = db.Column(db.String(200))
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    attendance_records  = db.relationship('Attendance', backref='labour',
                                           cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id':                  self.id,
            'name':                self.name,
            'phone':               self.phone,
            'age':                 self.age,
            'daily_wage':          float(self.daily_wage),
            'address':             self.address,
            'photo_path':          self.photo_path,
            'is_active':           self.is_active,
            'bank_name':           self.bank_name,
            'bank_account_number': self.bank_account_number,
            'bank_account_name':   self.bank_account_name,
            'created_at':          self.created_at.isoformat() if self.created_at else None
        }