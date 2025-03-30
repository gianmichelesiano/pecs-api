# models/analyze_models.py
from typing import Optional
from sqlmodel import SQLModel

# Classi per le richieste API
class PhraseRequest(SQLModel):
    phrase: str

class WordRequest(SQLModel):
    word: str

class PictogramResponse(SQLModel):
    word: Optional[str]
    id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None



