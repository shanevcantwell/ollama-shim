from fastapi import FastAPI
from routes import health, chat, generate, ollama_compat, unsupported

app = FastAPI()

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(generate.router)
app.include_router(ollama_compat.router)
app.include_router(unsupported.router)
