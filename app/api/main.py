from fastapi import APIRouter

from app.api.routes import (
    items, login, private, users, utils, posts, nomi, 
    pecs, categories, phrases, favorites, translations,
    collections, images
)
from app.core.config import settings
from app.api.routes import analyze

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(posts.router) 
api_router.include_router(analyze.router) 
api_router.include_router(nomi.router)

# PECS API routes
api_router.include_router(pecs.router)
api_router.include_router(categories.router)
api_router.include_router(phrases.router)
api_router.include_router(collections.router)
api_router.include_router(favorites.router)
api_router.include_router(translations.router)
api_router.include_router(images.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
