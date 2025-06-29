# Multi-stage build to reduce final image size
FROM python:3.9-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Final stage - use slim image
FROM python:3.9-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Generate ESCO data and embeddings if not present (only if data files don't exist)
RUN if [ ! -f "data/esco_skills.json" ] && [ -f "convert_esco_to_json.py" ]; then \
        python convert_esco_to_json.py; \
    fi

RUN if [ ! -f "data/esco_embeddings.npy" ] && [ -f "generate_embeddings.py" ]; then \
        python generate_embeddings.py; \
    fi

# Clean up unnecessary files
RUN find /app -name "*.pyc" -delete && \
    find /app -name "__pycache__" -type d -delete && \
    find /app -name "*.pyo" -delete && \
    find /app -name "*.pyd" -delete && \
    find /app -name ".coverage" -delete && \
    find /app -name "*.log" -delete

# Remove unnecessary Python packages to reduce size
RUN pip uninstall -y setuptools pip && \
    rm -rf /root/.cache/pip

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Start the API server
CMD ["uvicorn", "employment_match.API:app", "--host", "0.0.0.0", "--port", "8080"] 