# Stage 1: Python application
FROM python:3 AS python-app

# Create and set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY app/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip --no-cache-dir install -r requirements.txt

# Copy the application code
COPY app /app

# Stage 2: PostgreSQL with PostGIS
FROM postgres:16 AS postgresql-postgis

# Install PostGIS extension
RUN apt-get update && \
    apt-get install -y postgis

# Switch back to the python-app stage
FROM python-app AS final

# Set the working directory
WORKDIR /app

# Expose any ports the app is expecting
EXPOSE 5000

# Run the application
ENTRYPOINT ["python"]
CMD ["app.py"]
