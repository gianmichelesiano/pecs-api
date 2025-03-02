from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Field, SQLModel, JSON

class PictogramBase(SQLModel):
    """Base Pictogram model with shared attributes"""
    name: str = Field(index=True)
    language: str = Field(index=True)
    category: str = Field(index=True)
    image_url: str
    description: Optional[str] = None
    tags: Dict[str, Any] = Field(default={}, sa_type=JSON)

class Pictogram(PictogramBase, table=True):
    """Pictogram model representing a pictogram in the database"""
    id: Optional[int] = Field(default=None, primary_key=True)

class PictogramCreate(PictogramBase):
    """Model for creating a new pictogram"""
    pass

class PictogramUpdate(SQLModel):
    """Model for updating an existing pictogram"""
    name: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    
class PictogramResponse(BaseModel):
    """Response model for pictogram search results"""
    word: str
    id: Optional[int] = None
    url: Optional[str] = None
    error: Optional[str] = None

class PhraseRequest(BaseModel):
    """Request model for phrase processing"""
    phrase: str = Field(..., description="Phrase to be processed")

class WordRequest(BaseModel):
    """Request model for word options"""
    word: str = Field(..., description="Word to find options for")
