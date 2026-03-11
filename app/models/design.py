from app.extensions import db
from datetime import datetime


class Design(db.Model):
    __tablename__ = 'designs'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category    = db.Column(db.String(50), nullable=False)  # Wedding / Temple Festival / Reception
    image_path  = db.Column(db.String(300))
    thumb_path  = db.Column(db.String(300))
    is_featured = db.Column(db.Boolean, default=False)
    is_active   = db.Column(db.Boolean, default=True)
    view_count  = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':          self.id,
            'title':       self.title,
            'description': self.description,
            'category':    self.category,
            'image_path':  self.image_path,
            'thumb_path':  self.thumb_path,
            'is_featured': self.is_featured,
            'is_active':   self.is_active,
            'view_count':  self.view_count,
            'created_at':  self.created_at.isoformat() if self.created_at else None
        }