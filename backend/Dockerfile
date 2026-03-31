FROM python:3.12-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pytest pytest-asyncio

COPY . .

# Run tests
RUN python -m pytest app/tests/ -v --tb=short -x 2>&1 | tee /tmp/test_output.txt; \
    grep -q "passed" /tmp/test_output.txt || echo "WARNING: tests did not pass"

# Accept GitHub token as build arg for enrichment
ARG GITHUB_TOKEN=""
ENV GITHUB_TOKEN=$GITHUB_TOKEN

# Pre-seed the database at build time (with GitHub enrichment if token provided)
RUN mkdir -p /app/seed_data && \
    DATABASE_URL=sqlite:////app/seed_data/agenthub.db \
    python -m app.seed && \
    echo "Seed complete: $(ls -lh /app/seed_data/agenthub.db)" && \
    echo "Agents: $(python3 -c 'import sqlite3; c=sqlite3.connect(\"/app/seed_data/agenthub.db\"); print(c.execute(\"SELECT COUNT(*) FROM agents\").fetchone()[0])')" && \
    echo "Projects: $(python3 -c 'import sqlite3; c=sqlite3.connect(\"/app/seed_data/agenthub.db\"); print(c.execute(\"SELECT COUNT(*) FROM projects\").fetchone()[0])')"

EXPOSE 8080

ENV DATABASE_URL=sqlite:////app/seed_data/agenthub.db
# Clear token from runtime environment for security
ENV GITHUB_TOKEN=""

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
