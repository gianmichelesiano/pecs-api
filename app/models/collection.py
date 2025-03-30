# models/collection.py
from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from uuid import UUID
import uuid

from .user import User
from .phrase import Phrase


class CollectionBase(SQLModel):
    is_custom: bool = Field(default=True)
    is_visible: bool = Field(default=True)
    name_custom: Optional[str] = Field(default=None, max_length=255)
    icon: Optional[str] = Field(default="")
    color: Optional[str] = Field(default="#000000")


class CollectionCreate(CollectionBase):
    user_id: UUID
    translations: Optional[List[dict]] = None
    phrase_ids: Optional[List[UUID]] = None


class CollectionUpdate(SQLModel):
    is_custom: Optional[bool] = None
    is_visible: Optional[bool] = None
    name_custom: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    translations: Optional[List[dict]] = None
    phrase_ids: Optional[List[UUID]] = None


class CollectionTranslationBase(SQLModel):
    language_code: str = Field(max_length=10)
    name: str = Field(max_length=255)


class CollectionTranslationCreate(CollectionTranslationBase):
    collection_id: UUID


class CollectionTranslationUpdate(SQLModel):
    language_code: Optional[str] = None
    name: Optional[str] = None


class CollectionTranslationRead(CollectionTranslationBase):
    id: UUID
    collection_id: UUID


class CollectionTranslation(CollectionTranslationBase, table=True):
    __tablename__ = "collections_translations"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    collection_id: UUID = Field(foreign_key="collections.id")
    
    # Relationships
    collection: "Collection" = Relationship(back_populates="translations")
    
    class Config:
        table_name = "collections_translations"
        schema_extra = {
            "table_constraints": [
                {"name": "uq_collection_translation", "type": "unique", "columns": ["collection_id", "language_code"]}
            ]
        }


class PhraseCollection(SQLModel, table=True):
    __tablename__ = "phrase_collections"
    
    phrase_id: UUID = Field(foreign_key="phrases.id", primary_key=True)
    collection_id: UUID = Field(foreign_key="collections.id", primary_key=True)
    
    # Relationships
    phrase: Phrase = Relationship(back_populates="collections")
    collection: "Collection" = Relationship(back_populates="phrases")


class CollectionRead(CollectionBase):
    id: UUID
    created_at: datetime
    user_id: UUID
    translations: List[CollectionTranslationRead] = []
    phrase_count: Optional[int] = None


class Collection(CollectionBase, table=True):
    __tablename__ = "collections"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    user: User = Relationship(back_populates="collections")
    translations: List[CollectionTranslation] = Relationship(
        back_populates="collection",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    phrases: List[PhraseCollection] = Relationship(
        back_populates="collection",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
