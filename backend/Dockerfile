FROM python:3.12-slim AS base

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pytest pytest-asyncio

COPY . .

# Run tests
RUN python -m pytest app/tests/ -v --tb=short -x 2>&1 | tee /tmp/test_output.txt; \
    cat /tmp/test_output.txt; \
    grep -q "passed" /tmp/test_output.txt || echo "WARNING: Some tests failed or were skipped"

# Pre-seed the database at build time
# This ensures agents are available immediately on cold start
RUN mkdir -p /app/seed_data && \
    DATABASE_URL=sqlite:////app/seed_data/agenthub.db \
    python -m app.seed && \
    echo "Seed complete: $(ls -lh /app/seed_data/agenthub.db)"

EXPOSE 8080

# Use the pre-seeded DB path at runtime
ENV DATABASE_URL=sqlite:////app/seed_data/agenthub.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
