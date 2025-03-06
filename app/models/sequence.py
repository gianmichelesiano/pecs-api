# models/sequence.py
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
import uuid

from .user import User
from .pictogram import Pictogram


class SequenceGroupBase(SQLModel):
    name: str = Field(max_length=100)
    icon: Optional[str] = Field(default=None, max_length=100)
    color: str = Field(max_length=20)
    display_order: int


class SequenceGroupCreate(SequenceGroupBase):
    created_by: Optional[UUID] = None


class SequenceGroupUpdate(SQLModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    display_order: Optional[int] = None


class SequenceGroupRead(SequenceGroupBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None


class SequenceGroup(SequenceGroupBase, table=True):
    __tablename__ = "sequence_groups"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[UUID] = Field(default=None, foreign_key="user.id")
    
    # Relazioni
    sequences: List["Sequence"] = Relationship(back_populates="group")
    creator: Optional[User] = Relationship(sa_relationship_kwargs={"foreign_keys": "SequenceGroup.created_by"})


class SequenceBase(SQLModel):
    name: str = Field(max_length=100)
    display_order: int
    is_favorite: bool = Field(default=False)
    group_id: Optional[UUID] = Field(default=None, foreign_key="sequence_groups.id")


class SequenceCreate(SequenceBase):
    created_by: Optional[UUID] = None
    # Opzionalmente, include i pittogrammi iniziali
    items: Optional[List[dict]] = None  # Lista di dizionari {pictogram_id, position}


class SequenceUpdate(SQLModel):
    name: Optional[str] = None
    display_order: Optional[int] = None
    is_favorite: Optional[bool] = None
    group_id: Optional[UUID] = None


class SequenceRead(SequenceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None


class Sequence(SequenceBase, table=True):
    __tablename__ = "sequences"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[UUID] = Field(default=None, foreign_key="user.id")
    
    # Relazioni
    group: Optional[SequenceGroup] = Relationship(back_populates="sequences")
    items: List["SequenceItem"] = Relationship(back_populates="sequence")
    creator: Optional[User] = Relationship(sa_relationship_kwargs={"foreign_keys": "Sequence.created_by"})


class SequenceItemBase(SQLModel):
    sequence_id: UUID = Field(foreign_key="sequences.id")
    pictogram_id: UUID = Field(foreign_key="pictograms.id")
    position: int


class SequenceItemCreate(SequenceItemBase):
    pass


class SequenceItemUpdate(SQLModel):
    position: Optional[int] = None
    pictogram_id: Optional[UUID] = None


class SequenceItemRead(SequenceItemBase):
    id: UUID
    created_at: datetime


class SequenceItem(SequenceItemBase, table=True):
    __tablename__ = "sequence_items"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relazioni
    sequence: Sequence = Relationship(back_populates="items")
    pictogram: Pictogram = Relationship(back_populates="sequence_items")