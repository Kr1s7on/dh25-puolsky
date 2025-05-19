#!/usr/bin/env python

import os
import sys
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.exc import IntegrityError

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Role, Permission, Resident
from app.models.inventory_item import InventoryItem, MealRelation, Frequency
from app.models.usage_log import UsageLog, UsageStatus

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
faker = Faker()


def generate_fake_residents(count=10):
    """Generate fake residents."""
    print(f"Generating {count} fake residents...")
    
    with app.app_context():
        for i in range(count):
            resident = Resident(
                name=f"{faker.first_name()} {faker.last_name()}",
                date_of_birth=faker.date_of_birth(minimum_age=60, maximum_age=95),
                photo_url=f"https://randomuser.me/api/portraits/{'men' if random.choice([True, False]) else 'women'}/{random.randint(1, 99)}.jpg"
            )
            db.session.add(resident)
            try:
                db.session.commit()
                print(f"Created resident: {resident.name}")
            except IntegrityError:
                db.session.rollback()
                print(f"Error creating resident {i+1}")


def generate_fake_caregivers(count=5):
    """Generate fake caregivers."""
    print(f"Generating {count} fake caregivers...")
    
    with app.app_context():
        caregiver_role = Role.query.filter_by(permissions=Permission.CAREGIVER).first()
        if not caregiver_role:
            print("Caregiver role not found. Creating it...")
            caregiver_role = Role(name='Caregiver', 
                                  permissions=Permission.GENERAL | Permission.CAREGIVER,
                                  index='caregiver')
            db.session.add(caregiver_role)
            db.session.commit()
        
        for i in range(count):
            phone = f"+1{faker.msisdn()[3:13]}"  # Generate US phone format
            
            caregiver = User(
                first_name=faker.first_name(),
                last_name=faker.last_name(),
                email=faker.email(),
                password="password",  # All test users get the same password for easy testing
                confirmed=True,
                role=caregiver_role,
                phone_number=phone,
                sms_opt_in=random.choice([True, False])
            )
            db.session.add(caregiver)
            try:
                db.session.commit()
                print(f"Created caregiver: {caregiver.full_name()}")
            except IntegrityError:
                db.session.rollback()
                print(f"Error creating caregiver {i+1}")


def assign_residents_to_caregivers():
    """Assign residents to caregivers."""
    print("Assigning residents to caregivers...")
    
    with app.app_context():
        residents = Resident.query.all()
        caregivers = User.query.filter(User.role.has(permissions=Permission.CAREGIVER)).all()
        
        if not residents:
            print("No residents found. Please generate residents first.")
            return
        
        if not caregivers:
            print("No caregivers found. Please generate caregivers first.")
            return
        
        # Each resident gets assigned to 1-3 caregivers
        for resident in residents:
            num_caregivers = random.randint(1, min(3, len(caregivers)))
            selected_caregivers = random.sample(caregivers, num_caregivers)
            
            for caregiver in selected_caregivers:
                caregiver.residents.append(resident)
            
            try:
                db.session.commit()
                print(f"Assigned {resident.name} to {num_caregivers} caregivers")
            except IntegrityError:
                db.session.rollback()
                print(f"Error assigning caregivers to {resident.name}")


