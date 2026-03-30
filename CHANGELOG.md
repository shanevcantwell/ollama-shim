# Changelog

## [1.0.0] - 2026-03-30

### Added
- Added `scripts/install-linux-service.sh` for automated systemd service deployment on Ubuntu/Debian
- Added `SHIM_PORT` configuration via `.env` file with default value of 11434

### Changed
- Refactored `run.bat` and `run.sh` to read `SHIM_PORT` from `.env` and added `--reload` flag for development
- Moved `install-windows-service.ps1` to `scripts/` folder
- Updated `INSTALL.md` to use the new automated service installation scripts

### Fixed
- Fixed Dockerfile to use correct module path (`src.main:app`) and environment variables

### Removed
- Removed `ollama-shim.service` from root directory (replaced by `scripts/install-linux-service.sh`)

## [0.1.0] - 2025-10-23

### Added
- Initial release of ollama_shim service that bridges LM Studio with Ollama API clients.
- OpenAI-compatible chat completions endpoint
- Ollama-specific generate, pull and tags endpoints
- Support for multimodal requests (text + images)
- Basic error handling and logging