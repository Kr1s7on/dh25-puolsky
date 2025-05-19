#!/usr/bin/env python
# filepath: /Users/puolsky/Downloads/GitHub/dh25-puolsky/test_tasks.py

import os
from app import create_app, db
from app.tasks.alerts import (
    check_inventory_thresholds, 
    check_missed_doses, 
    check_overdue_doses, 
    send_weekly_digest
)
from flask_rq import get_queue

def test_tasks():
    """Test the various background tasks manually."""
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    
    with app.app_context():
        print("Starting tests...")
        
        # Test 1: Direct task execution (synchronous)
        print("\n---- Test 1: Direct Task Execution ----")
        
        print("Running check_inventory_thresholds...")
        check_inventory_thresholds()
        print("✅ Completed inventory threshold check")
        
        print("Running check_missed_doses...")
        check_missed_doses()
        print("✅ Completed missed doses check")
        
        print("Running check_overdue_doses...")
        check_overdue_doses()
        print("✅ Completed overdue doses check")
        
        # Test 2: Queue tasks for background processing
        print("\n---- Test 2: Queue Tasks for Background Processing ----")
        queue = get_queue()
        
        print("Queueing inventory threshold check...")
        job1 = queue.enqueue(check_inventory_thresholds)
        print(f"✅ Task queued with job ID: {job1.id}")
        
        print("Queueing missed doses check...")
        job2 = queue.enqueue(check_missed_doses)
        print(f"✅ Task queued with job ID: {job2.id}")
        
        print("Queueing overdue doses check...")
        job3 = queue.enqueue(check_overdue_doses)
        print(f"✅ Task queued with job ID: {job3.id}")
        
        print("Queueing weekly digest...")
        job4 = queue.enqueue(send_weekly_digest)
        print(f"✅ Task queued with job ID: {job4.id}")
        
        print("\nAll tests completed. Check your worker terminal for job execution logs.")

if __name__ == '__main__':
    test_tasks()
