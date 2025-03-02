from datetime import datetime
import uuid
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional

from .user import User

class PostBase(SQLModel):
    title: str = Field(index=True)
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Post(PostBase, table=True):
    __tablename__ = "post"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    owner: Optional[User] = Relationship(back_populates="posts")

class PostCreate(PostBase):
    pass

class PostUpdate(SQLModel):
    title: str | None = None
    description: str | None = None

class PostPublic(PostBase):
    id: uuid.UUID
    owner_id: uuid.UUID

class PostsPublic(SQLModel):
    data: list[PostPublic]
    count: int