# models/phrase.py
from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from uuid import UUID
import uuid

from .user import User
from .pecs import PECS


class PhraseBase(SQLModel):
    # Base class for phrases
    pass


class PhraseCreate(PhraseBase):
    user_id: UUID
    translations: Optional[List[dict]] = None
    pecs_items: Optional[List[dict]] = None


class PhraseUpdate(SQLModel):
    translations: Optional[List[dict]] = None
    pecs_items: Optional[List[dict]] = None


class PhraseTranslationBase(SQLModel):
    language_code: str = Field(max_length=10)
    text: str = Field(max_length=500)
    audio_url: Optional[str] = Field(default=None, max_length=500)


class PhraseTranslationCreate(PhraseTranslationBase):
    phrase_id: UUID


class PhraseTranslationUpdate(SQLModel):
    language_code: Optional[str] = None
    text: Optional[str] = None
    audio_url: Optional[str] = None


class PhraseTranslationRead(PhraseTranslationBase):
    id: UUID
    phrase_id: UUID


class PhraseTranslation(PhraseTranslationBase, table=True):
    __tablename__ = "phrases_translations"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    phrase_id: UUID = Field(foreign_key="phrases.id")
    
    # Relationships
    phrase: "Phrase" = Relationship(back_populates="translations")
    
    class Config:
        table_name = "phrases_translations"
        schema_extra = {
            "table_constraints": [
                {"name": "uq_phrase_translation", "type": "unique", "columns": ["phrase_id", "language_code"]}
            ]
        }


class PhrasePECSBase(SQLModel):
    position: int


class PhrasePECSCreate(PhrasePECSBase):
    phrase_id: UUID
    pecs_id: UUID


class PhrasePECSUpdate(SQLModel):
    position: Optional[int] = None


class PhrasePECSRead(PhrasePECSBase):
    phrase_id: UUID
    pecs_id: UUID
    pecs_info: Optional[dict] = None


class PhrasePECS(PhrasePECSBase, table=True):
    __tablename__ = "phrase_pecs"
    
    phrase_id: UUID = Field(foreign_key="phrases.id", primary_key=True)
    pecs_id: UUID = Field(foreign_key="pecs.id", primary_key=True)
    
    # Relationships
    phrase: "Phrase" = Relationship(back_populates="pecs_items")
    pecs: PECS = Relationship(back_populates="phrases")


class PhraseRead(PhraseBase):
    id: UUID
    created_at: datetime
    user_id: UUID
    translations: List[PhraseTranslationRead] = []
    pecs_items: List[PhrasePECSRead] = []


class Phrase(PhraseBase, table=True):
    __tablename__ = "phrases"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    user: User = Relationship(back_populates="phrases")
    translations: List[PhraseTranslation] = Relationship(
        back_populates="phrase",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    pecs_items: List[PhrasePECS] = Relationship(
        back_populates="phrase",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    favorite_users: List["FavoritePhrase"] = Relationship(
        back_populates="phrase",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
