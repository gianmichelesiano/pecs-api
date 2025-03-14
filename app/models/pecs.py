# models/pecs.py
from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from uuid import UUID
import uuid

from .user import User


class PECSBase(SQLModel):
    image_url: str = Field(max_length=500)
    is_custom: bool = Field(default=False)


class PECSCreate(PECSBase):
    user_id: Optional[UUID] = None
    translations: Optional[List[dict]] = None
    category_ids: Optional[List[UUID]] = None


class PECSUpdate(SQLModel):
    image_url: Optional[str] = None
    is_custom: Optional[bool] = None
    translations: Optional[List[dict]] = None
    category_ids: Optional[List[UUID]] = None


class PECSTranslationBase(SQLModel):
    language_code: str = Field(max_length=10)
    name: str = Field(max_length=255)


class PECSTranslationCreate(PECSTranslationBase):
    pecs_id: UUID


class PECSTranslationUpdate(SQLModel):
    language_code: Optional[str] = None
    name: Optional[str] = None


class PECSTranslationRead(PECSTranslationBase):
    id: UUID
    pecs_id: UUID


class PECSTranslation(PECSTranslationBase, table=True):
    __tablename__ = "pecs_translations"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    pecs_id: UUID = Field(foreign_key="pecs.id")
    
    # Relationships
    pecs: "PECS" = Relationship(back_populates="translations")
    
    class Config:
        table_name = "pecs_translations"
        schema_extra = {
            "table_constraints": [
                {"name": "uq_pecs_translation", "type": "unique", "columns": ["pecs_id", "language_code"]}
            ]
        }


class PECSRead(PECSBase):
    id: UUID
    created_at: datetime
    user_id: Optional[UUID] = None
    translations: List[PECSTranslationRead] = []


class PECS(PECSBase, table=True):
    __tablename__ = "pecs"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="pecs")
    translations: List[PECSTranslation] = Relationship(
        back_populates="pecs",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    categories: List["PECSCategoryItem"] = Relationship(
        back_populates="pecs",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    phrases: List["PhrasePECS"] = Relationship(
        back_populates="pecs",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    favorite_users: List["FavoritePECS"] = Relationship(
        back_populates="pecs",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
