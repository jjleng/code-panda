"""Main FastAPI application module."""

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from cp_agent.api.v1 import api_router
from cp_agent.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CodePanda Agent API",
    version=settings.VERSION,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
