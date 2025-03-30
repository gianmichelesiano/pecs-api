import uuid
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel
from .user import User

class ImageBase(SQLModel):
    filename: str = Field(min_length=1, max_length=255)
    url: str = Field(min_length=1)
    content_type: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)

class ImageCreate(ImageBase):
    pass

class ImageUpdate(SQLModel):
    filename: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)

class Image(ImageBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    owner: Optional[User] = Relationship(back_populates="images")

class ImagePublic(ImageBase):
    id: uuid.UUID
    owner_id: uuid.UUID

class ImagesPublic(SQLModel):
    data: List[ImagePublic]
    count: int
