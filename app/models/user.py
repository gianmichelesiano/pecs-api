import uuid
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, List
from datetime import datetime

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = Field(default=None, max_length=255)
    lang: Optional[str] = Field(default="en", max_length=2)

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)

class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: Optional[str] = Field(default=None, max_length=255)
    lang: Optional[str] = Field(default="en", max_length=2)

class UserUpdate(UserBase):
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8, max_length=40)

class UserUpdateMe(SQLModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    lang: Optional[str] = Field(default=None, max_length=2)

class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)

class User(UserBase, table=True):
    __tablename__ = "user"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    items: List["Item"] = Relationship(back_populates="owner", sa_relationship_kwargs={"cascade": "all, delete"})
    posts: List["Post"] = Relationship(back_populates="owner", sa_relationship_kwargs={"cascade": "all, delete"})

    sync_logs: List["SyncLog"] = Relationship(back_populates="user")
    
    # PECS relationships
    pecs: List["PECS"] = Relationship(back_populates="user")
    phrases: List["Phrase"] = Relationship(back_populates="user")
    collections: List["Collection"] = Relationship(back_populates="user")
    favorite_pecs: List["FavoritePECS"] = Relationship(back_populates="user")
    favorite_phrases: List["FavoritePhrase"] = Relationship(back_populates="user")
    
    # Images relationship
    images: List["Image"] = Relationship(back_populates="owner", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class UserPublic(UserBase):
    id: uuid.UUID

class UsersPublic(SQLModel):
    data: List[UserPublic]
    count: int
