"""API v1 package."""

from fastapi import APIRouter

from cp_agent.api.v1.chat import router as chat_router
from cp_agent.api.v1.projects import router as projects_router

api_router = APIRouter()

api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
