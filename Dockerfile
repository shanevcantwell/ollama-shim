# Dockerfile for Ollama Shim service
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PRIMARY_MODEL_URL=http://localhost:1234/v1/chat/completions

EXPOSE 11434

CMD ["uvicorn", "ollama_shim:app", "--host", "0.0.0.0", "--port", "11434"]
