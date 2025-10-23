# Dockerfile for Ollama Shim service
FROM python:3.9-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -e ".[all]"

COPY . .

ENV PRIMARY_MODEL_URL=http://localhost:1234/v1/chat/completions
ENV REFINER_MODEL_URL=http://localhost:1235/v1/chat/completions

EXPOSE 11434

CMD ["uvicorn", "ollama_shim:app", "--host", "0.0.0.0", "--port", "11434"]