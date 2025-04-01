from fastapi import APIRouter
from ..api.endpoints import users, urls

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(urls.router, prefix="/links", tags=["links"]) 