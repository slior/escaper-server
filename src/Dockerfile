# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies required for playsound (GStreamer backend)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-gi \
    gir1.2-gstreamer-1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-tools \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
# Ensure audio and logs directories exist within the image context although they will be mounted
COPY . .
RUN mkdir -p /app/audio /app/logs

# Make port 80 available to the world outside this container (if needed, not currently used)
# EXPOSE 80 

# Define environment variables (can be overridden by docker-compose)
ENV PYTHONUNBUFFERED=1
ENV MQTT_BROKER_HOST=mqtt_broker
ENV MQTT_BROKER_PORT=1883

# Run server.py when the container launches
CMD ["python", "server.py"] 