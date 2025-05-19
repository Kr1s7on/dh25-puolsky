#!/usr/bin/env bash

echo "Starting database reset and fake data generation..."

# Step 1: Recreate the database
echo "Step 1: Recreating database..."
python3 manage.py recreate_db
if [ $? -ne 0 ]; then
    echo "Error: Failed to recreate database"
    exit 1
fi

# Step 2: Setup development environment (creates admin user and roles)
echo "Step 2: Setting up development environment..."
python3 manage.py setup_dev
if [ $? -ne 0 ]; then
    echo "Error: Failed to setup development environment"
    exit 1
fi

# Step 3: Generate comprehensive fake data
echo "Step 3: Generating comprehensive fake data..."
python3 generate_fake_data.py
if [ $? -ne 0 ]; then
    echo "Error: Failed to generate fake data"
    exit 1
fi

echo "Database reset and fake data generation completed successfully!"
