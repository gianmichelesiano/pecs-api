from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select, Session

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    PECSCategory, PECSCategoryCreate, PECSCategoryRead, PECSCategoryUpdate,
    CategoryTranslation, CategoryTranslationCreate, CategoryTranslationRead, CategoryTranslationUpdate,
    PECS, PECSRead, PECSCategoryItem,
    Message
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=List[PECSCategoryRead])
def get_all_categories(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve all categories.
    """
    query = select(PECSCategory).offset(skip).limit(limit)
    categories = session.exec(query).all()
    
    return categories


@router.get("/language/it/with_pecs_count")
def get_italian_categories_with_pecs_count(
    session: SessionDep,
    skip: int = 0,
    limit: Optional[int] = None,
    name: Optional[str] = None
) -> Any:
    """
    Retrieve Italian categories with pecs count.
    """
    # First check if there are any translations with Italian language code
    translations_query = select(CategoryTranslation).where(
        CategoryTranslation.language_code == "it"
    )
    translations = session.exec(translations_query).all()
    print(f"Found {len(translations)} translations for language code: it")
    
    # Build the query
    query = select(PECSCategory).join(CategoryTranslation).where(
        CategoryTranslation.language_code == "it"
    )
    
    # Add name filter if provided
    if name:
        query = query.where(CategoryTranslation.name == name)
    
    # Add pagination only if limit is provided
    query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    
    # Execute query
    categories = session.exec(query).all()
    print(f"Found {len(categories)} categories for language code: it")
    
    # Add pecs count for each category
    from sqlalchemy import func
    result = []
    for category in categories:
        # Convert category to dict
        category_dict = category.model_dump()
        
        # Count PECS items for this category
        pecs_count_query = select(func.count()).select_from(PECSCategoryItem).where(
            PECSCategoryItem.category_id == category.id
        )
        pecs_count = session.exec(pecs_count_query).one()
        
        # Add pecs count to the dict
        category_dict["pecs"] = pecs_count
        result.append(category_dict)
    
    return result


@router.get("/language/{code}", response_model=List[PECSCategoryRead])
def get_categories_by_language(
    code: str,
    session: SessionDep,
    skip: int = 0,
    limit: Optional[int] = None,  # Made limit optional
    name: Optional[str] = None  # Added name filter
) -> Any:
    """
    Retrieve categories in a specific language.
    """
    # First check if there are any translations with this language code
    translations_query = select(CategoryTranslation).where(
        CategoryTranslation.language_code == code
    )
    translations = session.exec(translations_query).all()
    print(f"Found {len(translations)} translations for language code: {code}")
    
    # Build the query
    query = select(PECSCategory).join(CategoryTranslation).where(
        CategoryTranslation.language_code == code
    )
    
    # Add name filter if provided
    if name:
        query = query.where(CategoryTranslation.name == name)
    
    # Add pagination only if limit is provided
    query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    
    # Execute query
    categories = session.exec(query).all()
    print(f"Found {len(categories)} categories for language code: {code}")
    
    return categories


@router.get("/{category_id}", response_model=PECSCategoryRead)
def get_category(
    category_id: UUID,
    session: SessionDep
) -> Any:
    """
    Retrieve a specific category by ID.
    """
    category = session.get(PECSCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


@router.get("/{category_id}/pecs", response_model=List[PECSRead])
def get_pecs_in_category(
    category_id: UUID,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve all PECS in a specific category.
    """
    # Verify category exists
    category = session.get(PECSCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get PECS in this category
    query = select(PECS).join(PECSCategoryItem).where(
        PECSCategoryItem.category_id == category_id
    ).offset(skip).limit(limit)
    
    pecs_list = session.exec(query).all()
    return pecs_list


@router.post("/", response_model=PECSCategoryRead)
def create_category(
    category_in: PECSCategoryCreate,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Create a new category.
    """
    # Verify parent category exists if provided
    if category_in.parent_id:
        parent = session.get(PECSCategory, category_in.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
    
    # Create category with new fields
    category = PECSCategory(
        parent_id=category_in.parent_id,
        icon=category_in.icon,
        color=category_in.color,
        is_custom=category_in.is_custom,
        is_visible=category_in.is_visible
    )
    
    session.add(category)
    session.commit()
    session.refresh(category)
    
    # Add translations if provided
    if category_in.translations:
        for translation_data in category_in.translations:
            translation = CategoryTranslation(
                category_id=category.id,
                language_code=translation_data.get("language_code"),
                name=translation_data.get("name")
            )
            session.add(translation)
        
        session.commit()
        session.refresh(category)
    # Handle direct lang and name parameters for translation
    elif category_in.lang and category_in.name:
        translation = CategoryTranslation(
            category_id=category.id,
            language_code=category_in.lang,  # Map lang to language_code
            name=category_in.name
        )
        session.add(translation)
        session.commit()
        session.refresh(category)
    
    return category


@router.put("/{category_id}", response_model=PECSCategoryRead)
def update_category(
    category_id: UUID,
    category_in: PECSCategoryUpdate,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Update a category.
    """
    category = session.get(PECSCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update category fields
    update_data = category_in.model_dump(exclude_unset=True)
    
    # Handle parent_id
    if "parent_id" in update_data:
        # Prevent circular references
        if update_data["parent_id"] == category_id:
            raise HTTPException(status_code=400, detail="Category cannot be its own parent")
        
        # Verify parent exists if not None
        if update_data["parent_id"] is not None:
            parent = session.get(PECSCategory, update_data["parent_id"])
            if not parent:
                raise HTTPException(status_code=404, detail="Parent category not found")
        
        category.parent_id = update_data["parent_id"]
    
    # Update other fields
    if "icon" in update_data:
        category.icon = update_data["icon"]
    if "color" in update_data:
        category.color = update_data["color"]
    if "is_custom" in update_data:
        category.is_custom = update_data["is_custom"]
    if "is_visible" in update_data:
        category.is_visible = update_data["is_visible"]
    
    # Handle translations
    if "translations" in update_data and update_data["translations"]:
        # Get existing translations
        existing_translations = {t.language_code: t for t in category.translations}
        
        for translation_data in update_data["translations"]:
            language_code = translation_data.get("language_code")
            name = translation_data.get("name")
            
            if language_code in existing_translations:
                # Update existing translation
                existing_translations[language_code].name = name
            else:
                # Create new translation
                new_translation = CategoryTranslation(
                    category_id=category.id,
                    language_code=language_code,
                    name=name
                )
                session.add(new_translation)
    
    session.add(category)
    session.commit()
    session.refresh(category)
    
    return category


@router.delete("/{category_id}", response_model=Message)
def delete_category(
    category_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Delete a category.
    """
    category = session.get(PECSCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    session.delete(category)
    session.commit()
    
    return Message(message="Category deleted successfully")


@router.post("/{category_id}/pecs/{pecs_id}", response_model=Message)
def add_pecs_to_category(
    category_id: UUID,
    pecs_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Associate a PECS with a category.
    """
    # Verify category exists
    category = session.get(PECSCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Verify PECS exists
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    # Check if association already exists
    existing = session.exec(
        select(PECSCategoryItem).where(
            PECSCategoryItem.category_id == category_id,
            PECSCategoryItem.pecs_id == pecs_id
        )
    ).first()
    
    if existing:
        return Message(message="PECS is already in this category")
    
    # Create association
    category_item = PECSCategoryItem(
        category_id=category_id,
        pecs_id=pecs_id
    )
    
    session.add(category_item)
    session.commit()
    
    return Message(message="PECS added to category successfully")


@router.delete("/{category_id}/pecs/{pecs_id}", response_model=Message)
def remove_pecs_from_category(
    category_id: UUID,
    pecs_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Remove a PECS from a category.
    """
    # Verify association exists
    association = session.exec(
        select(PECSCategoryItem).where(
            PECSCategoryItem.category_id == category_id,
            PECSCategoryItem.pecs_id == pecs_id
        )
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="PECS is not in this category")
    
    # Remove association
    session.delete(association)
    session.commit()
    
    return Message(message="PECS removed from category successfully")
