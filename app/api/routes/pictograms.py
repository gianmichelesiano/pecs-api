from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import get_db, get_current_active_superuser, SessionDep, CurrentUser
from app.models.pictogram import Pictogram, PictogramCreate, PictogramUpdate
from app.models.user import User

router = APIRouter(prefix="/pictograms", tags=["pictograms"])


@router.get("/", response_model=List[Pictogram])
def read_pictograms(
    *,
    db: SessionDep,
    skip: int = 0,
    limit: int = 100,
    language: Optional[str] = None,
    category: Optional[str] = None,
    name: Optional[str] = None,
):
    """
    Retrieve pictograms with optional filtering.
    """
    query = select(Pictogram)
    
    # Apply filters if provided
    if language:
        query = query.where(Pictogram.language == language)
    if category:
        query = query.where(Pictogram.category == category)
    if name:
        query = query.where(Pictogram.name.contains(name))
    
    pictograms = db.exec(query.offset(skip).limit(limit)).all()
    return pictograms


@router.post("/", response_model=Pictogram)
def create_pictogram(
    *,
    db: SessionDep,
    pictogram_in: PictogramCreate,
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Create new pictogram.
    """
    pictogram = Pictogram.model_validate(pictogram_in.model_dump())
    db.add(pictogram)
    db.commit()
    db.refresh(pictogram)
    return pictogram


@router.get("/{pictogram_id}", response_model=Pictogram)
def read_pictogram(
    *,
    db: SessionDep,
    pictogram_id: int,
):
    """
    Get pictogram by ID.
    """
    pictogram = db.get(Pictogram, pictogram_id)
    if not pictogram:
        raise HTTPException(status_code=404, detail="Pictogram not found")
    return pictogram


@router.put("/{pictogram_id}", response_model=Pictogram)
def update_pictogram(
    *,
    db: SessionDep,
    pictogram_id: int,
    pictogram_in: PictogramUpdate,
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Update a pictogram.
    """
    pictogram = db.get(Pictogram, pictogram_id)
    if not pictogram:
        raise HTTPException(status_code=404, detail="Pictogram not found")
    
    # Update pictogram attributes
    pictogram_data = pictogram_in.model_dump(exclude_unset=True)
    for key, value in pictogram_data.items():
        setattr(pictogram, key, value)
    
    db.add(pictogram)
    db.commit()
    db.refresh(pictogram)
    return pictogram


@router.delete("/{pictogram_id}", response_model=Pictogram)
def delete_pictogram(
    *,
    db: SessionDep,
    pictogram_id: int,
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Delete a pictogram.
    """
    pictogram = db.get(Pictogram, pictogram_id)
    if not pictogram:
        raise HTTPException(status_code=404, detail="Pictogram not found")
    
    db.delete(pictogram)
    db.commit()
    return pictogram


@router.get("/search/", response_model=List[Pictogram])
def search_pictograms(
    *,
    db: SessionDep,
    q: str = Query(..., description="Search query"),
    language: Optional[str] = None,
):
    """
    Search pictograms by name or tags.
    """
    query = select(Pictogram).where(Pictogram.name.contains(q))
    
    if language:
        query = query.where(Pictogram.language == language)
    
    pictograms = db.exec(query).all()
    return pictograms
