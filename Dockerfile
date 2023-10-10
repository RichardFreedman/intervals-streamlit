# app/Dockerfile
FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip install poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --no-dev
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "intervals_streamlit2.py", "--server.port=8501", "--server.address=0.0.0.0"]