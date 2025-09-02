
# Use a lightweight Python base image
FROM python:3.10-slim

# Install system dependencies required by Chrome
RUN apt-get update && apt-get install -y     wget     curl     unzip     gnupg     libglib2.0-0     libnss3     libgconf-2-4     libfontconfig1     libxss1     libasound2     libxtst6     libx11-xcb1     libxcomposite1     libxdamage1     libxrandr2     libu2f-udev     libvulkan1     fonts-liberation     xdg-utils     && rm -rf /var/lib/apt/lists/*

# Install Chrome (stable version)
RUN curl -Lo /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb &&     apt-get install -y /tmp/chrome.deb &&     rm /tmp/chrome.deb

# Symlink Chrome to /usr/bin to ensure it's in PATH
RUN ln -sf /opt/google/chrome/google-chrome /usr/bin/google-chrome

# Install matching ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $NF}' | cut -d. -f1) &&     DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") &&     curl -Lo /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip" &&     unzip /tmp/chromedriver.zip -d /usr/local/bin/ &&     chmod +x /usr/local/bin/chromedriver &&     rm /tmp/chromedriver.zip

# Symlink ChromeDriver to /usr/bin to ensure it's in PATH
RUN ln -sf /usr/local/bin/chromedriver /usr/bin/chromedriver

# Set environment variables
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PATH="/usr/bin:/usr/local/bin:$PATH"

# Diagnostic step to verify installation
RUN echo "PATH=$PATH" &&     ls -l /usr/bin/google-chrome &&     ls -l /usr/bin/chromedriver &&     which google-chrome &&     which chromedriver &&     google-chrome --version &&     chromedriver --version

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . /app
WORKDIR /app

# Expose port and run the app
EXPOSE 5000
CMD ["python", "app.py"]
