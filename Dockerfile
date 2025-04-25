# Use the official Python 3.12 Alpine image as a base
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install build dependencies, system libraries, and netcat
# Using --no-cache-dir reduces image size
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev mariadb-dev \
    && apk add --no-cache netcat-openbsd \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8000



# Command to run the application using Uvicorn
# We use the non-reloading version for production
CMD ["uvicorn", "manage:app", "--host", "0.0.0.0", "--port", "8000"]
