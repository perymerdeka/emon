# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Prevent python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure python output is sent straight to terminal (useful for logs)
ENV PYTHONUNBUFFERED 1

# Install system dependencies if needed (e.g., for psycopg2)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install pip requirements
# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
# Use the specific requirements provided by the user
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable (optional, can be overridden)
# ENV DATABASE_URL sqlite:///./database.db

# Run main.py when the container launches
# Use the command from main.py but without reload for the image
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
