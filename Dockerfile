FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install project dependencies from pyproject.toml
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    "uvicorn[standard]>=0.24.0" \
    pydantic>=2.0.0 \
    pydantic-settings>=2.0.0 \
    openai>=1.0.0 \
    finnhub-python>=2.4.0 \
    python-multipart>=0.0.6 \
    pytest>=7.4.0 \
    pytest-asyncio>=0.21.0 \
    ruff>=0.1.0

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
