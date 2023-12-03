# Use the official Python image as the base image
FROM python:3.10-slim-buster

# Set the working directory
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files to the working directory
COPY . .

# Set the Flask app environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Set the Gunicorn environment variables
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:8080"

# Expose the HTTP and HTTPS ports
EXPOSE 8080

# Start Gunicorn
CMD ["gunicorn", "--timeout", "120", "main:app"]
