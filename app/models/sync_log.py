# models/sync_log.py
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from pydantic import validator
import uuid
from uuid import UUID

from .user import User


class SyncLogBase(SQLModel):
    entity_type: str = Field(max_length=20)  # 'category', 'pictogram', 'sequence', 'sequence_group'
    entity_id: UUID
    action: str = Field(max_length=10)  # 'create', 'update', 'delete'
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    
    @validator('entity_type')
    def validate_entity_type(cls, v):
        valid_types = ['category', 'pictogram', 'sequence', 'sequence_group']
        if v not in valid_types:
            raise ValueError(f"entity_type deve essere uno di {valid_types}")
        return v
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['create', 'update', 'delete']
        if v not in valid_actions:
            raise ValueError(f"action deve essere uno di {valid_actions}")
        return v


class SyncLogCreate(SyncLogBase):
    pass


class SyncLogRead(SyncLogBase):
    id: UUID
    timestamp: datetime


class SyncLog(SyncLogBase, table=True):
    __tablename__ = "sync_log"
    
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Relazioni
    user: Optional[User] = Relationship(sa_relationship_kwargs={"foreign_keys": "SyncLog.user_id"})