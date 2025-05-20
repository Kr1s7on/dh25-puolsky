#!/usr/bin/env python
# filepath: /Users/puolsky/Downloads/GitHub/dh25-puolsky/scheduler.py
import os
import redis
from rq import Worker, Queue, Connection
from flask import Flask
from rq.job import Job
from flask_rq import RQ
from rq_scheduler import Scheduler
import datetime

from app import create_app, db
from app.tasks.alerts import check_inventory_thresholds, check_missed_doses, check_overdue_doses, send_weekly_digest
from app.tasks.reports import send_weekly_reports

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

def initialize_scheduler():
    """Set up the scheduler with periodic jobs"""
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
    
    # 5. Weekly reports for all residents every Monday at 9:00 AM
    scheduler.cron(
        "0 9 * * 1",  # Run at 9:00 AM every Monday
        func=send_weekly_reports,
        repeat=None,
        queue_name='default'
    )
    print("✅ Scheduled weekly reports generation every Monday at 9:00 AM")
    
    print("All jobs scheduled successfully!")
    return scheduler

if __name__ == '__main__':
    with app.app_context():
        initialize_scheduler()
        
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379')
    redis_connection = redis.from_url(redis_url)
    
    with Connection(redis_connection):
        worker = Worker(['default'])
        worker.work()
