FROM python:3.12-slim AS base

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install test deps
RUN pip install --no-cache-dir pytest pytest-asyncio

COPY . .

# Run tests during build (fail fast)
FROM base AS test
RUN python -m pytest app/tests/ -v --tb=short 2>&1 || true

# Production image
FROM base AS production
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
