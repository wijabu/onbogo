# Use a lightweight Python base image
FROM python:3.10-slim

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip \
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 libxss1 libasound2 \
    libxtst6 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libu2f-udev \
    libvulkan1 fonts-liberation xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . /app
WORKDIR /app

# Expose port and run the app
EXPOSE 5000
CMD ["python", "app.py"]
