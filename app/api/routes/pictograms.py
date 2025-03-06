import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from app.api.deps import SessionDep, CurrentUser
from app.models import Pictogram, PictogramCreate, PictogramUpdate, PictogramRead, PictogramCategory, Category, Message

router = APIRouter(prefix="/pictograms", tags=["pictograms"])


@router.get("/", response_model=List[PictogramRead])
def read_pictograms(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    is_custom: Optional[bool] = None,
    category_id: Optional[uuid.UUID] = None,
    word: Optional[str] = None,
):
    """
    Retrieve pictograms with optional filtering.
    """
    query = select(Pictogram)
    
    # Apply filters if provided
    if is_custom is not None:
        query = query.where(Pictogram.is_custom == is_custom)
    
    if word:
        query = query.where(Pictogram.word.contains(word))
    
    if category_id:
        query = (
            query
            .join(PictogramCategory, Pictogram.id == PictogramCategory.pictogram_id)
            .where(PictogramCategory.category_id == category_id)
        )
    
    # Filter by user for custom pictograms
    if not current_user.is_superuser and is_custom:
        query = query.where(Pictogram.created_by == current_user.id)
    
    pictograms = session.exec(query.offset(skip).limit(limit)).all()
    return pictograms


@router.post("/", response_model=PictogramRead)
def create_pictogram(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    pictogram_in: PictogramCreate,
):
    """
    Create new pictogram.
    """
    # Create the pictogram
    pictogram_data = pictogram_in.model_dump(exclude={"category_ids"})
    pictogram = Pictogram.model_validate(pictogram_data, update={"created_by": current_user.id})
    session.add(pictogram)
    session.commit()
    session.refresh(pictogram)
    
    # Add categories if provided
    if pictogram_in.category_ids:
        for category_id in pictogram_in.category_ids:
            # Verify category exists
            category = session.get(Category, category_id)
            if not category:
                session.delete(pictogram)
                session.commit()
                raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")
            
            # Create relationship
            pictogram_category = PictogramCategory(
                pictogram_id=pictogram.id,
                category_id=category_id
            )
            session.add(pictogram_category)
        
        session.commit()
        session.refresh(pictogram)
    
    return pictogram


@router.get("/{pictogram_id}", response_model=PictogramRead)
def read_pictogram(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    pictogram_id: uuid.UUID,
):
    """
    Get pictogram by ID.
    """
    pictogram = session.get(Pictogram, pictogram_id)
    if not pictogram:
        raise HTTPException(status_code=404, detail="Pictogram not found")
    
    # Check permissions for custom pictograms
    if pictogram.is_custom and not current_user.is_superuser and pictogram.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return pictogram


@router.put("/{pictogram_id}", response_model=PictogramRead)
def update_pictogram(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    pictogram_id: uuid.UUID,
    pictogram_in: PictogramUpdate,
):
    """
    Update a pictogram.
    """
    pictogram = session.get(Pictogram, pictogram_id)
    if not pictogram:
        raise HTTPException(status_code=404, detail="Pictogram not found")
    
    # Check permissions
    if not current_user.is_superuser and (pictogram.is_custom and pictogram.created_by != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update pictogram attributes
    update_data = pictogram_in.model_dump(exclude_unset=True, exclude={"category_ids"})
    for key, value in update_data.items():
        setattr(pictogram, key, value)
    
    # Update categories if provided
    if pictogram_in.category_ids is not None:
        # Remove existing category relationships
        existing_relations = session.exec(
            select(PictogramCategory).where(PictogramCategory.pictogram_id == pictogram_id)
        ).all()
        for relation in existing_relations:
            session.delete(relation)
        
        # Add new category relationships
        for category_id in pictogram_in.category_ids:
            # Verify category exists
            category = session.get(Category, category_id)
            if not category:
                raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")
            
            # Create relationship
            pictogram_category = PictogramCategory(
                pictogram_id=pictogram.id,
                category_id=category_id
            )
            session.add(pictogram_category)
    
    pictogram.updated_at = func.now()
    session.add(pictogram)
    session.commit()
    session.refresh(pictogram)
    return pictogram


@router.delete("/{pictogram_id}", response_model=Message)
def delete_pictogram(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    pictogram_id: uuid.UUID,
):
    """
    Delete a pictogram.
    """
    pictogram = session.get(Pictogram, pictogram_id)
    if not pictogram:
        raise HTTPException(status_code=404, detail="Pictogram not found")
    
    # Check permissions
    if not current_user.is_superuser and (pictogram.is_custom and pictogram.created_by != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Delete the pictogram (relationships will be deleted automatically due to cascade)
    session.delete(pictogram)
    session.commit()
    return Message(message="Pictogram deleted successfully")


@router.get("/search/", response_model=List[PictogramRead])
def search_pictograms(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    q: str = Query(..., description="Search query"),
):
    """
    Search pictograms by word.
    """
    query = select(Pictogram).where(Pictogram.word.contains(q))
    
    # Filter by user for custom pictograms if not superuser
    if not current_user.is_superuser:
        query = query.where((Pictogram.is_custom == False) | (Pictogram.created_by == current_user.id))
    
    pictograms = session.exec(query).all()
    return pictograms
