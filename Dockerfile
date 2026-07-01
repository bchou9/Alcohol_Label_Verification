# Use an official lightweight Python base image
FROM python:3.12-slim

# Configure system requirements safely (software-properties-common removed)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face security mandate: Create and configure an isolated non-root user account
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirement configurations with appropriate non-root ownership permissions
COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application script assets into the isolated workspace directory 
COPY --chown=user app.py app.py

# Force Streamlit to route explicitly over port 7860 under a non-root context
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
