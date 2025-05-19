#!/usr/bin/env python
# filepath: /Users/puolsky/Downloads/GitHub/dh25-puolsky/worker.py
import os
import redis
from rq import Worker, Queue, Connection

from app import create_app

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# Initialize Flask-RQ worker
redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379')

if __name__ == '__main__':
    with Connection(redis.from_url(redis_url)):
        worker = Worker(['default', 'high', 'low'])
        worker.work()
