from sqlmodel import SQLModel

from .item import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate
from .auth import Message, Token, TokenPayload, NewPassword, UpdatePassword
from .user import User, UserCreate, UserPublic, UsersPublic, UserUpdate, UserUpdateMe, UserRegister
from .post import Post, PostCreate, PostUpdate, PostPublic, PostsPublic
from .nome import Nome, NomeCreate, NomeUpdate
from .analyze_models import PhraseRequest, WordRequest, PictogramResponse

# SyncLog models
from .sync_log import SyncLog, SyncLogBase, SyncLogCreate, SyncLogRead

# PECS models
from .pecs import (
    PECS, PECSBase, PECSCreate, PECSUpdate, PECSRead,
    PECSTranslation, PECSTranslationBase, PECSTranslationCreate, PECSTranslationUpdate, PECSTranslationRead
)
from .pecs_category import (
    PECSCategory, PECSCategoryBase, PECSCategoryCreate, PECSCategoryUpdate, PECSCategoryRead,
    CategoryTranslation, CategoryTranslationBase, CategoryTranslationCreate, CategoryTranslationUpdate, CategoryTranslationRead,
    PECSCategoryItem
)
from .phrase import (
    Phrase, PhraseBase, PhraseCreate, PhraseUpdate, PhraseRead,
    PhraseTranslation, PhraseTranslationBase, PhraseTranslationCreate, PhraseTranslationUpdate, PhraseTranslationRead,
    PhrasePECS, PhrasePECSBase, PhrasePECSCreate, PhrasePECSUpdate, PhrasePECSRead
)
from .favorite import FavoritePECS, FavoritePECSBase, FavoritePhrase, FavoritePhraseBase

__all__ = [
    "Item",
    "ItemCreate",
    "ItemPublic",
    "ItemsPublic",
    "ItemUpdate",
    "Message",
    "Post",
    "PostCreate",
    "PostUpdate",
    "PostPublic",
    "PostsPublic",
    "Token",
    "TokenPayload",
    "UpdatePassword",
    "NewPassword",
    "User",
    "UserCreate",
    "UserPublic",
    "UsersPublic",
    "UserUpdate",
    "UserUpdateMe",
    "UserRegister",
    "Nome",
    "NomeCreate",
    "NomeUpdate",
    # Analyze models
    "PhraseRequest",
    "WordRequest",
    "PictogramResponse",
    # SyncLog
    'SyncLog', 'SyncLogBase', 'SyncLogCreate', 'SyncLogRead',
    # PECS
    'PECS', 'PECSBase', 'PECSCreate', 'PECSUpdate', 'PECSRead',
    'PECSTranslation', 'PECSTranslationBase', 'PECSTranslationCreate', 'PECSTranslationUpdate', 'PECSTranslationRead',
    # PECS Categories
    'PECSCategory', 'PECSCategoryBase', 'PECSCategoryCreate', 'PECSCategoryUpdate', 'PECSCategoryRead',
    'CategoryTranslation', 'CategoryTranslationBase', 'CategoryTranslationCreate', 'CategoryTranslationUpdate', 'CategoryTranslationRead',
    'PECSCategoryItem',
    # Phrases
    'Phrase', 'PhraseBase', 'PhraseCreate', 'PhraseUpdate', 'PhraseRead',
    'PhraseTranslation', 'PhraseTranslationBase', 'PhraseTranslationCreate', 'PhraseTranslationUpdate', 'PhraseTranslationRead',
    'PhrasePECS', 'PhrasePECSBase', 'PhrasePECSCreate', 'PhrasePECSUpdate', 'PhrasePECSRead',
    # Favorites
    'FavoritePECS', 'FavoritePECSBase', 'FavoritePhrase', 'FavoritePhraseBase'
]
