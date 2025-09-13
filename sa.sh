# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies for Plotly static image generation
RUN apt-get update && apt-get install -y curl jq
RUN apt install chromium -y

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install playwright
RUN playwright install

# Download Plotly topojson files from GitHub
RUN mkdir -p /app/topojson \
	&& cd /app/topojson \
	&& curl -s https://api.github.com/repos/plotly/plotly.js/contents/dist/topojson \
		| jq -r '.[].download_url' \
		| xargs -n 1 curl -O

# Copy the rest of the application code
COPY . .

# Run the scripts
CMD ["/bin/bash", "-c", "python gen.py && python vis.py && python output.py"]
