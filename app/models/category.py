# models/category.py
from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from uuid import UUID
import uuid
from .user import User


class CategoryBase(SQLModel):
    name: str = Field(max_length=100)
    icon: Optional[str] = Field(default=None, max_length=100)
    color: str = Field(max_length=20)
    display_order: Optional[int] = Field(default=None)
    is_custom: bool = Field(default=False)
    is_visible: bool = Field(default=True)


class CategoryCreate(CategoryBase):
    # Se ci sono campi specifici solo per la creazione, li aggiungi qui
    created_by: Optional[UUID] = None


class CategoryUpdate(SQLModel):
    # Tutti opzionali per aggiornamenti parziali
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    display_order: Optional[int] = None
    is_custom: Optional[bool] = None
    is_visible: Optional[bool] = None


class CategoryRead(CategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None


class Category(CategoryBase, table=True):
    __tablename__ = "categories"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[UUID] = Field(default=None, foreign_key="user.id")
    
    # Relazioni
    pictograms: List["PictogramCategory"] = Relationship(back_populates="category")
    creator: Optional[User] = Relationship(sa_relationship_kwargs={"foreign_keys": "Category.created_by"})