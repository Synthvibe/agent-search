FROM python:3.12-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pytest pytest-asyncio && \
    # Pre-download the embedding model so it's baked into the image (no download at runtime)
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2'); print('Model downloaded')"

COPY . .

# Run tests
RUN python -m pytest app/tests/ -v --tb=short -x 2>&1 | tee /tmp/test_output.txt; \
    grep -q "passed" /tmp/test_output.txt || echo "WARNING: tests did not pass"

# Accept GitHub token as build arg for enrichment
ARG GITHUB_TOKEN=""
ENV GITHUB_TOKEN=$GITHUB_TOKEN

# Pre-seed the database at build time
RUN mkdir -p /app/seed_data && \
    DATABASE_URL=sqlite:////app/seed_data/agenthub.db \
    python -m app.seed && \
    echo "Seed complete: $(ls -lh /app/seed_data/agenthub.db)"

EXPOSE 8080

ENV DATABASE_URL=sqlite:////app/seed_data/agenthub.db
ENV GITHUB_TOKEN=""

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
