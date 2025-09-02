# Use an official Python base image
FROM python:3.10-slim

# Install system dependencies required by Chrome
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libasound2 \
    libxtst6 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libu2f-udev \
    libvulkan1 \
    fonts-liberation \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Download Chrome for Testing
RUN mkdir -p /opt/chrome && \
    curl -Lo /tmp/chrome.zip https://storage.googleapis.com/chrome-for-testing-public/139.0.7258.154/linux64/chrome-linux64.zip && \
    unzip /tmp/chrome.zip -d /opt/chrome && \
    mv /opt/chrome/chrome-linux64 /opt/chrome/chrome && \
    ln -s /opt/chrome/chrome/chrome /usr/bin/google-chrome

# Set environment variable for Chrome binary
ENV CHROME_BIN=/usr/bin/google-chrome

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . /app
WORKDIR /app

# Expose port and run the app
EXPOSE 5000
CMD ["python", "app.py"]
