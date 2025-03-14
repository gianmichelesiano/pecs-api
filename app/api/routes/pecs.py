from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select, Session

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    PECS, PECSCreate, PECSRead, PECSUpdate,
    PECSTranslation, PECSTranslationCreate, PECSTranslationRead, PECSTranslationUpdate,
    Message
)

router = APIRouter(prefix="/pecs", tags=["pecs"])


@router.get("/", response_model=List[PECSRead])
def get_all_pecs(
    session: SessionDep,
    language: Optional[str] = Query(None, description="Filter by language code"),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve all PECS with optional language filter.
    """
    query = select(PECS)
    
    if language:
        query = query.join(PECSTranslation).where(PECSTranslation.language_code == language)
    
    query = query.offset(skip).limit(limit)
    pecs_list = session.exec(query).all()
    
    return pecs_list


@router.get("/custom", response_model=List[PECSRead])
def get_custom_pecs(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve custom PECS created by the current user.
    """
    query = select(PECS).where(
        PECS.is_custom == True,
        PECS.user_id == current_user.id
    ).offset(skip).limit(limit)
    
    pecs_list = session.exec(query).all()
    return pecs_list


@router.get("/language/{code}", response_model=List[PECSRead])
def get_pecs_by_language(
    code: str,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve PECS in a specific language.
    """
    query = select(PECS).join(PECSTranslation).where(
        PECSTranslation.language_code == code
    ).offset(skip).limit(limit)
    
    pecs_list = session.exec(query).all()
    return pecs_list


@router.get("/{pecs_id}", response_model=PECSRead)
def get_pecs(
    pecs_id: UUID,
    session: SessionDep
) -> Any:
    """
    Retrieve a specific PECS by ID.
    """
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    return pecs


@router.post("/", response_model=PECSRead)
def create_pecs(
    pecs_in: PECSCreate,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Create a new PECS.
    """
    pecs = PECS(
        image_url=pecs_in.image_url,
        is_custom=pecs_in.is_custom,
        user_id=current_user.id if pecs_in.is_custom else None
    )
    
    session.add(pecs)
    session.commit()
    session.refresh(pecs)
    
    # Add translations if provided
    if pecs_in.translations:
        for translation_data in pecs_in.translations:
            translation = PECSTranslation(
                pecs_id=pecs.id,
                language_code=translation_data.get("language_code"),
                name=translation_data.get("name")
            )
            session.add(translation)
        
        session.commit()
        session.refresh(pecs)
    
    # Add to categories if provided
    if pecs_in.category_ids:
        from app.models import PECSCategoryItem
        for category_id in pecs_in.category_ids:
            category_item = PECSCategoryItem(
                pecs_id=pecs.id,
                category_id=category_id
            )
            session.add(category_item)
        
        session.commit()
        session.refresh(pecs)
    
    return pecs


@router.put("/{pecs_id}", response_model=PECSRead)
def update_pecs(
    pecs_id: UUID,
    pecs_in: PECSUpdate,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Update a PECS.
    """
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    # Check if user has permission to update
    if pecs.is_custom and pecs.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update PECS fields
    update_data = pecs_in.model_dump(exclude_unset=True)
    
    # Handle direct fields
    if "image_url" in update_data:
        pecs.image_url = update_data["image_url"]
    if "is_custom" in update_data:
        pecs.is_custom = update_data["is_custom"]
    
    # Handle translations
    if "translations" in update_data and update_data["translations"]:
        # Get existing translations
        existing_translations = {t.language_code: t for t in pecs.translations}
        
        for translation_data in update_data["translations"]:
            language_code = translation_data.get("language_code")
            name = translation_data.get("name")
            
            if language_code in existing_translations:
                # Update existing translation
                existing_translations[language_code].name = name
            else:
                # Create new translation
                new_translation = PECSTranslation(
                    pecs_id=pecs.id,
                    language_code=language_code,
                    name=name
                )
                session.add(new_translation)
    
    # Handle categories
    if "category_ids" in update_data and update_data["category_ids"] is not None:
        from app.models import PECSCategoryItem
        
        # Remove existing category associations
        session.exec(
            select(PECSCategoryItem).where(PECSCategoryItem.pecs_id == pecs.id)
        ).all()
        
        # Add new category associations
        for category_id in update_data["category_ids"]:
            category_item = PECSCategoryItem(
                pecs_id=pecs.id,
                category_id=category_id
            )
            session.add(category_item)
    
    session.add(pecs)
    session.commit()
    session.refresh(pecs)
    
    return pecs


@router.delete("/{pecs_id}", response_model=Message)
def delete_pecs(
    pecs_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Delete a PECS.
    """
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    # Check if user has permission to delete
    if pecs.is_custom and pecs.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    session.delete(pecs)
    session.commit()
    
    return Message(message="PECS deleted successfully")
