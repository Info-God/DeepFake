FROM python:3.10-slim

# Prevent Python buffering
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for:
# - opencv
# - reportlab
# - torch
# - pillow
# - solc
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (better Docker caching)
COPY requirements.txt .

# Upgrade pip before install
RUN pip install --upgrade pip

# Install torch CPU properly (important)
RUN pip install torch==2.9.0+cpu torchvision==0.24.0+cpu torchaudio==2.9.0+cpu --index-url https://download.pytorch.org/whl/cpu

# Install remaining requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]