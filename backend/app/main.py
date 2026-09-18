import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.routers import auth, ingestion, ml, scraping, webhooks

app = FastAPI(
    title="Money Docs Decoded API",
    description="FastAPI orchestrator for financial document analysis, red-flag detection, and market benchmarking.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS for frontend Next.js application
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register stub service routers
app.include_router(auth.router)
app.include_router(ingestion.router)
app.include_router(ml.router)
app.include_router(scraping.router)
app.include_router(webhooks.router)


@app.get("/health", tags=["Health & Monitoring"])
async def health_check():
    """
    Uptime and health check endpoint for monitoring and deployment platforms.
    """
    return {
        "status": "healthy",
        "service": "Money Docs Decoded Backend API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
