from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select, Session, func

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Collection, CollectionCreate, CollectionRead, CollectionUpdate,
    CollectionTranslation, CollectionTranslationCreate, CollectionTranslationRead, CollectionTranslationUpdate,
    PhraseCollection,
    Phrase, PhraseRead,
    PECS, PhrasePECSRead,
    Message
)

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/", response_model=List[CollectionRead])
def get_all_collections(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve all collections.
    """
    query = select(Collection).offset(skip).limit(limit)
    collections = session.exec(query).all()
    
    # Add phrase count for each collection
    result = []
    for collection in collections:
        # Count phrases in this collection
        phrase_count_query = select(func.count()).select_from(PhraseCollection).where(
            PhraseCollection.collection_id == collection.id
        )
        phrase_count = session.exec(phrase_count_query).one()
        
        # Create a CollectionRead object with phrase_count
        collection_read = CollectionRead(
            id=collection.id,
            created_at=collection.created_at,
            user_id=collection.user_id,
            is_custom=collection.is_custom,
            is_visible=collection.is_visible,
            name_custom=collection.name_custom,
            icon=collection.icon,
            color=collection.color,
            translations=collection.translations,
            phrase_count=phrase_count
        )
        
        result.append(collection_read)
    
    return result


@router.get("/language/{code}", response_model=List[CollectionRead])
def get_collections_by_language(
    code: str,
    session: SessionDep,
    skip: int = 0,
    limit: Optional[int] = None,
    name: Optional[str] = None
) -> Any:
    """
    Retrieve collections in a specific language.
    """
    # Build the query
    query = select(Collection).join(CollectionTranslation).where(
        CollectionTranslation.language_code == code
    )
    
    # Add name filter if provided
    if name:
        query = query.where(CollectionTranslation.name == name)
    
    # Add pagination
    query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)
    
    # Execute query
    collections = session.exec(query).all()
    
    # Add phrase count for each collection
    result = []
    for collection in collections:
        # Count phrases in this collection
        phrase_count_query = select(func.count()).select_from(PhraseCollection).where(
            PhraseCollection.collection_id == collection.id
        )
        phrase_count = session.exec(phrase_count_query).one()
        
        # Create a CollectionRead object with phrase_count
        collection_read = CollectionRead(
            id=collection.id,
            created_at=collection.created_at,
            user_id=collection.user_id,
            is_custom=collection.is_custom,
            is_visible=collection.is_visible,
            name_custom=collection.name_custom,
            icon=collection.icon,
            color=collection.color,
            translations=collection.translations,
            phrase_count=phrase_count
        )
        
        result.append(collection_read)
    
    return result


@router.get("/{collection_id}", response_model=CollectionRead)
def get_collection(
    collection_id: UUID,
    session: SessionDep
) -> Any:
    """
    Retrieve a specific collection by ID.
    """
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Count phrases in this collection
    phrase_count_query = select(func.count()).select_from(PhraseCollection).where(
        PhraseCollection.collection_id == collection.id
    )
    phrase_count = session.exec(phrase_count_query).one()
    
    # Create a CollectionRead object with phrase_count
    collection_read = CollectionRead(
        id=collection.id,
        created_at=collection.created_at,
        user_id=collection.user_id,
        is_custom=collection.is_custom,
        is_visible=collection.is_visible,
        name_custom=collection.name_custom,
        icon=collection.icon,
        color=collection.color,
        translations=collection.translations,
        phrase_count=phrase_count
    )
    
    return collection_read


@router.get("/{collection_id}/phrases", response_model=List[PhraseRead])
def get_phrases_in_collection(
    collection_id: UUID,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve all phrases in a specific collection.
    """
    # Verify collection exists
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Get phrases in this collection
    query = select(Phrase).join(PhraseCollection).where(
        PhraseCollection.collection_id == collection_id
    ).offset(skip).limit(limit)
    
    phrases = session.exec(query).all()
    
    # Create PhraseRead objects with enhanced PECS info
    result = []
    for phrase in phrases:
        # Create a new list for enhanced pecs_items
        enhanced_pecs_items = []
        
        for pecs_item in phrase.pecs_items:
            pecs = session.get(PECS, pecs_item.pecs_id)
            pecs_info = None
            if pecs:
                # Get first translation if available
                translation = None
                if pecs.translations and len(pecs.translations) > 0:
                    translation = pecs.translations[0]
                
                pecs_info = {
                    "id": pecs.id,
                    "image_url": pecs.image_url,
                    "name": translation.name if translation else None,
                    "language_code": translation.language_code if translation else None
                }
            
            # Create a new PhrasePECSRead object with pecs_info
            enhanced_pecs_items.append(PhrasePECSRead(
                phrase_id=pecs_item.phrase_id,
                pecs_id=pecs_item.pecs_id,
                position=pecs_item.position,
                pecs_info=pecs_info
            ))
        
        # Create a PhraseRead object with the enhanced pecs_items
        phrase_read = PhraseRead(
            id=phrase.id,
            created_at=phrase.created_at,
            user_id=phrase.user_id,
            translations=phrase.translations,
            pecs_items=enhanced_pecs_items
        )
        
        result.append(phrase_read)
    
    return result


@router.post("/", response_model=CollectionRead)
def create_collection(
    collection_in: CollectionCreate,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Create a new collection.
    """
    # Create collection
    collection = Collection(
        user_id=current_user.id,
        is_custom=collection_in.is_custom,
        is_visible=collection_in.is_visible,
        name_custom=collection_in.name_custom,
        icon=collection_in.icon,
        color=collection_in.color
    )
    
    session.add(collection)
    session.commit()
    session.refresh(collection)
    
    # Add translations if provided
    if collection_in.translations:
        for translation_data in collection_in.translations:
            translation = CollectionTranslation(
                collection_id=collection.id,
                language_code=translation_data.get("language_code"),
                name=translation_data.get("name")
            )
            session.add(translation)
        
        session.commit()
        session.refresh(collection)
    
    # Add phrases if provided
    if collection_in.phrase_ids:
        for phrase_id in collection_in.phrase_ids:
            # Verify phrase exists
            phrase = session.get(Phrase, phrase_id)
            if not phrase:
                continue  # Skip invalid phrase
            
            phrase_collection = PhraseCollection(
                phrase_id=phrase_id,
                collection_id=collection.id
            )
            session.add(phrase_collection)
        
        session.commit()
        session.refresh(collection)
    
    # Count phrases in this collection
    phrase_count_query = select(func.count()).select_from(PhraseCollection).where(
        PhraseCollection.collection_id == collection.id
    )
    phrase_count = session.exec(phrase_count_query).one()
    
    # Create a CollectionRead object with phrase_count
    collection_read = CollectionRead(
        id=collection.id,
        created_at=collection.created_at,
        user_id=collection.user_id,
        is_custom=collection.is_custom,
        is_visible=collection.is_visible,
        name_custom=collection.name_custom,
        icon=collection.icon,
        color=collection.color,
        translations=collection.translations,
        phrase_count=phrase_count
    )
    
    return collection_read


@router.put("/{collection_id}", response_model=CollectionRead)
def update_collection(
    collection_id: UUID,
    collection_in: CollectionUpdate,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Update a collection.
    """
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Check if user has permission to update
    if collection.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update collection fields
    update_data = collection_in.model_dump(exclude_unset=True)
    
    # Update basic fields
    if "is_custom" in update_data:
        collection.is_custom = update_data["is_custom"]
    if "is_visible" in update_data:
        collection.is_visible = update_data["is_visible"]
    if "name_custom" in update_data:
        collection.name_custom = update_data["name_custom"]
    if "icon" in update_data:
        collection.icon = update_data["icon"]
    if "color" in update_data:
        collection.color = update_data["color"]
    
    # Handle translations
    if "translations" in update_data and update_data["translations"]:
        # Get existing translations
        existing_translations = {t.language_code: t for t in collection.translations}
        
        for translation_data in update_data["translations"]:
            language_code = translation_data.get("language_code")
            name = translation_data.get("name")
            
            if language_code in existing_translations:
                # Update existing translation
                existing_translations[language_code].name = name
            else:
                # Create new translation
                new_translation = CollectionTranslation(
                    collection_id=collection.id,
                    language_code=language_code,
                    name=name
                )
                session.add(new_translation)
    
    # Handle phrases
    if "phrase_ids" in update_data and update_data["phrase_ids"]:
        # Remove existing phrase associations
        existing_items = session.exec(
            select(PhraseCollection).where(PhraseCollection.collection_id == collection.id)
        ).all()
        
        for item in existing_items:
            session.delete(item)
        
        # Add new phrase associations
        for phrase_id in update_data["phrase_ids"]:
            # Verify phrase exists
            phrase = session.get(Phrase, phrase_id)
            if not phrase:
                continue  # Skip invalid phrase
            
            phrase_collection = PhraseCollection(
                phrase_id=phrase_id,
                collection_id=collection.id
            )
            session.add(phrase_collection)
    
    session.add(collection)
    session.commit()
    session.refresh(collection)
    
    # Count phrases in this collection
    phrase_count_query = select(func.count()).select_from(PhraseCollection).where(
        PhraseCollection.collection_id == collection.id
    )
    phrase_count = session.exec(phrase_count_query).one()
    
    # Create a CollectionRead object with phrase_count
    collection_read = CollectionRead(
        id=collection.id,
        created_at=collection.created_at,
        user_id=collection.user_id,
        is_custom=collection.is_custom,
        is_visible=collection.is_visible,
        name_custom=collection.name_custom,
        icon=collection.icon,
        color=collection.color,
        translations=collection.translations,
        phrase_count=phrase_count
    )
    
    return collection_read


@router.delete("/{collection_id}", response_model=Message)
def delete_collection(
    collection_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Delete a collection.
    """
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Check if user has permission to delete
    if collection.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    session.delete(collection)
    session.commit()
    
    return Message(message="Collection deleted successfully")


@router.post("/{collection_id}/phrases/{phrase_id}", response_model=Message)
def add_phrase_to_collection(
    collection_id: UUID,
    phrase_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Add a phrase to a collection.
    """
    # Verify collection exists
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Check if user has permission
    if collection.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify phrase exists
    phrase = session.get(Phrase, phrase_id)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    # Check if association already exists
    existing = session.exec(
        select(PhraseCollection).where(
            PhraseCollection.collection_id == collection_id,
            PhraseCollection.phrase_id == phrase_id
        )
    ).first()
    
    if existing:
        return Message(message="Phrase is already in this collection")
    
    # Create association
    phrase_collection = PhraseCollection(
        collection_id=collection_id,
        phrase_id=phrase_id
    )
    
    session.add(phrase_collection)
    session.commit()
    
    return Message(message="Phrase added to collection successfully")


@router.delete("/{collection_id}/phrases/{phrase_id}", response_model=Message)
def remove_phrase_from_collection(
    collection_id: UUID,
    phrase_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Remove a phrase from a collection.
    """
    # Verify collection exists
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Check if user has permission
    if collection.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify association exists
    association = session.exec(
        select(PhraseCollection).where(
            PhraseCollection.collection_id == collection_id,
            PhraseCollection.phrase_id == phrase_id
        )
    ).first()
    
    if not association:
        raise HTTPException(status_code=404, detail="Phrase is not in this collection")
    
    # Remove association
    session.delete(association)
    session.commit()
    
    return Message(message="Phrase removed from collection successfully")
