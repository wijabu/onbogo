
# Use a lightweight Python base image
FROM python:3.10-slim

# Install system dependencies and Chromium
RUN apt-get update && apt-get install -y     wget     curl     unzip     gnupg     libglib2.0-0     libnss3     libgconf-2-4     libfontconfig1     libxss1     libasound2     libxtst6     libx11-xcb1     libxcomposite1     libxdamage1     libxrandr2     libu2f-udev     libvulkan1     fonts-liberation     xdg-utils     chromium     chromium-driver     && rm -rf /var/lib/apt/lists/*

# Symlink Chromium to google-chrome so Selenium can find it
RUN ln -sf $(which chromium || which chromium-browser) /usr/bin/google-chrome

# Symlink chromedriver to /usr/bin/chromedriver
RUN ln -sf $(which chromedriver) /usr/bin/chromedriver

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
