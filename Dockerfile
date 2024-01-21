# Use the official Python image as the base image
FROM python:3.11-slim
# FROM --platform=linux/amd64,linux/arm64 python:3.11-slim

# Set the working directory
WORKDIR /code

# Copy the requirements file to the working directory
COPY requirements.txt .

RUN python -m pip install --upgrade pip

# Install the required packages
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files to the working directory
COPY . .

# Set the Flask app environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Set the Gunicorn environment variables
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:80"

# Expose the HTTP and HTTPS ports
EXPOSE 80

# Start Gunicorn
CMD ["gunicorn", "--timeout", "120", "main:app"]
