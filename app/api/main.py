from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils, posts, pictograms, nomi
from app.core.config import settings
from app.api.routes import analyze

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(posts.router) 
api_router.include_router(analyze.router) 
api_router.include_router(pictograms.router)
api_router.include_router(nomi.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
