from .. import db
from sqlalchemy.orm import relationship
import enum
from datetime import datetime


class UsageStatus(enum.Enum):
    """Enum for status of UsageLog."""
    TAKEN = 'taken'
    MISSED = 'missed'


class UsageLog(db.Model):
    """
    UsageLog model for tracking medication and supply usage.
    """
    __tablename__ = 'usage_logs'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_time = db.Column(db.String(5), nullable=True)  # Format: '08:00'
    status = db.Column(db.Enum(UsageStatus), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    voice_note_url = db.Column(db.String(256), nullable=True)
    
    # Foreign keys
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    resident_id = db.Column(db.Integer, db.ForeignKey('residents.id'))
    caregiver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    inventory_item = relationship('InventoryItem', back_populates='usage_logs')
    resident = relationship('Resident', back_populates='usage_logs')
    caregiver = relationship('User', backref='usage_logs')
    
    def __repr__(self):
        return '<UsageLog \'%s %s\'>' % (self.inventory_item.name if self.inventory_item else 'Unknown', 
                                         self.timestamp)
