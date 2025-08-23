FROM python:3.12-slim

# Install system dependencies for PyQt6 and pygame
RUN apt-get update && apt-get install -y \
    libqt6core6 libqt6gui6 libqt6widgets6 \
    libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and app
COPY requirements.txt .
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set display for GUI
##ENV DISPLAY=:0

# Run the app
CMD ["python3", "main.py"]
