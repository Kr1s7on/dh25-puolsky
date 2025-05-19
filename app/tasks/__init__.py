from flask_rq import get_queue

def init_app(app):
    """Initialize background job queues."""
    app.config.setdefault('RQ_REDIS_URL', 'redis://localhost:6379')
    app.config.setdefault('RQ_QUEUES', ['default', 'high', 'low'])
    
    @app.cli.command('run_scheduler')
    def run_scheduler_command():
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
