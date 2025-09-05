# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies for Plotly static image generation
RUN apt update 
RUN apt install chromium -y

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Run the scripts
CMD ["/bin/bash", "-c", "python gen.py && python vis.py"]
