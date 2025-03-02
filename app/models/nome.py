from typing import Optional
from sqlmodel import Field, SQLModel

class NomeBase(SQLModel):
    """Base Nome model with shared attributes"""
    pictogram_id: int = Field(index=True)  # Removed foreign key constraint
    name: str = Field(index=True)
    lang: str = Field(max_length=3, index=True)

class Nome(NomeBase, table=True):
    """Nome model representing a name for a pictogram in a specific language"""
    id: Optional[int] = Field(default=None, primary_key=True)
    # Removed relationship to Pictogram

class NomeCreate(NomeBase):
    """Model for creating a new nome"""
    pass

class NomeUpdate(SQLModel):
    """Model for updating an existing nome"""
    pictogram_id: Optional[int] = None
    name: Optional[str] = None
    lang: Optional[str] = None
