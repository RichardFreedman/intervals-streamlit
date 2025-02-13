FROM python:3.11.5-slim as builder

# Install Poetry and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Poetry environment
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME="/usr/local" \
    POETRY_CACHE_DIR="/var/cache/pypoetry"

# Install dependencies
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi

# Final stage
FROM python:3.11.5-slim

WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY . .

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Entry point configuration
ENTRYPOINT ["streamlit", "run", "--server.port=8501", "intervals_streamlit2.py"]