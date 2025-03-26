# Stage 1: Base image with system dependencies
FROM python:3.13-slim-bookworm AS base-deps

# Add version pinning for better reproducibility
RUN apt-get update && apt-get install -y \
  build-essential \
  gcc \
  g++ \
  git \
  && rm -rf /var/lib/apt/lists/*

# Set Git user and email
RUN git config --global user.email "agent@codepanda.ai" && \
  git config --global user.name "CodePanda Agent"

# Stage 2: Python dependencies
FROM base-deps AS python-deps

WORKDIR /app

# Add pip configuration for better security
RUN pip install --no-cache-dir poetry && \
  poetry config virtualenvs.create false && \
  poetry config installer.max-workers 4

# Copy dependency files only
COPY pyproject.toml poetry.lock ./

# Replace chromadb with chromadb-client in dependencies and update lock file
RUN sed -i 's/chromadb/chromadb-client/' pyproject.toml && \
  poetry lock && \
  poetry install --without dev --no-root

# Stage 3: Final image
FROM python-deps AS final

WORKDIR /app

# Set environment variables
ARG ENV_FILE=.env.development
ARG ENV=development
ENV LOGURU_LEVEL=DEBUG

COPY ${ENV_FILE} .env.${ENV}

# Copy project files after installing dependencies
COPY cp_agent/ cp_agent/

# Expose port
EXPOSE 8000

ENV ENV=${ENV}

# Run the FastAPI server with --reload only in development
CMD ["sh", "-c", "uvicorn cp_agent.main:app --host 0.0.0.0 --port ${PORT:-8000} $([ \"$ENV\" = \"development\" ] && echo \"--reload\")"]