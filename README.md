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
pip install "fastapi[all]" httpx uvicorn
deactivate
```

## Running the Service

### Development mode (foreground):

```bash
./run.sh
```

### Production mode with systemd:

1. Copy the service file to systemd:

```bash
sudo cp ollama-shim.service /etc/systemd/system/
sudo systemctl daemon-reload
```

2. Start and enable the service:

```bash
sudo systemctl start ollama-shim.service
sudo systemctl enable ollama-shim.service
```

## Configuration

Edit `ollama_shim.py` to set:
- `PRIMARY_MODEL_URL`
- `REFINER_MODEL_URL`
- `REFINER_SYSTEM_PROMPT`

## Usage

The service exposes endpoints at http://localhost:11434:

- `/v1/chat/completions` - OpenAI-compatible chat endpoint
- `/api/generate` - Ollama-specific generate endpoint
- `/api/pull` - Mock Ollama pull endpoint
- `/api/tags` - Mock model tags endpoint

## License

MIT