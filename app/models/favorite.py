# models/favorite.py
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from uuid import UUID

from .user import User
from .pecs import PECS
from .phrase import Phrase


class FavoritePECSBase(SQLModel):
    # Base class for favorite PECS
    pass


class FavoritePECS(FavoritePECSBase, table=True):
    __tablename__ = "favorite_pecs"
    
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    pecs_id: UUID = Field(foreign_key="pecs.id", primary_key=True)
    
    # Relationships
    user: User = Relationship(back_populates="favorite_pecs")
    pecs: PECS = Relationship(back_populates="favorite_users")


class FavoritePhraseBase(SQLModel):
    # Base class for favorite phrases
    pass


class FavoritePhrase(FavoritePhraseBase, table=True):
    __tablename__ = "favorite_phrases"
    
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    phrase_id: UUID = Field(foreign_key="phrases.id", primary_key=True)
    
    # Relationships
    user: User = Relationship(back_populates="favorite_phrases")
    phrase: Phrase = Relationship(back_populates="favorite_users")
