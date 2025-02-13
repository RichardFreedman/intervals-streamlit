# Stage 1: Builder
FROM python:3.11.5-slim AS builder

# Install essential tools with cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    python3-pip \
    python3-wheel \
    python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Convert TOML dependencies to requirements.txt
COPY pyproject.toml .
RUN python -m pip install tomli[tomlkit] \
    && python -c """
import tomli
import sys

with open('pyproject.toml', 'rb') as f:
    data = tomli.read(f)
    
dependencies = []
for dep in data['project']['dependencies']:
    if isinstance(dep, str):
        dependencies.append(dep)
    elif isinstance(dep, dict):
        name = list(dep.keys())[0]
        extras = dep[name].get('extras', [])
        markers = dep[name].get('markers', '')
        
        req = name
        if extras:
            req += f"[{','.join(extras)}]"
        if markers:
            req += f"; {markers}"
        dependencies.append(req)

with open('requirements.txt', 'w') as f:
    f.write('\\n'.join(dependencies))
""" \
    && rm pyproject.toml

# Clone and install repository
RUN git clone https://github.com/HCDigitalScholarship/intervals.git \
    && cd intervals \
    && git checkout intervals_4_streamlit \
    && python -m pip install .

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final
FROM python:3.11.5-slim AS final

WORKDIR /app
COPY . .

# Expose port for Streamlit
EXPOSE 8501

# Health check endpoint
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_PORT=8501 \
    STREAMLIT_DEBUG=false \
    STREAMLIT_LOG_LEVEL=info

# Entry point configuration
ENTRYPOINT ["streamlit", "run", "--server.port=8501", "intervals_streamlit2.py"]