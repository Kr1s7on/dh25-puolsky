import enum
from .. import db
from datetime import datetime

class NotificationType(enum.Enum):
    LOW_STOCK = 'low_stock'
    MISSED_DOSE = 'missed_dose'
    OVERDUE_DOSE = 'overdue_dose'

class NotificationStatus(enum.Enum):
    UNREAD = 'unread'
    READ = 'read'
    SNOOZED = 'snoozed'
    ACKNOWLEDGED = 'acknowledged'

class Notification(db.Model):
    """
    Notification model for alerts to caregivers.
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    message = db.Column(db.String(256), nullable=False)
    status = db.Column(db.Enum(NotificationStatus), default=NotificationStatus.UNREAD)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    snoozed_until = db.Column(db.DateTime, nullable=True)
    
    # Foreign keys for related entities
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resident_id = db.Column(db.Integer, db.ForeignKey('residents.id'), nullable=True)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    resident = db.relationship('Resident', backref='notifications')
    inventory_item = db.relationship('InventoryItem', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.type.value} - {self.status.value}>'
    
    def mark_as_read(self):
        self.status = NotificationStatus.READ
        self.read_at = datetime.utcnow()
        
    def snooze(self, hours=1):
        self.status = NotificationStatus.SNOOZED
        self.snoozed_until = datetime.utcnow() + datetime.timedelta(hours=hours)
        
    def acknowledge(self):
        self.status = NotificationStatus.ACKNOWLEDGED
        self.read_at = datetime.utcnow()
