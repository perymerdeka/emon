#!/bin/sh
# Entrypoint script for Docker container

# Wait for database to be ready
echo "Checking database connection..."
while ! nc -z $DB_HOST $DB_PORT; do 
    sleep 0.1
done
echo "Database is up!"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start application
echo "Starting application..."
exec uvicorn manage:app --host 0.0.0.0 --port 8000
