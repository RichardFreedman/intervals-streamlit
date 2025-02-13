FROM python:3.11.5-slim as builder

FROM python:3.11.5-slim as builder

# Install Poetry and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:${PATH}"
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME="/root/.local" \
    POETRY_CACHE_DIR="/var/cache/pypoetry"

WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Verify git repository access
RUN git ls-remote https://github.com/HCDigitalScholarship/intervals.git

# Install git-based dependency with verification
RUN poetry add git+https://github.com/HCDigitalScholarship/intervals.git@intervals_4_streamlit \
    --source git+https://github.com/HCDigitalScholarship/intervals.git@intervals_4_streamlit

# Verify installation
RUN poetry show crim-intervals

# Install remaining dependencies
RUN poetry install --no-interaction --no-ansi

# Final stage
FROM python:3.11.5-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Entry point configuration
ENTRYPOINT ["streamlit", "run", "--server.port=8501", "intervals_streamlit2.py"]