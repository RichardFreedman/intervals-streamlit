FROM python:3.11.5-slim AS builder

# Install Poetry and git
RUN apt-get update && apt-get install -y \
    python3-poetry \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/local/bin:${PATH}"
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME="/usr/local" \
    POETRY_CACHE_DIR="/var/cache/pypoetry"

WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Install git-based dependency first
RUN poetry add git+https://github.com/HCDigitalScholarship/intervals.git@intervals_4_streamlit \
    --source git+https://github.com/HCDigitalScholarship/intervals.git@intervals_4_streamlit

# Install remaining dependencies
RUN poetry install --no-interaction --no-ansi

# Final stage
FROM python:3.11.5-slim AS final

WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY . .

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1
# Entry point configuration
ENTRYPOINT ["streamlit", "run", "--server.port=8501", "intervals_streamlit2.py"]