def generate_fake_inventory_items():
    """Generate realistic inventory items for residents."""
    print("Generating inventory items...")
    
    with app.app_context():
        # Common medications for elderly care
        medications = [
            {"name": "Lisinopril", "type": "medication", "daily_usage": 1, "is_scheduled": True},
            {"name": "Metformin", "type": "medication", "daily_usage": 2, "is_scheduled": True},
            {"name": "Amlodipine", "type": "medication", "daily_usage": 1, "is_scheduled": True},
            {"name": "Levothyroxine", "type": "medication", "daily_usage": 1, "is_scheduled": True},
            {"name": "Atorvastatin", "type": "medication", "daily_usage": 1, "is_scheduled": True},
            {"name": "Aspirin", "type": "medication", "daily_usage": 1, "is_scheduled": True},
            {"name": "Metoprolol", "type": "medication", "daily_usage": 2, "is_scheduled": True},
            {"name": "Furosemide", "type": "medication", "daily_usage": 1, "is_scheduled": True},
            {"name": "Omeprazole", "type": "medication", "daily_usage": 1, "is_scheduled": True},
            {"name": "Gabapentin", "type": "medication", "daily_usage": 3, "is_scheduled": True},
            {"name": "Vitamin D", "type": "supplement", "daily_usage": 1, "is_scheduled": True},
            {"name": "Calcium", "type": "supplement", "daily_usage": 2, "is_scheduled": True},
        ]
        
        # Common supplies
        supplies = [
            {"name": "Adult Diapers", "type": "supply", "daily_usage": 3, "is_scheduled": False},
            {"name": "Wet Wipes", "type": "supply", "daily_usage": 10, "is_scheduled": False},
            {"name": "Gauze", "type": "supply", "daily_usage": 2, "is_scheduled": False},
            {"name": "Bandages", "type": "supply", "daily_usage": 3, "is_scheduled": False},
            {"name": "Antiseptic Solution", "type": "supply", "daily_usage": 0.5, "is_scheduled": False},
            {"name": "Moisturizer", "type": "supply", "daily_usage": 1, "is_scheduled": False},
            {"name": "Gloves", "type": "supply", "daily_usage": 4, "is_scheduled": False},
        ]
        
        residents = Resident.query.all()
        if not residents:
            print("No residents found. Please generate residents first.")
            return
        
        for resident in residents:
            # Each resident gets 2-5 medications and 1-3 supplies
            num_medications = random.randint(2, 5)
            num_supplies = random.randint(1, 3)
            
            selected_medications = random.sample(medications, num_medications)
            selected_supplies = random.sample(supplies, num_supplies)
            
            # Process medications
            for med in selected_medications:
                # Calculate realistic quantity and threshold
                daily_usage = med["daily_usage"]
                # Keep 2-4 weeks of supply
                days_supply = random.randint(14, 28)
                quantity = daily_usage * days_supply
                # Set threshold to 7-10 days supply
                threshold = daily_usage * random.randint(7, 10)
                
                # Create schedule times for medications
                schedule_times = []
                if med["is_scheduled"]:
                    if daily_usage == 1:
                        schedule_times = [f"{random.randint(7, 9):02d}:00"]  # Morning
                    elif daily_usage == 2:
                        schedule_times = [f"{random.randint(7, 9):02d}:00", f"{random.randint(17, 19):02d}:00"]  # Morning and evening
                    elif daily_usage == 3:
                        schedule_times = [f"{random.randint(7, 9):02d}:00", f"{random.randint(11, 13):02d}:00", f"{random.randint(17, 19):02d}:00"]  # Morning, noon, evening
                
                # Set expiration date (3-12 months in the future)
                expiration_days = random.randint(90, 365)
                expiration_date = datetime.now() + timedelta(days=expiration_days)
                
                # Create the inventory item
                item = InventoryItem(
                    name=med["name"],
                    type=med["type"],
                    quantity=quantity,
                    threshold=threshold,
                    daily_usage=daily_usage,
                    expiration_date=expiration_date,
                    schedule_times=schedule_times,
                    frequency=Frequency.DAILY if med["is_scheduled"] else None,
                    relation_to_meals=random.choice(list(MealRelation)) if med["is_scheduled"] else None,
                    resident=resident
                )
                db.session.add(item)
            
            # Process supplies
            for supply in selected_supplies:
                # Calculate realistic quantity and threshold
                daily_usage = supply["daily_usage"]
                # Keep 2-3 weeks of supply
                days_supply = random.randint(14, 21)
                quantity = daily_usage * days_supply
                # Set threshold to 5-7 days supply
                threshold = daily_usage * random.randint(5, 7)
                
                # Create the inventory item (supplies don't have schedules)
                item = InventoryItem(
                    name=supply["name"],
                    type=supply["type"],
                    quantity=quantity,
                    threshold=threshold,
                    daily_usage=daily_usage,
                    resident=resident
                )
                db.session.add(item)
        
        try:
            db.session.commit()
            print(f"Created inventory items for {len(residents)} residents")
        except IntegrityError as e:
            db.session.rollback()
            print(f"Error creating inventory items: {e}")


def generate_usage_logs():
    """Generate usage logs for the past week."""
    print("Generating usage logs for the past week...")
    
    with app.app_context():
        # Get all scheduled inventory items
        scheduled_items = InventoryItem.query.filter(InventoryItem.schedule_times.isnot(None)).all()
        
        if not scheduled_items:
            print("No scheduled items found.")
            return
        
        # Generate logs for the past 7 days
        for day_offset in range(7, 0, -1):
            log_date = datetime.now() - timedelta(days=day_offset)
            
            for item in scheduled_items:
                if not item.schedule_times:
                    continue
                    
                resident = item.resident
                caregivers = list(resident.caregivers)
                
                if not caregivers:
                    continue
                    
                # For each scheduled time
                for scheduled_time in item.schedule_times:
                    # Parse the scheduled time (format: "HH:MM")
                    hour, minute = map(int, scheduled_time.split(':'))
                    scheduled_datetime = datetime(
                        log_date.year, log_date.month, log_date.day, 
                        hour, minute
                    )
                    
                    # 85% chance of medication being taken, 15% chance of being missed
                    status = UsageStatus.TAKEN if random.random() < 0.85 else UsageStatus.MISSED
                    
                    # If taken, reduce quantity
                    if status == UsageStatus.TAKEN:
                        # Determine how much was used (usually 1 unit per dose)
                        used_quantity = 1
                        item.quantity -= used_quantity
                    
                    # Create a usage log
                    log = UsageLog(
                        timestamp=scheduled_datetime,
                        scheduled_time=scheduled_time,
                        status=status,
                        notes=f"{'Given as scheduled' if status == UsageStatus.TAKEN else 'Missed dose'}" if random.random() < 0.3 else None,
                        inventory_item=item,
                        resident=resident,
                        caregiver=random.choice(caregivers)
                    )
                    
                    db.session.add(log)
            
            try:
                db.session.commit()
                print(f"Created usage logs for {log_date.strftime('%Y-%m-%d')}")
            except IntegrityError:
                db.session.rollback()
                print(f"Error creating usage logs for {log_date.strftime('%Y-%m-%d')}")
                    

def generate_all_fake_data():
    """Generate all fake data in the correct order."""
    generate_fake_residents(count=8)
    generate_fake_caregivers(count=5)
    assign_residents_to_caregivers()
    generate_fake_inventory_items()
    generate_usage_logs()
    
    print("All fake data generation complete!")


if __name__ == '__main__':
    generate_all_fake_data()
