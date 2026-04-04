FROM python:3.10-slim

# Install system dependencies for Playwright/Chromium
RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip \
    libglib2.0-0 libnss3 libfontconfig1 libxss1 libasound2 \
    libxtst6 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libu2f-udev \
    libvulkan1 fonts-liberation xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy app code
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright chromium browser
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

# Expose port and run the app with gunicorn
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "main:app"]
