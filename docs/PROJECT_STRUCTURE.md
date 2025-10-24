# Project Structure: Ollama Shim

This document outlines the file and directory structure of the Ollama Shim project, serving as a quick reference for both human developers and AI agents. The refactoring aims to improve modularity, readability, and maintainability.

## Top-Level Files

*   `main.py`:
    *   **Purpose**: The main entry point of the FastAPI application. It initializes the FastAPI app and includes all the individual routers defined in the `routes/` directory.
    *   **Interconnection**: Imports `config` for global settings and includes routers from `routes/`.
*   `config.py`:
    *   **Purpose**: Stores environment variable loading and core configuration settings such as `LM_STUDIO_BASE_URL`, `PRIMARY_MODEL_URL`, `API_TIMEOUT`, and `RESPONSE_TIMEOUT`.
    *   **Interconnection**: Imported by `utils.py` and various route files to access global configuration.
*   `utils.py`:
    *   **Purpose**: Contains shared helper functions used across multiple parts of the application, including `map_ollama_options_to_openai` (for translating Ollama options to OpenAI format), `call_llm` (for making HTTP calls to the backend LLM), and `check_backend_health` (for verifying backend service availability).
    *   **Interconnection**: Imported by various route files that need to interact with the LLM backend or perform health checks.
*   `ollama_shim.py.bak`:
    *   **Purpose**: A backup of the original `ollama_shim.py` file before refactoring.
    *   **Interconnection**: Not directly connected to the running application; solely for historical reference.

## `routes/` Directory

This directory contains individual FastAPI routers, each responsible for a specific set of API endpoints.

*   `routes/chat.py`:
    *   **Purpose**: Handles chat-related API endpoints. This includes both OpenAI-compatible chat completions (`/v1/chat/completions`) and Ollama-specific chat requests (`/api/chat`). It translates Ollama requests to the OpenAI format before forwarding them to the LM Studio backend.
    *   **Interconnection**: Imports `utils.py` for helper functions and `config.py` for backend URLs and timeouts.
*   `routes/generate.py`:
    *   **Purpose**: Manages the Ollama-specific text generation endpoint (`/api/generate`). It translates Ollama generation requests (including multimodal inputs like images) to the OpenAI chat completions format.
    *   **Interconnection**: Imports `utils.py` for helper functions and `config.py` for backend URLs and timeouts.
*   `routes/health.py`:
    *   **Purpose**: Provides various health check endpoints for the application and its backend connection. This includes basic health checks (`/`, `/v1`, `/v1/`) and a detailed health check (`/health`).
    *   **Interconnection**: Imports `utils.py` to use `check_backend_health` and `config.py` for reporting configured URLs and timeouts.
*   `routes/ollama_compat.py`:
    *   **Purpose**: Implements endpoints to provide compatibility with Ollama clients for non-generation specific requests. This includes faking the `pull` command (`/api/pull`), providing dummy model information for `show` (`/api/show`), and translating LM Studio models into an Ollama-compatible format for `tags` (`/api/tags`).
    *   **Interconnection**: Imports `utils.py` for health checks and `config.py` for LM Studio base URL.
*   `routes/unsupported.py`:
    *   **Purpose**: Defines a specific response for an unsupported OpenAI completions endpoint (`/v1/completions`), guiding clients to use the chat completions endpoint instead.
    *   **Interconnection**: A standalone router with no external dependencies within the project beyond FastAPI.

## `scripts/` Directory

*   `scripts/graveyard/`:
    *   **Purpose**: A directory for successful, one-off scripts that are no longer needed in the project root but are kept for reference.
    *   **Interconnection**: Contains `refactor_script.sh` after its successful execution.

## How They Interconnect

The `main.py` acts as the orchestrator, bringing together the configuration, utility functions, and distinct API route definitions. The `config.py` provides global parameters, while `utils.py` encapsulates reusable logic for interacting with the LM Studio backend and performing common tasks. Each file in the `routes/` directory defines a subset of the API, making it easier to manage and extend endpoints without affecting other parts of the application. This modular design promotes clear separation of concerns and improves the overall maintainability of the Ollama Shim.

---
This document will be kept up-to-date with any future structural changes to the project.
