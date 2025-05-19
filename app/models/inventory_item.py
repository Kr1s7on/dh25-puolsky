from .. import db
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
import enum


class MealRelation(enum.Enum):
    """Enum for relation to meals for InventoryItem."""
    BEFORE_MEAL = 'before_meal'
    WITH_MEAL = 'with_meal'
    AFTER_MEAL = 'after_meal'
    INDEPENDENT = 'independent'


class Frequency(enum.Enum):
    """Enum for frequency of InventoryItem administration."""
    DAILY = 'daily'
    WEEKLY = 'weekly'
    CUSTOM = 'custom'


class InventoryItem(db.Model):
    """
    InventoryItem model for medications and supplies in the care facility.
    """
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(64), nullable=False)  # medication or supply
    quantity = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Float, nullable=False)  # threshold for low stock alert
    daily_usage = db.Column(db.Float, default=0)
    expiration_date = db.Column(db.Date, nullable=True)
    
    # Scheduling fields
    schedule_times = db.Column(db.JSON, nullable=True)  # list of times e.g. ['08:00', '20:00']
    frequency = db.Column(db.Enum(Frequency), nullable=True)
    relation_to_meals = db.Column(db.Enum(MealRelation), nullable=True)
    
    # Foreign keys
    resident_id = db.Column(db.Integer, db.ForeignKey('residents.id'))
    
    # Relationships
    resident = relationship('Resident', back_populates='inventory_items')
    usage_logs = relationship('UsageLog', back_populates='inventory_item')
    
    def __repr__(self):
        return '<InventoryItem \'%s\'>' % self.name
