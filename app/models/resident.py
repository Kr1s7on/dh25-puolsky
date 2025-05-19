from .. import db
from sqlalchemy.orm import relationship


class Resident(db.Model):
    """
    Resident model for patients in the care facility.
    Residents can only be created by admin users.
    """
    __tablename__ = 'residents'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    date_of_birth = db.Column(db.Date)
    photo_url = db.Column(db.String(256))
    
    # Relationships
    inventory_items = relationship('InventoryItem', back_populates='resident')
    usage_logs = relationship('UsageLog', back_populates='resident')
    
    def __repr__(self):
        return '<Resident \'%s\'>' % self.name
