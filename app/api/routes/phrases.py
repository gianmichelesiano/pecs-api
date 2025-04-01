from typing import Any, List, Optional
from uuid import UUID


from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import select, Session

from app.api.deps import CurrentUser, SessionDep
from app.models import (Collection,
    Phrase, PhraseCreate, PhraseRead, PhraseUpdate,
    PhraseTranslation, PhraseTranslationCreate, PhraseTranslationRead, PhraseTranslationUpdate,
    PhrasePECS, PhrasePECSCreate, PhrasePECSRead, PhrasePECSUpdate, PECSOutput, PECSInput,
    PECS, PECSRead,
    PhraseCollection,
    Message
)
from pydantic import BaseModel
from app.services.token_phrase import token_2_phrase

router = APIRouter(prefix="/phrases", tags=["phrases"])


class TransformPecsRequest(BaseModel):
    pecs: List[PECSInput]
    language: str

class ImageURLResponse(BaseModel):
    image_url: str


@router.get("/", response_model=List[PhraseRead])
def get_all_phrases(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve all phrases.
    """
    query = select(Phrase).offset(skip).limit(limit)
    phrases = session.exec(query).all()
    
    # Create PhraseRead objects with enhanced PECS info
    result = []
    for phrase in phrases:
        # Get the language code from the phrase translations
        language_code = None
        if phrase.translations and len(phrase.translations) > 0:
            language_code = phrase.translations[0].language_code
        print("language_code", language_code)
        
        # Create a new list for enhanced pecs_items
        enhanced_pecs_items = []
        
        for pecs_item in phrase.pecs_items:
            pecs = session.get(PECS, pecs_item.pecs_id)
            pecs_info = None
            if pecs:
                # Try to get translation in the same language as the phrase
                translation = None
                if pecs.translations and len(pecs.translations) > 0:
                    # First try to find a translation with the same language code
                    if language_code:
                        print("Cercando traduzione in lingua:", language_code)
                        for t in pecs.translations:
                            print("Traduzione disponibile:", t.language_code, t.name)
                            if t.language_code == language_code:
                                translation = t
                                print("Trovata traduzione in lingua:", language_code)
                                break
                    
                    # If no translation found with the same language code, use the first one
                    if not translation:
                        translation = pecs.translations[0]
                        print("Nessuna traduzione trovata in lingua:", language_code, "usando:", translation.language_code)
                
                # Costruisci pecs_info con language_code della frase, anche se la traduzione è in un'altra lingua
                pecs_info = {
                    "id": pecs.id,
                    "image_url": pecs.image_url,
                    "name": translation.name if translation else None,
                    "language_code": language_code if language_code else (translation.language_code if translation else None)
                }
                print("pecs_info costruito:", pecs_info)
            
            # Create a new PhrasePECSRead object with pecs_info
            enhanced_pecs_items.append(PhrasePECSRead(
                phrase_id=pecs_item.phrase_id,
                pecs_id=pecs_item.pecs_id,
                position=pecs_item.position,
                pecs_info=pecs_info,
                origin=pecs_item.origin if hasattr(pecs_item, 'origin') else None
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


@router.get("/language/{code}", response_model=List[PhraseRead])
def get_phrases_by_language(
    code: str,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve phrases in a specific language.
    """
    query = select(Phrase).join(PhraseTranslation).where(
        PhraseTranslation.language_code == code
    ).offset(skip).limit(limit)
    
    phrases = session.exec(query).all()
    
    # Create PhraseRead objects with enhanced PECS info
    result = []
    for phrase in phrases:
        # Use the provided language code
        language_code = code
        
        # Create a new list for enhanced pecs_items
        enhanced_pecs_items = []
        
        for pecs_item in phrase.pecs_items:
            pecs = session.get(PECS, pecs_item.pecs_id)
            pecs_info = None
            if pecs:
                # Try to get translation in the same language as the phrase
                translation = None
                if pecs.translations and len(pecs.translations) > 0:
                    # First try to find a translation with the same language code
                    if language_code:
                        for t in pecs.translations:
                            if t.language_code == language_code:
                                translation = t
                                break
                    
                    # If no translation found with the same language code, use the first one
                    if not translation:
                        translation = pecs.translations[0]
                
            # Qui è dove impostiamo il language_code nel pecs_info
            # Nota: usiamo il language_code della frase (it), non quello della traduzione PECS (de)
            pecs_info = {
                "id": pecs.id,
                "image_url": pecs.image_url,
                "name": translation.name if translation else None,
                "language_code": language_code if language_code else (translation.language_code if translation else None)
            }
            print("IMPORTANTE - pecs_info costruito:", pecs_info)
            print("IMPORTANTE - language_code della frase:", language_code)
            print("IMPORTANTE - language_code della traduzione PECS:", translation.language_code if translation else None)
            
            # Create a new PhrasePECSRead object with pecs_info
            enhanced_pecs_items.append(PhrasePECSRead(
                phrase_id=pecs_item.phrase_id,
                pecs_id=pecs_item.pecs_id,
                position=pecs_item.position,
                pecs_info=pecs_info,
                origin=pecs_item.origin if hasattr(pecs_item, 'origin') else None
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


@router.get("/{phrase_id}", response_model=PhraseRead)
def get_phrase(
    phrase_id: UUID,
    session: SessionDep
) -> Any:
    """
    Retrieve a specific phrase by ID.
    """
    phrase = session.get(Phrase, phrase_id)
    print("phrase---------", phrase)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    # Get the language code from the phrase translations
    language_code = None
    if phrase.translations and len(phrase.translations) > 0:
        language_code = phrase.translations[0].language_code
    print("language_code", language_code)
    # Create a new list for enhanced pecs_items
    enhanced_pecs_items = []
    
    for pecs_item in phrase.pecs_items:
        print(pecs_item)
        pecs = session.get(PECS, pecs_item.pecs_id)
        print("pecs->", pecs)
        print("pecs-nnnnn>", pecs.translations)
        
        pecs_info = None
        if pecs:
            # Try to get translation in the same language as the phrase
            translation = None
            if pecs.translations and len(pecs.translations) > 0:
                # First try to find a translation with the same language code
                if language_code:
                    for t in pecs.translations:
                        if t.language_code == language_code:
                            translation = t
                            break
                
                # If no translation found with the same language code, use the first one
                if not translation:
                    translation = pecs.translations[0]
            
            # Qui è dove impostiamo il language_code nel pecs_info
            # Nota: usiamo il language_code della frase (it), non quello della traduzione PECS (de)
            pecs_info = {
                "id": pecs.id,
                "image_url": pecs.image_url,
                "name": translation.name if translation else None,
                "language_code": language_code if language_code else (translation.language_code if translation else None)
            }
            print("IMPORTANTE - pecs_info costruito:", pecs_info)
            print("IMPORTANTE - language_code della frase:", language_code)
            print("IMPORTANTE - language_code della traduzione PECS:", translation.language_code if translation else None)
            
        
        # Create a new PhrasePECSRead object with pecs_info
        enhanced_pecs_items.append(PhrasePECSRead(
            phrase_id=pecs_item.phrase_id,
            pecs_id=pecs_item.pecs_id,
            position=pecs_item.position,
            pecs_info=pecs_info,
            origin=pecs_item.origin if hasattr(pecs_item, 'origin') else None
        ))
    
    # Create a PhraseRead object with the enhanced pecs_items
    phrase_read = PhraseRead(
        id=phrase.id,
        created_at=phrase.created_at,
        user_id=phrase.user_id,
        translations=phrase.translations,
        pecs_items=enhanced_pecs_items
    )
    
    return phrase_read


@router.get("/{phrase_id}/pecs", response_model=List[PhrasePECSRead])
def get_pecs_in_phrase(
    phrase_id: UUID,
    session: SessionDep
) -> Any:
    """
    Retrieve all PECS in a specific phrase with their positions.
    """
    # Verify phrase exists
    phrase = session.get(Phrase, phrase_id)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    # Get the language code from the phrase translations
    language_code = None
    if phrase.translations and len(phrase.translations) > 0:
        language_code = phrase.translations[0].language_code
    
    # Get PECS in this phrase with positions
    query = select(PhrasePECS).where(
        PhrasePECS.phrase_id == phrase_id
    ).order_by(PhrasePECS.position)
    
    phrase_pecs = session.exec(query).all()
    
    # Enhance with PECS info
    result = []
    for pp in phrase_pecs:
        pecs = session.get(PECS, pp.pecs_id)
        pecs_info = None
        if pecs:
            # Try to get translation in the same language as the phrase
            translation = None
            if pecs.translations and len(pecs.translations) > 0:
                # First try to find a translation with the same language code
                if language_code:
                    for t in pecs.translations:
                        if t.language_code == language_code:
                            translation = t
                            break
                
                # If no translation found with the same language code, use the first one
                if not translation:
                    translation = pecs.translations[0]
            
            pecs_info = {
                "id": pecs.id,
                "image_url": pecs.image_url,
                "name": translation.name if translation else None,
                "language_code": language_code if language_code else (translation.language_code if translation else None)
            }
            print(pecs_info)
        
        result.append(PhrasePECSRead(
            phrase_id=pp.phrase_id,
            pecs_id=pp.pecs_id,
            position=pp.position,
            pecs_info=pecs_info,
            origin=pp.origin if hasattr(pp, 'origin') else None
        ))
    
    return result


@router.post("/", response_model=PhraseRead)
def create_phrase(
    phrase_in: PhraseCreate,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Create a new phrase.
    """
    # Create phrase
    phrase = Phrase(
        user_id=current_user.id,
        origin=phrase_in.origin if hasattr(phrase_in, 'origin') else None
    )
    # Stampa il payload ricevuto
    print(f"Payload ricevuto: {phrase_in}")
    session.add(phrase)
    session.commit()
    session.refresh(phrase)
    
    # Add translations if provided
    if phrase_in.translations:
        for translation_data in phrase_in.translations:
            translation = PhraseTranslation(
                phrase_id=phrase.id,
                language_code=translation_data.get("language_code"),
                text=translation_data.get("text"),
                audio_url=translation_data.get("audio_url")
            )
            session.add(translation)
        
        session.commit()
        session.refresh(phrase)
    
    # Add PECS items if provided
    if phrase_in.pecs_items:
        for pecs_item in phrase_in.pecs_items:
            # Verify PECS exists
            pecs_id = pecs_item.get("pecs_id")
            
            # Check if pecs_id is a valid UUID
            try:
                # Try to convert to UUID
                uuid_pecs_id = UUID(pecs_id)
                pecs = session.get(PECS, uuid_pecs_id)
            except (ValueError, TypeError):
                # If not a valid UUID, it might be a numeric ID
                # Try to find PECS by image URL which might contain the numeric ID
                query = select(PECS).where(
                    PECS.image_url.contains(f"/{pecs_id}")
                )
                pecs = session.exec(query).first()
            
            if not pecs:
                continue  # Skip invalid PECS
                
            # Get the language code from the phrase translations
            language_code = None
            if phrase_in.translations and len(phrase_in.translations) > 0:
                language_code = phrase_in.translations[0].get("language_code")
            
            # Try to find a PECS with the same image but with a translation in the language of the phrase
            if language_code and pecs.translations and len(pecs.translations) > 0:
                # Check if the current PECS has a translation in the language of the phrase
                has_translation_in_language = False
                for t in pecs.translations:
                    if t.language_code == language_code:
                        has_translation_in_language = True
                        break
                
                # If the current PECS doesn't have a translation in the language of the phrase,
                # try to find another PECS with the same image but with a translation in the language of the phrase
                if not has_translation_in_language:
                    # Get the image URL of the current PECS
                    image_url = pecs.image_url
                    
                    # Find all PECS with the same image URL
                    query = select(PECS).where(
                        PECS.image_url == image_url
                    )
                    all_pecs_with_same_image = session.exec(query).all()
                    
                    # Check if any of them has a translation in the language of the phrase
                    for p in all_pecs_with_same_image:
                        for t in p.translations:
                            if t.language_code == language_code:
                                # Found a PECS with the same image and a translation in the language of the phrase
                                pecs = p
                                print(f"Found a better PECS with translation in {language_code}: {pecs.id}")
                                break
                        else:
                            # Continue the outer loop if the inner loop wasn't broken
                            continue
                        # Break the outer loop if the inner loop was broken
                        break
                
                
            
            # Get origin from pecs_item if provided, otherwise use PECS name in the same language as the phrase
            origin = pecs_item.get("origin")
            if not origin and pecs.translations and len(pecs.translations) > 0:
                # Get the language code from the phrase translations
                language_code = None
                if phrase_in.translations and len(phrase_in.translations) > 0:
                    language_code = phrase_in.translations[0].get("language_code")
                
                # Try to find a translation with the same language code
                translation = None
                if language_code:
                    for t in pecs.translations:
                        if t.language_code == language_code:
                            translation = t
                            break
                
                # If no translation found with the same language code, use the first one
                if not translation:
                    translation = pecs.translations[0]
                
                origin = translation.name
                
            phrase_pecs = PhrasePECS(
                phrase_id=phrase.id,
                pecs_id=pecs.id,  # Use the actual UUID from the found PECS
                position=pecs_item.get("position", 0),
                origin=origin
            )
            session.add(phrase_pecs)
        
        session.commit()
        session.refresh(phrase)
    
    # Add collections if provided
    print(f"DEBUG - collection_ids type: {type(phrase_in.collection_ids)}")
    print(f"DEBUG - collection_ids: {phrase_in.collection_ids}")
    print(f"DEBUG - Raw request data: {phrase_in.model_dump()}")
    
    # Try to handle collection_ids even if they're in a different format
    collection_ids = []
    
    # If collection_ids is directly available
    if phrase_in.collection_ids:
        collection_ids = phrase_in.collection_ids
        print(f"DEBUG - Using direct collection_ids: {collection_ids}")
    
    if collection_ids:
        print(f"DEBUG - Processing {len(collection_ids)} collection IDs")
        for collection_id in collection_ids:
            try:
                # Ensure collection_id is a UUID
                if isinstance(collection_id, str):
                    collection_id = UUID(collection_id)
                    print(f"DEBUG - Converted string to UUID: {collection_id}")
                
                print(f"DEBUG - Processing collection_id: {collection_id}")
                # Verify collection exists
                collection = session.get(Collection, collection_id)
                if not collection:
                    print(f"DEBUG - Collection not found: {collection_id}")
                    continue  # Skip invalid collection
                
                print(f"DEBUG - Collection found: {collection_id}")
                # Create association
                phrase_collection = PhraseCollection(
                    phrase_id=phrase.id,
                    collection_id=collection_id
                )
                session.add(phrase_collection)
                print(f"DEBUG - Added association for phrase {phrase.id} and collection {collection_id}")
            except Exception as e:
                print(f"DEBUG - Error processing collection_id {collection_id}: {str(e)}")
        
        session.commit()
        print(f"DEBUG - Committed associations")
        session.refresh(phrase)
    
    return phrase


@router.put("/{phrase_id}", response_model=PhraseRead)
def update_phrase(
    phrase_id: UUID,
    phrase_in: PhraseUpdate,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Update a phrase.
    """
    phrase = session.get(Phrase, phrase_id)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    # Check if user has permission to update
    if phrase.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update phrase fields
    update_data = phrase_in.model_dump(exclude_unset=True)
    
    # Update origin field if provided
    if "origin" in update_data:
        phrase.origin = update_data["origin"]
    
    # Handle translations
    if "translations" in update_data and update_data["translations"]:
        # Get existing translations
        existing_translations = {t.language_code: t for t in phrase.translations}
        
        for translation_data in update_data["translations"]:
            language_code = translation_data.get("language_code")
            text = translation_data.get("text")
            audio_url = translation_data.get("audio_url")
            
            if language_code in existing_translations:
                # Update existing translation
                if text is not None:
                    existing_translations[language_code].text = text
                if audio_url is not None:
                    existing_translations[language_code].audio_url = audio_url
            else:
                # Create new translation
                new_translation = PhraseTranslation(
                    phrase_id=phrase.id,
                    language_code=language_code,
                    text=text,
                    audio_url=audio_url
                )
                session.add(new_translation)
    
    # Handle PECS items
    if "pecs_items" in update_data and update_data["pecs_items"]:
        # Remove existing PECS items
        existing_items = session.exec(
            select(PhrasePECS).where(PhrasePECS.phrase_id == phrase.id)
        ).all()
        
        for item in existing_items:
            session.delete(item)
        
        # Add new PECS items
        for pecs_item in update_data["pecs_items"]:
            # Verify PECS exists
            pecs_id = pecs_item.get("pecs_id")
            
            # Check if pecs_id is a valid UUID
            try:
                # Try to convert to UUID
                uuid_pecs_id = UUID(pecs_id)
                pecs = session.get(PECS, uuid_pecs_id)
            except (ValueError, TypeError):
                # If not a valid UUID, it might be a numeric ID
                # Try to find PECS by image URL which might contain the numeric ID
                query = select(PECS).where(
                    PECS.image_url.contains(f"/{pecs_id}")
                )
                pecs = session.exec(query).first()
            
            if not pecs:
                continue  # Skip invalid PECS
            
            # Get origin from pecs_item if provided, otherwise use PECS name in the same language as the phrase
            origin = pecs_item.get("origin")
            if not origin and pecs.translations and len(pecs.translations) > 0:
                # Get the language code from the phrase translations
                language_code = None
                for translation_data in update_data.get("translations", []):
                    language_code = translation_data.get("language_code")
                    if language_code:
                        break
                
                if not language_code and phrase.translations and len(phrase.translations) > 0:
                    language_code = phrase.translations[0].language_code
                
                # Try to find a translation with the same language code
                translation = None
                if language_code:
                    for t in pecs.translations:
                        if t.language_code == language_code:
                            translation = t
                            break
                
                # If no translation found with the same language code, use the first one
                if not translation:
                    translation = pecs.translations[0]
                
                origin = translation.name
                
            phrase_pecs = PhrasePECS(
                phrase_id=phrase.id,
                pecs_id=pecs.id,  # Use the actual UUID from the found PECS
                position=pecs_item.get("position", 0),
                origin=origin
            )
            session.add(phrase_pecs)
    
    # Handle collections
    print(f"DEBUG UPDATE - collection_ids in update_data: {update_data.get('collection_ids')}")
    if "collection_ids" in update_data and update_data["collection_ids"]:
        # Remove existing collection associations
        existing_collections = session.exec(
            select(PhraseCollection).where(PhraseCollection.phrase_id == phrase.id)
        ).all()
        
        print(f"DEBUG UPDATE - Removing {len(existing_collections)} existing collection associations")
        for item in existing_collections:
            session.delete(item)
        
        # Add new collection associations
        collection_ids = update_data["collection_ids"]
        print(f"DEBUG UPDATE - Adding {len(collection_ids)} new collection associations")
        
        for collection_id in collection_ids:
            try:
                # Ensure collection_id is a UUID
                if isinstance(collection_id, str):
                    collection_id = UUID(collection_id)
                    print(f"DEBUG UPDATE - Converted string to UUID: {collection_id}")
                
                print(f"DEBUG UPDATE - Processing collection_id: {collection_id}")
                # Verify collection exists
                collection = session.get(Collection, collection_id)
                if not collection:
                    print(f"DEBUG UPDATE - Collection not found: {collection_id}")
                    continue  # Skip invalid collection
                
                print(f"DEBUG UPDATE - Collection found: {collection_id}")
                # Create association
                phrase_collection = PhraseCollection(
                    phrase_id=phrase.id,
                    collection_id=collection_id
                )
                session.add(phrase_collection)
                print(f"DEBUG UPDATE - Added association for phrase {phrase.id} and collection {collection_id}")
            except Exception as e:
                print(f"DEBUG UPDATE - Error processing collection_id {collection_id}: {str(e)}")
    
    session.add(phrase)
    session.commit()
    session.refresh(phrase)
    
    return phrase


@router.delete("/{phrase_id}", response_model=Message)
def delete_phrase(
    phrase_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Delete a phrase.
    """
    phrase = session.get(Phrase, phrase_id)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    # Check if user has permission to delete
    if phrase.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    session.delete(phrase)
    session.commit()
    
    return Message(message="Phrase deleted successfully")


@router.post("/{phrase_id}/pecs/{pecs_id}", response_model=PhrasePECSRead)
def add_pecs_to_phrase(
    phrase_id: UUID,
    pecs_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    position: int = Query(..., description="Position of the PECS in the phrase")
) -> Any:
    """
    Add a PECS to a phrase at a specific position.
    """
    # Verify phrase exists
    phrase = session.get(Phrase, phrase_id)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    # Check if user has permission
    if phrase.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify PECS exists
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    # Check if association already exists
    existing = session.exec(
        select(PhrasePECS).where(
            PhrasePECS.phrase_id == phrase_id,
            PhrasePECS.pecs_id == pecs_id
        )
    ).first()
    
    if existing:
        # Update position
        existing.position = position
        session.add(existing)
        session.commit()
        session.refresh(existing)
        
        # Get the language code from the phrase translations
        language_code = None
        if phrase.translations and len(phrase.translations) > 0:
            language_code = phrase.translations[0].language_code
        
        # Get PECS info
        pecs_info = None
        if pecs:
            # Try to get translation in the same language as the phrase
            translation = None
            if pecs.translations and len(pecs.translations) > 0:
                # First try to find a translation with the same language code
                if language_code:
                    for t in pecs.translations:
                        if t.language_code == language_code:
                            translation = t
                            break
                
                # If no translation found with the same language code, use the first one
                if not translation:
                    translation = pecs.translations[0]
            
            pecs_info = {
                "id": pecs.id,
                "image_url": pecs.image_url,
                "name": translation.name if translation else None,
                "language_code": language_code if language_code else (translation.language_code if translation else None)
            }
        
        return PhrasePECSRead(
            phrase_id=existing.phrase_id,
            pecs_id=existing.pecs_id,
            position=existing.position,
            pecs_info=pecs_info,
            origin=existing.origin if hasattr(existing, 'origin') else None
        )
    
    # Create association with origin in the same language as the phrase
    # Get the language code from the phrase translations
    language_code = None
    if phrase.translations and len(phrase.translations) > 0:
        language_code = phrase.translations[0].language_code
    
    # Get origin in the same language as the phrase
    origin = None
    if pecs.translations and len(pecs.translations) > 0:
        # Try to find a translation with the same language code
        translation = None
        if language_code:
            for t in pecs.translations:
                if t.language_code == language_code:
                    translation = t
                    break
        
        # If no translation found with the same language code, use the first one
        if not translation:
            translation = pecs.translations[0]
        
        origin = translation.name
    
    phrase_pecs = PhrasePECS(
        phrase_id=phrase_id,
        pecs_id=pecs_id,
        position=position,
        origin=origin
    )
    
    session.add(phrase_pecs)
    session.commit()
    session.refresh(phrase_pecs)
    
    # Get the language code from the phrase translations
    language_code = None
    if phrase.translations and len(phrase.translations) > 0:
        language_code = phrase.translations[0].language_code
    
    # Get PECS info
    pecs_info = None
    if pecs:
        # Try to get translation in the same language as the phrase
        translation = None
        if pecs.translations and len(pecs.translations) > 0:
            # First try to find a translation with the same language code
            if language_code:
                for t in pecs.translations:
                    if t.language_code == language_code:
                        translation = t
                        break
            
            # If no translation found with the same language code, use the first one
            if not translation:
                translation = pecs.translations[0]
        
        pecs_info = {
            "id": pecs.id,
            "image_url": pecs.image_url,
            "name": translation.name if translation else None,
            "language_code": language_code if language_code else (translation.language_code if translation else None)
        }
    
    return PhrasePECSRead(
        phrase_id=phrase_pecs.phrase_id,
        pecs_id=phrase_pecs.pecs_id,
        position=phrase_pecs.position,
        pecs_info=pecs_info,
        origin=phrase_pecs.origin if hasattr(phrase_pecs, 'origin') else None
    )


@router.put("/{phrase_id}/pecs/{pecs_id}", response_model=PhrasePECSRead)
def update_pecs_position_in_phrase(
    phrase_id: UUID,
    pecs_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    position: int = Query(..., description="New position of the PECS in the phrase")
) -> Any:
    """
    Update the position of a PECS in a phrase.
    """
    # Verify phrase exists
    phrase = session.get(Phrase, phrase_id)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    # Check if user has permission
    if phrase.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify PECS exists
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    # Check if association exists
    phrase_pecs = session.exec(
        select(PhrasePECS).where(
            PhrasePECS.phrase_id == phrase_id,
            PhrasePECS.pecs_id == pecs_id
        )
    ).first()
    
    if not phrase_pecs:
        raise HTTPException(status_code=404, detail="PECS is not in this phrase")
    
    # Update position
    phrase_pecs.position = position
    session.add(phrase_pecs)
    session.commit()
    session.refresh(phrase_pecs)
    
    # Get the language code from the phrase translations
    language_code = None
    if phrase.translations and len(phrase.translations) > 0:
        language_code = phrase.translations[0].language_code
    
    # Get PECS info
    pecs_info = None
    if pecs:
        # Try to get translation in the same language as the phrase
        translation = None
        if pecs.translations and len(pecs.translations) > 0:
            # First try to find a translation with the same language code
            if language_code:
                for t in pecs.translations:
                    if t.language_code == language_code:
                        translation = t
                        break
            
            # If no translation found with the same language code, use the first one
            if not translation:
                translation = pecs.translations[0]
        
        pecs_info = {
            "id": pecs.id,
            "image_url": pecs.image_url,
            "name": translation.name if translation else None,
            "language_code": language_code if language_code else (translation.language_code if translation else None)
        }
        
    return PhrasePECSRead(
        phrase_id=phrase_pecs.phrase_id,
        pecs_id=phrase_pecs.pecs_id,
        position=phrase_pecs.position,
        pecs_info=pecs_info,
        origin=phrase_pecs.origin if hasattr(phrase_pecs, 'origin') else None
    )


@router.get("/pecs/{pecs_id}/image", response_model=ImageURLResponse)
def get_pecs_image_url(
    pecs_id: UUID,
    session: SessionDep
) -> Any:
    """
    Get the image URL for a specific PECS by ID.
    """
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    return ImageURLResponse(image_url=pecs.image_url)


@router.delete("/{phrase_id}/pecs/{pecs_id}", response_model=Message)
def remove_pecs_from_phrase(
    phrase_id: UUID,
    pecs_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Remove a PECS from a phrase.
    """
    # Verify phrase exists
    phrase = session.get(Phrase, phrase_id)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    # Check if user has permission
    if phrase.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify association exists
    phrase_pecs = session.exec(
        select(PhrasePECS).where(
            PhrasePECS.phrase_id == phrase_id,
            PhrasePECS.pecs_id == pecs_id
        )
    ).first()
    
    if not phrase_pecs:
        raise HTTPException(status_code=404, detail="PECS is not in this phrase")
    
    # Remove association
    session.delete(phrase_pecs)
    session.commit()
    
    return Message(message="PECS removed from phrase successfully")

@router.post("/transform-pecs", response_model=List[PECSOutput])
def transform_pecs_format(
    request: TransformPecsRequest
) -> List[PECSOutput]:
    """
    Transform PECS items from the input format to the output format with tokens and phrases.
    """
    transformed_items = []
    
    sequence = ''
    for item in request.pecs:
        sequence += item.name + ' '

    result = token_2_phrase(sequence, request.language)

    for key, val in result['mapping'].items():
        transformed_item = PECSOutput(
            id=item.id,
            token=key,
            phrase=val,
            position=item.position
        )
        transformed_items.append(transformed_item)
    return transformed_items
