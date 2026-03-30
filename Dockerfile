# Dockerfile for Ollama Shim service
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY src/ ./src/
COPY .env.example ./.env

# Set default environment variables (can be overridden with -e)
ENV SHIM_PORT=11434
ENV BACKEND_BASE_URL=http://host.docker.internal:1234

EXPOSE ${SHIM_PORT}

# Use shell form for variable expansion, or pass via --env-file
CMD ["sh", "-c", "python -m uvicorn src.main:app --host 0.0.0.0 --port ${SHIM_PORT}"]
