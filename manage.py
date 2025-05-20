#!/usr/bin/env python
import os
import subprocess

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell, Server
from redis import Redis
from rq import Connection, Queue, Worker

from app import create_app, db
from app.models import Role, User
from config import Config

# Create Flask application instance - this is required for Gunicorn
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host="0.0.0.0", port=8080))


@manager.command
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def recreate_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    db.drop_all()
    db.create_all()
    db.session.commit()


@manager.command
def add_fake_data():
    """
    Adds comprehensive fake data to the database including realistic resident, caregiver,
    inventory and usage log information.
    """
    from app.models.generate_fake_data import generate_all_fake_data
    generate_all_fake_data()


@manager.command
def setup_dev():
    """Runs the set-up needed for local development."""
    setup_general()


@manager.command
def setup_prod():
    """Runs the set-up needed for production."""
    setup_general()


def setup_general():
    """Runs the set-up needed for both local development and production.
       Also sets up first admin user."""
    Role.insert_roles()
    admin_query = Role.query.filter_by(name='Administrator')
    if admin_query.first() is not None:
        if User.query.filter_by(email=Config.ADMIN_EMAIL).first() is None:
            user = User(
                first_name='Admin',
                last_name='Account',
                password=Config.ADMIN_PASSWORD,
                confirmed=True,
                email=Config.ADMIN_EMAIL)
            db.session.add(user)
            db.session.commit()
            print('Added administrator {}'.format(user.full_name()))


@manager.command
def run_worker():
    """Initializes a slim rq task queue."""
    listen = ['default']
    conn = Redis(
        host=app.config['RQ_DEFAULT_HOST'],
        port=app.config['RQ_DEFAULT_PORT'],
        db=0,
        password=app.config['RQ_DEFAULT_PASSWORD'])

    # Use the same connection for the Flask-RQ
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()


@manager.command
def run_scheduler():
    """Run the RQ scheduler for periodic tasks."""
    import redis
    from rq_scheduler import Scheduler
    from app.tasks.alerts import check_inventory_thresholds, check_missed_doses, check_overdue_doses, send_weekly_digest
    
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379')
    conn = redis.from_url(redis_url)
    scheduler = Scheduler(connection=conn)
    
    # Clear any existing jobs
    for job in scheduler.get_jobs():
        scheduler.cancel(job)
        
    print("Setting up scheduled jobs...")
    
    # 1. Check inventory thresholds hourly
    scheduler.cron(
        "0 * * * *",  # Run at the top of every hour (minute 0)
        func=check_inventory_thresholds,
        repeat=None,
        queue_name='default'
    )
    print("✅ Scheduled hourly inventory threshold checks")
    
    # 2. Check for missed doses every 30 minutes
    scheduler.cron(
        "*/30 * * * *",  # Run every 30 minutes
        func=check_missed_doses,
        repeat=None,
        queue_name='default'
    )
    print("✅ Scheduled missed dose checks every 30 minutes")
    
    # 3. Check for overdue doses every 15 minutes
    scheduler.cron(
        "*/15 * * * *",  # Run every 15 minutes
        func=check_overdue_doses,
        repeat=None,
        queue_name='default'
    )
    print("✅ Scheduled overdue dose checks every 15 minutes")
    
    # 4. Weekly caregiver digest email every Monday at 8:00 AM
    scheduler.cron(
        "0 8 * * 1",  # Run at 8:00 AM every Monday
        func=send_weekly_digest,
        repeat=None,
        queue_name='default'
    )
    print("✅ Scheduled weekly caregiver digest every Monday at 8:00 AM")
    
    print("All jobs scheduled successfully!")
    
    try:
        scheduler.run()
    except KeyboardInterrupt:
        print("Scheduler stopped")


@manager.command
def schedule_jobs():
    """Schedule background jobs for periodic execution."""
    from app.tasks.alerts import (
        check_inventory_thresholds,
        check_missed_doses,
        check_overdue_doses,
        send_weekly_digest
    )
    from datetime import datetime, timedelta
    from rq_scheduler import Scheduler
    
    # Connect to Redis
    conn = Redis(
        host=app.config['RQ_DEFAULT_HOST'],
        port=app.config['RQ_DEFAULT_PORT'],
        db=0,
        password=app.config['RQ_DEFAULT_PASSWORD']
    )
    
    # Create scheduler
    scheduler = Scheduler(connection=conn)
    
    # Clear any existing scheduled jobs
    for job in scheduler.get_jobs():
        scheduler.cancel(job)
    
    # Schedule jobs
    # Check for low inventory items every hour
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=check_inventory_thresholds,
        interval=60*60  # Every 60 minutes
    )
    
    # Check for missed doses every 30 minutes
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=check_missed_doses,
        interval=30*60  # Every 30 minutes
    )
    
    # Check for overdue doses every 15 minutes
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=check_overdue_doses,
        interval=15*60  # Every 15 minutes
    )
    
    # Send weekly digest every Sunday at 8 AM
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=send_weekly_digest,
        interval=7*24*60*60  # Every 7 days
    )
    
    print('Jobs scheduled successfully')


