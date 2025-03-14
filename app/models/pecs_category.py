# models/pecs_category.py
from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from uuid import UUID
import uuid

from .user import User
from .pecs import PECS


class PECSCategoryBase(SQLModel):
    parent_id: Optional[UUID] = Field(default=None)
    icon: Optional[str] = Field(default="")
    color: Optional[str] = Field(default="#000000")
    is_custom: Optional[bool] = Field(default=True)
    is_visible: Optional[bool] = Field(default=True)


class PECSCategoryCreate(PECSCategoryBase):
    parent_id: Optional[UUID] = None
    name: Optional[str] = None
    lang: Optional[str] = None
    translations: Optional[List[dict]] = None


class PECSCategoryUpdate(SQLModel):
    parent_id: Optional[UUID] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_custom: Optional[bool] = None
    is_visible: Optional[bool] = None
    translations: Optional[List[dict]] = None


class CategoryTranslationBase(SQLModel):
    language_code: str = Field(max_length=10)
    name: str = Field(max_length=255)


class CategoryTranslationCreate(CategoryTranslationBase):
    category_id: UUID


class CategoryTranslationUpdate(SQLModel):
    language_code: Optional[str] = None
    name: Optional[str] = None


class CategoryTranslationRead(CategoryTranslationBase):
    id: UUID
    category_id: UUID


class CategoryTranslation(CategoryTranslationBase, table=True):
    __tablename__ = "categories_translations"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    category_id: UUID = Field(foreign_key="pecs_categories.id")
    
    # Relationships
    category: "PECSCategory" = Relationship(back_populates="translations")
    
    class Config:
        table_name = "categories_translations"
        schema_extra = {
            "table_constraints": [
                {"name": "uq_category_translation", "type": "unique", "columns": ["category_id", "language_code"]}
            ]
        }


class PECSCategoryRead(PECSCategoryBase):
    id: UUID
    created_at: datetime
    parent_id: Optional[UUID] = None
    translations: List[CategoryTranslationRead] = []


class PECSCategory(PECSCategoryBase, table=True):
    __tablename__ = "pecs_categories"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    parent_id: Optional[UUID] = Field(default=None, foreign_key="pecs_categories.id")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    parent: Optional["PECSCategory"] = Relationship(
        sa_relationship_kwargs={"remote_side": "PECSCategory.id", "backref": "subcategories"}
    )
    translations: List[CategoryTranslation] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    pecs_items: List["PECSCategoryItem"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class PECSCategoryItem(SQLModel, table=True):
    __tablename__ = "pecs_category_items"
    
    pecs_id: UUID = Field(foreign_key="pecs.id", primary_key=True)
    category_id: UUID = Field(foreign_key="pecs_categories.id", primary_key=True)
    
    # Relationships
    pecs: PECS = Relationship(back_populates="categories")
    category: PECSCategory = Relationship(back_populates="pecs_items")
