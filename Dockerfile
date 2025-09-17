# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies for Plotly static image generation
RUN apt-get update && apt-get install -y curl jq

# Download Plotly.js locally for offline use
RUN mkdir -p /app/assets \
    && cd /app/assets \
    && curl -o plotly.min.js https://cdn.plot.ly/plotly-latest.min.js

# Download Plotly topojson files from GitHub
RUN mkdir -p /app/topojson \
	&& cd /app/topojson \
	&& curl -s https://api.github.com/repos/plotly/plotly.js/contents/dist/topojson \
		| jq -r '.[].download_url' \
		| xargs -n 1 curl -O

# Download geojson files from GitHub
RUN mkdir -p /app/geojson \
	&& cd /app/geojson \
	&& curl -s https://api.github.com/repos/nvkelso/natural-earth-vector/contents/geojson \
		| jq -r '.[].download_url' \
		| xargs -n 1 curl -O

# Download all JSON files from eric.clst.org
RUN mkdir -p /app/ericclst \
    && cd /app/ericclst \
    && curl -s https://eric.clst.org/assets/wiki/uploads/Stuff/ \
    | grep -o '"[^"]\+\.json"' | sed 's/"//g' \
    | while read file; do \
        curl -O "https://eric.clst.org/assets/wiki/uploads/Stuff/$file"; \
    done

# Download GeoJSON files for data generation (offline usage)
RUN cd /app \
    && curl -o german_districts.geo.json \
       https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/4_kreise/4_niedrig.geo.json

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-dejavu fonts-liberation \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Install Playwright web-driver and an intergrated chromium browser into Playwright driver
RUN playwright install
RUN playwright install chromium
RUN playwright install-deps chromium

# If you like, set the binary path via env (optional)
ENV CHROMIUM_BIN=/usr/bin/chromium

# Copy the rest of the application code
COPY . .

# Run the scripts
CMD ["/bin/bash", "-c", "python gen.py && python vis.py"]
