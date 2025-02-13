FROM python:3.11.5-slim

# Phase 1: Base Setup
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME="/usr/local" \
    POETRY_CACHE_DIR="/var/cache/pypoetry"

WORKDIR /app

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Phase 2: Dependency Management
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi

# Phase 3: Application Setup
COPY . .

# Configure Streamlit
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Phase 4: Finalization
ENTRYPOINT ["streamlit", "run", "--server.port=8501", "--server.address=0.0.0.0", "app.py"]