# models/pictogram.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional
from uuid import UUID
import uuid

from .user import User
from .category import Category

# Classi per le richieste API
class PhraseRequest(SQLModel):
    phrase: str

class WordRequest(SQLModel):
    word: str

class PictogramResponse(SQLModel):
    word: str
    id: Optional[int] = None
    url: Optional[str] = None
    error: Optional[str] = None


class PictogramBase(SQLModel):
    word: str = Field(max_length=100)
    image_url: str
    is_custom: bool = Field(default=False)
    lang: str = Field(max_length=10, default="en")


class PictogramCreate(PictogramBase):
    created_by: Optional[UUID] = None
    # Lista di ID categorie a cui aggiungere il pittogramma
    category_ids: Optional[List[UUID]] = None


class PictogramUpdate(SQLModel):
    word: Optional[str] = None
    image_url: Optional[str] = None
    is_custom: Optional[bool] = None
    lang: Optional[str] = None
    # Se vuoi aggiornare le categorie
    category_ids: Optional[List[UUID]] = None


class PictogramRead(PictogramBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None


class Pictogram(PictogramBase, table=True):
    __tablename__ = "pictograms"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[UUID] = Field(default=None, foreign_key="user.id")
    
    # Relazioni
    categories: List["PictogramCategory"] = Relationship(back_populates="pictogram", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    sequence_items: List["SequenceItem"] = Relationship(back_populates="pictogram", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    creator: Optional[User] = Relationship(sa_relationship_kwargs={"foreign_keys": "Pictogram.created_by"})


class PictogramCategory(SQLModel, table=True):
    __tablename__ = "pictogram_categories"
    
    pictogram_id: UUID = Field(foreign_key="pictograms.id", primary_key=True)
    category_id: UUID = Field(foreign_key="categories.id", primary_key=True)
    
    # Relazioni
    pictogram: "Pictogram" = Relationship(back_populates="categories")
    category: Category = Relationship(back_populates="pictograms")