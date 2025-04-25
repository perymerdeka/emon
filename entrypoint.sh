#!/bin/sh
# entrypoint.sh
echo "Checking database connection..."
while ! nc -z $DB_HOST $DB_PORT; do 
    sleep 0.1
done
echo "Database is up!"
echo "Running migrations..."
# Run migrations
alembic upgrade head