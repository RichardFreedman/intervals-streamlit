FROM python:3.11.5-slim

# Install Poetry and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Poetry environment
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME="/usr/local" \
    POETRY_CACHE_DIR="/var/cache/pypoetry"

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi
COPY . .

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1
ENTRYPOINT ["streamlit", "run", "--server.port=8501", "--server.address=0.0.0.0", "app.py"]