from typing import Any, List, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import select, Session

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    PECS, PECSTranslation, PECSTranslationCreate, PECSTranslationRead, PECSTranslationUpdate,
    PECSCategory, CategoryTranslation, CategoryTranslationCreate, CategoryTranslationRead, CategoryTranslationUpdate,
    Message
)

router = APIRouter(prefix="/translations", tags=["translations"])


@router.get("/pecs/{pecs_id}", response_model=List[PECSTranslationRead])
def get_pecs_translations(
    pecs_id: UUID,
    session: SessionDep
) -> Any:
    """
    Retrieve all translations for a specific PECS.
    """
    # Verify PECS exists
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    # Get translations
    query = select(PECSTranslation).where(
        PECSTranslation.pecs_id == pecs_id
    )
    
    translations = session.exec(query).all()
    return translations


@router.post("/pecs/{pecs_id}", response_model=PECSTranslationRead)
def add_pecs_translation(
    pecs_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    translation: Dict[str, str] = Body(...)
) -> Any:
    """
    Add a translation to a PECS.
    
    Required fields in the request body:
    - language_code: The language code (e.g., "en", "it", "fr")
    - name: The translated name
    """
    # Verify PECS exists
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    # Check if translation already exists
    language_code = translation.get("language_code")
    if not language_code:
        raise HTTPException(status_code=400, detail="Language code is required")
    
    existing = session.exec(
        select(PECSTranslation).where(
            PECSTranslation.pecs_id == pecs_id,
            PECSTranslation.language_code == language_code
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Translation for language '{language_code}' already exists")
    
    # Create translation
    name = translation.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    new_translation = PECSTranslation(
        pecs_id=pecs_id,
        language_code=language_code,
        name=name
    )
    
    session.add(new_translation)
    session.commit()
    session.refresh(new_translation)
    
    return new_translation


@router.put("/pecs/{pecs_id}/{language_code}", response_model=PECSTranslationRead)
def update_pecs_translation(
    pecs_id: UUID,
    language_code: str,
    session: SessionDep,
    current_user: CurrentUser,
    translation: Dict[str, str] = Body(...)
) -> Any:
    """
    Update a translation for a PECS.
    
    Required fields in the request body:
    - name: The translated name
    """
    # Verify PECS exists
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    # Get existing translation
    existing = session.exec(
        select(PECSTranslation).where(
            PECSTranslation.pecs_id == pecs_id,
            PECSTranslation.language_code == language_code
        )
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail=f"Translation for language '{language_code}' not found")
    
    # Update translation
    name = translation.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    existing.name = name
    
    session.add(existing)
    session.commit()
    session.refresh(existing)
    
    return existing


@router.get("/categories/{category_id}", response_model=List[CategoryTranslationRead])
def get_category_translations(
    category_id: UUID,
    session: SessionDep
) -> Any:
    """
    Retrieve all translations for a specific category.
    """
    # Verify category exists
    category = session.get(PECSCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get translations
    query = select(CategoryTranslation).where(
        CategoryTranslation.category_id == category_id
    )
    
    translations = session.exec(query).all()
    return translations


@router.post("/categories/{category_id}", response_model=CategoryTranslationRead)
def add_category_translation(
    category_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    translation: Dict[str, str] = Body(...)
) -> Any:
    """
    Add a translation to a category.
    
    Required fields in the request body:
    - language_code: The language code (e.g., "en", "it", "fr")
    - name: The translated name
    """
    # Verify category exists
    category = session.get(PECSCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if translation already exists
    language_code = translation.get("language_code")
    if not language_code:
        raise HTTPException(status_code=400, detail="Language code is required")
    
    existing = session.exec(
        select(CategoryTranslation).where(
            CategoryTranslation.category_id == category_id,
            CategoryTranslation.language_code == language_code
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Translation for language '{language_code}' already exists")
    
    # Create translation
    name = translation.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    new_translation = CategoryTranslation(
        category_id=category_id,
        language_code=language_code,
        name=name
    )
    
    session.add(new_translation)
    session.commit()
    session.refresh(new_translation)
    
    return new_translation


@router.put("/categories/{category_id}/{language_code}", response_model=CategoryTranslationRead)
def update_category_translation(
    category_id: UUID,
    language_code: str,
    session: SessionDep,
    current_user: CurrentUser,
    translation: Dict[str, str] = Body(...)
) -> Any:
    """
    Update a translation for a category.
    
    Required fields in the request body:
    - name: The translated name
    """
    # Verify category exists
    category = session.get(PECSCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get existing translation
    existing = session.exec(
        select(CategoryTranslation).where(
            CategoryTranslation.category_id == category_id,
            CategoryTranslation.language_code == language_code
        )
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail=f"Translation for language '{language_code}' not found")
    
    # Update translation
    name = translation.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    
    existing.name = name
    
    session.add(existing)
    session.commit()
    session.refresh(existing)
    
    return existing