@manager.command
def format():
    """Runs the yapf and isort formatters over the project."""
    isort = 'isort -rc *.py app/'
    yapf = 'yapf -r -i *.py app/'

    print('Running {}'.format(isort))
    subprocess.call(isort, shell=True)

    print('Running {}'.format(yapf))
    subprocess.call(yapf, shell=True)


@manager.command
def add_fake_data():
    """
    Adds fake data for testing DoseDash application.
    """
    from app.models import Role, User, Resident, InventoryItem, UsageLog, MealRelation, Frequency, UsageStatus
    from app.models.user import caregiver_resident_association
    from faker import Faker
    from datetime import datetime, timedelta
    import random
    
    # Setup
    fake = Faker()
    
    # Create roles if they don't exist
    Role.insert_roles()
    
    # Create admin user if they don't exist
    if User.query.filter_by(email=Config.ADMIN_EMAIL).first() is None:
        user = User(
            first_name='Admin',
            last_name='User',
            email=Config.ADMIN_EMAIL,
            password=Config.ADMIN_PASSWORD,
            confirmed=True)
        db.session.add(user)
        db.session.commit()
        print('Added admin user')
    
    # Add fake caregivers
    num_caregivers = 5
    for i in range(num_caregivers):
        email = f'caregiver{i+1}@example.com'
        if User.query.filter_by(email=email).first() is None:
            user = User(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=email,
                password='password',
                confirmed=True,
                role=Role.query.filter_by(name='Caregiver').first()
            )
            db.session.add(user)
            db.session.commit()
            print(f'Added caregiver: {user.full_name()}')
    
    caregivers = User.query.filter_by(role_id=Role.query.filter_by(name='Caregiver').first().id).all()
    
    # Add fake residents
    num_residents = 10
    for i in range(num_residents):
        name = fake.name()
        if Resident.query.filter_by(name=name).first() is None:
            resident = Resident(
                name=name,
                date_of_birth=fake.date_of_birth(minimum_age=65, maximum_age=95),
                photo_url=None  # Would use fake.image_url() in a real app
            )
            db.session.add(resident)
            db.session.commit()
            
            # Assign 1-3 random caregivers to each resident
            for caregiver in random.sample(caregivers, random.randint(1, min(3, len(caregivers)))):
                caregiver.residents.append(resident)
            
            db.session.commit()
            print(f'Added resident: {resident.name}')
    
    # Add inventory items for each resident
    residents = Resident.query.all()
    medication_types = ['Pill', 'Liquid', 'Injection', 'Topical', 'Inhaler']
    supply_types = ['Bandage', 'Gloves', 'Syringe', 'Catheter', 'Dressing']
    
    for resident in residents:
        # Add 2-5 medications
        for _ in range(random.randint(2, 5)):
            item = InventoryItem(
                name=fake.word() + ' ' + random.choice(['Tablet', 'Syrup', 'Capsule']),
                type='medication',
                quantity=random.randint(10, 50),
                threshold=random.randint(5, 10),
                daily_usage=random.uniform(0.5, 3),
                expiration_date=datetime.now() + timedelta(days=random.randint(30, 365)),
                schedule_times=['08:00', '20:00'] if random.random() > 0.5 else ['08:00', '12:00', '20:00'],
                frequency=random.choice(list(Frequency)),
                relation_to_meals=random.choice(list(MealRelation)),
                resident_id=resident.id
            )
            db.session.add(item)
        
        # Add 1-3 supplies
        for _ in range(random.randint(1, 3)):
            item = InventoryItem(
                name=random.choice(supply_types) + ' ' + fake.word(),
                type='supply',
                quantity=random.randint(5, 100),
                threshold=random.randint(3, 20),
                daily_usage=random.uniform(0.1, 2),
                expiration_date=datetime.now() + timedelta(days=random.randint(60, 730)),
                resident_id=resident.id
            )
            db.session.add(item)
    
    db.session.commit()
    print('Added inventory items for all residents')
    
    # Add usage logs
    inventory_items = InventoryItem.query.all()
    for item in inventory_items:
        # Generate 0-10 usage logs over the past week
        for _ in range(random.randint(0, 10)):
            timestamp = datetime.now() - timedelta(days=random.randint(0, 7))
            caregiver = random.choice(item.resident.caregivers.all() if item.resident.caregivers.count() > 0 else caregivers)
            
            log = UsageLog(
                timestamp=timestamp,
                scheduled_time=random.choice(item.schedule_times) if item.schedule_times else None,
                status=random.choice(list(UsageStatus)),
                notes=fake.sentence() if random.random() > 0.7 else None,
                voice_note_url=None,
                inventory_item_id=item.id,
                resident_id=item.resident_id,
                caregiver_id=caregiver.id
            )
            db.session.add(log)
    
    db.session.commit()
    print('Added usage logs')
    
    print('Fake data generation complete!')


if __name__ == '__main__':
    manager.run()
