# Use a lightweight, official Python image optimized for enterprise cloud runtimes
FROM python:3.12-slim

# Set strict system security boundaries inside the container
WORKDIR /app

# Expose system tools required to compile standard C extensions safely
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy your modern, pinned dependency configurations 
COPY requirements.txt .

# Install dependencies into an isolated, clean global environment layer
RUN pip install --no-cache-dir -r requirements.txt

# Copy your core application assets into the container workspace
COPY app.py .

# Expose port 7860 (Haug Face Spaces routes traffic through port 7860, not 8501)
EXPOSE 7860

# Force Streamlit to listen cleanly on the correct federal network mapping
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
