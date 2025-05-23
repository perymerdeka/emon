# Use the official Python 3.12 Alpine image as a base
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install build dependencies, system libraries, and netcat
# Using --no-cache-dir reduces image size
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev mariadb-dev \
    && apk add --no-cache netcat-openbsd redis curl \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Copy the rest of the application code into the container
COPY . .

# Create directory for Redis socket (if needed)
RUN mkdir -p /var/run/redis

# Expose the port the app runs on
EXPOSE 8000

# Add healthcheck for the application
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Command to run the application using Uvicorn
# We use the non-reloading version for production
CMD ["uvicorn", "manage:app", "--host", "0.0.0.0", "--port", "8000"]
