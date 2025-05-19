#!/usr/bin/env bash

echo "Starting DoseDash application..."

source env/bin/activate

# Run the application
python3 manage.py runserver --port 8080
