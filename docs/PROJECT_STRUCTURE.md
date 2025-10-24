# Project Structure: Ollama Shim (Updated)

This document outlines the file and directory structure of the Ollama Shim project, serving as a quick reference for both human developers and AI agents. The refactoring aims to improve modularity, readability, and maintainability.

## Top-Level Files

*   `main.py`:
    *   **Purpose**: The main entry point of the FastAPI application. It initializes the FastAPI app and includes all the individual routers defined in the `routes/` directory.
    *   **Interconnection**: Imports `config` for global settings and includes routers from `routes/`.

*   `config.py`:
    *   **Purpose**: Stores environment variable loading and core configuration settings such as `LM_STUDIO_BASE_URL`, `PRIMARY_MODEL_URL`, `API_TIMEOUT`, and `RESPONSE_TIMEOUT`.
    *   **Interconnection**: Imported by `utils.py` and various route files to access global configuration.

*   `utils.py`:
    *   **Purpose**: Contains shared helper functions used across multiple parts of the application, including `map_ollama_options_to_openai`, `call_llm`, and `check_backend_health`.
    *   **Interconnection**: Imported by various route files that need to interact with the LLM backend or perform health checks.

*   `ollama_shim.py.bak`:
    *   **Purpose**: A backup of the original file before refactoring.
    *   **Interconnection**: Not directly connected to the running application; solely for historical reference.

## `routes/` Directory

This directory contains individual FastAPI routers, each responsible for a specific set of API endpoints.

*   `routes/chat.py`: Handles chat-related endpoints, translating between OpenAI and Ollama formats.
*   `routes/generate.py`: Manages text generation endpoints with multimodal support.
*   `routes/health.py`: Provides health check endpoints and backend connection verification.
*   `routes/ollama_compat.py`: Implements compatibility endpoints for Ollama clients.
*   `routes/unsupported.py`: Handles unsupported OpenAI endpoints.

## Test Files

*   `tests/test_api.py`:
    *   **Purpose**: Contains unit tests for API routes, including mock responses that simulate the LM Studio backend behavior
    *   **Key Features**:
        - Uses pytest-httpx for HTTP request mocking
        - Includes detailed streaming response mocks that match real service output
        - Tests both streaming and non-streaming endpoints

## `scripts/` Directory

*   `scripts/run-tests.sh`:
    *   **Purpose**: Script for setting up a clean testing environment and executing API tests
    *   **Key Features**:
        - Creates virtual environment if needed
        - Installs required testing packages
        - Executes specific test cases with detailed output
        - Automatically cleans up after execution

*   `scripts/graveyard/`:
    *   **Purpose**: Stores previously used but now obsolete scripts for reference
    *   **Example Contents**:
        - `refactor_script.sh` (from previous refactoring efforts)

## Development Workflow Notes

1. **Testing Process**:
   - Tests are designed to run in an isolated virtual environment to prevent conflicts with system packages
   - Mock responses have been updated to closely match real service output for accurate testing
   - The test script handles all setup and teardown automatically

2. **Key Improvements Made**:
   - Added proper HTTP response mocking that matches the actual backend format
   - Implemented virtual environment isolation for reliable testing
   - Created reusable testing scripts to simplify future test execution

## How They Interconnect

The application maintains its modular design with `main.py` as the orchestrator. The test files and scripts are now properly integrated into the development workflow, allowing for isolated, reproducible testing without affecting the main codebase.

---
This document will be kept up-to-date with any future structural changes to the project.