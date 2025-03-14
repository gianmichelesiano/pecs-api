from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, Session

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    FavoritePECS, FavoritePhraseBase, FavoritePhrase,
    PECS, PECSRead, Phrase, PhraseRead,
    Message
)

router = APIRouter(prefix="/users", tags=["favorites"])


@router.get("/{user_id}/favorites/pecs", response_model=List[PECSRead])
def get_favorite_pecs(
    user_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Retrieve all favorite PECS for a user.
    """
    # Check if user has permission
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get favorite PECS
    query = select(PECS).join(FavoritePECS).where(
        FavoritePECS.user_id == user_id
    )
    
    pecs_list = session.exec(query).all()
    return pecs_list


@router.post("/{user_id}/favorites/pecs/{pecs_id}", response_model=Message)
def add_pecs_to_favorites(
    user_id: UUID,
    pecs_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Add a PECS to user's favorites.
    """
    # Check if user has permission
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify PECS exists
    pecs = session.get(PECS, pecs_id)
    if not pecs:
        raise HTTPException(status_code=404, detail="PECS not found")
    
    # Check if already in favorites
    existing = session.exec(
        select(FavoritePECS).where(
            FavoritePECS.user_id == user_id,
            FavoritePECS.pecs_id == pecs_id
        )
    ).first()
    
    if existing:
        return Message(message="PECS is already in favorites")
    
    # Add to favorites
    favorite = FavoritePECS(
        user_id=user_id,
        pecs_id=pecs_id
    )
    
    session.add(favorite)
    session.commit()
    
    return Message(message="PECS added to favorites successfully")


@router.delete("/{user_id}/favorites/pecs/{pecs_id}", response_model=Message)
def remove_pecs_from_favorites(
    user_id: UUID,
    pecs_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Remove a PECS from user's favorites.
    """
    # Check if user has permission
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if in favorites
    favorite = session.exec(
        select(FavoritePECS).where(
            FavoritePECS.user_id == user_id,
            FavoritePECS.pecs_id == pecs_id
        )
    ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="PECS is not in favorites")
    
    # Remove from favorites
    session.delete(favorite)
    session.commit()
    
    return Message(message="PECS removed from favorites successfully")


@router.get("/{user_id}/favorites/phrases", response_model=List[PhraseRead])
def get_favorite_phrases(
    user_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Retrieve all favorite phrases for a user.
    """
    # Check if user has permission
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get favorite phrases
    query = select(Phrase).join(FavoritePhrase).where(
        FavoritePhrase.user_id == user_id
    )
    
    phrases = session.exec(query).all()
    return phrases


@router.post("/{user_id}/favorites/phrases/{phrase_id}", response_model=Message)
def add_phrase_to_favorites(
    user_id: UUID,
    phrase_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Add a phrase to user's favorites.
    """
    # Check if user has permission
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Verify phrase exists
    phrase = session.get(Phrase, phrase_id)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")
    
    # Check if already in favorites
    existing = session.exec(
        select(FavoritePhrase).where(
            FavoritePhrase.user_id == user_id,
            FavoritePhrase.phrase_id == phrase_id
        )
    ).first()
    
    if existing:
        return Message(message="Phrase is already in favorites")
    
    # Add to favorites
    favorite = FavoritePhrase(
        user_id=user_id,
        phrase_id=phrase_id
    )
    
    session.add(favorite)
    session.commit()
    
    return Message(message="Phrase added to favorites successfully")


@router.delete("/{user_id}/favorites/phrases/{phrase_id}", response_model=Message)
def remove_phrase_from_favorites(
    user_id: UUID,
    phrase_id: UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Remove a phrase from user's favorites.
    """
    # Check if user has permission
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if in favorites
    favorite = session.exec(
        select(FavoritePhrase).where(
            FavoritePhrase.user_id == user_id,
            FavoritePhrase.phrase_id == phrase_id
        )
    ).first()
    
    if not favorite:
        raise HTTPException(status_code=404, detail="Phrase is not in favorites")
    
    # Remove from favorites
    session.delete(favorite)
    session.commit()
    
    return Message(message="Phrase removed from favorites successfully")
