# Ollama Shim Service

A service that bridges LM Studio with tools expecting an Ollama API.

## Features

- Exposes OpenAI-compatible chat completions endpoint
- Supports multimodal requests (text + images)
- Maintains compatibility with Ollama-specific endpoints

## Requirements

- Python 3.7+
- Required packages:
  - fastapi[all]
  - httpx
  - uvicorn

## Installation

1. Clone this repository:

```bash
git clone https://github.com/shanevcantwell/ollama_shim.git
cd ollama_shim
```

2. Set up a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

## Running the Service

```bash
./run.sh
```

## Configuration

Create a `.env` file in the project root directory to override the default settings.
You can copy the `.env.example` file to get started:

```bash
cp .env.example .env
```

Then, edit the `.env` file to set your desired configuration. The following variables are available:

- `PRIMARY_MODEL_URL`: The full URL to your LM Studio (or other OpenAI-compatible) completions endpoint.
- `API_TIMEOUT`: Timeout (in seconds) for the OpenAI API request.
- `RESPONSE_TIMEOUT`: Max wait time for a response from the model.
- `SHIM_PORT`: Port for the Ollama Shim service to listen on.

## Usage

The service exposes endpoints at http://localhost:11434:

- `/v1/chat/completions` - OpenAI-compatible chat endpoint
- `/api/generate` - Ollama-specific generate endpoint
- `/api/pull` - Mock Ollama pull endpoint
- `/api/tags` - Mock model tags endpoint

## License

MIT
