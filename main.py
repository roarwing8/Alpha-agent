import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Load .env before importing routes, because routes creates the LLM client singleton.
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

from crypto_agent.routes import router

app = FastAPI(
    title="Project AlphaQ - Crypto Trading AI Agent",
    description=(
        "Institutional-grade crypto trading intelligence agent. "
        "Supports OpenAI, OpenRouter, and Ollama backends. "
        "For educational purposes only — not financial advice."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve static frontend files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["System"], include_in_schema=False)
async def root():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "production") == "development",
    )
