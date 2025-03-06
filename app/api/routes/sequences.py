import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from sqlmodel import select, func

from app.api.deps import SessionDep, CurrentUser
from app.models import (
    SequenceGroup, SequenceGroupCreate, SequenceGroupUpdate, SequenceGroupRead,
    Sequence, SequenceCreate, SequenceUpdate, SequenceRead,
    SequenceItem, SequenceItemCreate, SequenceItemUpdate, SequenceItemRead,
    Pictogram, Message
)

router = APIRouter(tags=["sequences"])

# SequenceGroup routes
@router.get("/groups/", response_model=List[SequenceGroupRead])
def read_sequence_groups(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve sequence groups.
    """
    query = select(SequenceGroup)
    
    # Filter by user if not superuser
    if not current_user.is_superuser:
        query = query.where(SequenceGroup.created_by == current_user.id)
    
    # Order by display_order
    query = query.order_by(SequenceGroup.display_order)
    
    groups = session.exec(query.offset(skip).limit(limit)).all()
    return groups


@router.post("/groups/", response_model=SequenceGroupRead)
def create_sequence_group(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_in: SequenceGroupCreate,
):
    """
    Create new sequence group.
    """
    # Set created_by if not provided
    if group_in.created_by is None:
        group_in.created_by = current_user.id
    
    # Create the group
    group = SequenceGroup.model_validate(group_in.model_dump())
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


@router.get("/groups/{group_id}", response_model=SequenceGroupRead)
def read_sequence_group(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
):
    """
    Get sequence group by ID.
    """
    group = session.get(SequenceGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Sequence group not found")
    
    # Check permissions
    if not current_user.is_superuser and group.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return group


@router.put("/groups/{group_id}", response_model=SequenceGroupRead)
def update_sequence_group(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
    group_in: SequenceGroupUpdate,
):
    """
    Update a sequence group.
    """
    group = session.get(SequenceGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Sequence group not found")
    
    # Check permissions
    if not current_user.is_superuser and group.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update group attributes
    update_data = group_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)
    
    group.updated_at = func.now()
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


@router.delete("/groups/{group_id}", response_model=Message)
def delete_sequence_group(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID,
):
    """
    Delete a sequence group.
    """
    group = session.get(SequenceGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Sequence group not found")
    
    # Check permissions
    if not current_user.is_superuser and group.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Delete the group (sequences will be deleted automatically due to cascade)
    session.delete(group)
    session.commit()
    return Message(message="Sequence group deleted successfully")


# Sequence routes
@router.get("/", response_model=List[SequenceRead])
def read_sequences(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    group_id: Optional[uuid.UUID] = None,
    is_favorite: Optional[bool] = None,
):
    """
    Retrieve sequences with optional filtering.
    """
    query = select(Sequence)
    
    # Apply filters if provided
    if group_id:
        query = query.where(Sequence.group_id == group_id)
    
    if is_favorite is not None:
        query = query.where(Sequence.is_favorite == is_favorite)
    
    # Filter by user if not superuser
    if not current_user.is_superuser:
        query = query.where(Sequence.created_by == current_user.id)
    
    # Order by display_order
    query = query.order_by(Sequence.display_order)
    
    sequences = session.exec(query.offset(skip).limit(limit)).all()
    return sequences


@router.post("/", response_model=SequenceRead)
def create_sequence(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    sequence_in: SequenceCreate,
):
    """
    Create new sequence.
    """
    # Set created_by if not provided
    if sequence_in.created_by is None:
        sequence_in.created_by = current_user.id
    
    # Check if group exists if provided
    if sequence_in.group_id:
        group = session.get(SequenceGroup, sequence_in.group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Sequence group not found")
        
        # Check permissions for the group
        if not current_user.is_superuser and group.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions for this group")
    
    # Create the sequence
    sequence_data = sequence_in.model_dump(exclude={"items"})
    sequence = Sequence.model_validate(sequence_data)
    session.add(sequence)
    session.commit()
    session.refresh(sequence)
    
    # Add items if provided
    if sequence_in.items:
        for item_data in sequence_in.items:
            # Verify pictogram exists
            pictogram_id = item_data.get("pictogram_id")
            if not pictogram_id:
                continue
                
            pictogram = session.get(Pictogram, pictogram_id)
            if not pictogram:
                session.delete(sequence)
                session.commit()
                raise HTTPException(status_code=404, detail=f"Pictogram with ID {pictogram_id} not found")
            
            # Create sequence item
            sequence_item = SequenceItem(
                sequence_id=sequence.id,
                pictogram_id=pictogram_id,
                position=item_data.get("position", 0)
            )
            session.add(sequence_item)
        
        session.commit()
        session.refresh(sequence)
    
    return sequence


@router.get("/{sequence_id}", response_model=SequenceRead)
def read_sequence(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    sequence_id: uuid.UUID,
):
    """
    Get sequence by ID.
    """
    sequence = session.get(Sequence, sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    # Check permissions
    if not current_user.is_superuser and sequence.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return sequence


@router.put("/{sequence_id}", response_model=SequenceRead)
def update_sequence(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    sequence_id: uuid.UUID,
    sequence_in: SequenceUpdate,
):
    """
    Update a sequence.
    """
    sequence = session.get(Sequence, sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    # Check permissions
    if not current_user.is_superuser and sequence.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if new group exists if provided
    if sequence_in.group_id is not None:
        if sequence_in.group_id:  # Not None and not empty
            group = session.get(SequenceGroup, sequence_in.group_id)
            if not group:
                raise HTTPException(status_code=404, detail="Sequence group not found")
            
            # Check permissions for the new group
            if not current_user.is_superuser and group.created_by != current_user.id:
                raise HTTPException(status_code=403, detail="Not enough permissions for this group")
    
    # Update sequence attributes
    update_data = sequence_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sequence, key, value)
    
    sequence.updated_at = func.now()
    session.add(sequence)
    session.commit()
    session.refresh(sequence)
    return sequence


@router.delete("/{sequence_id}", response_model=Message)
def delete_sequence(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    sequence_id: uuid.UUID,
):
    """
    Delete a sequence.
    """
    sequence = session.get(Sequence, sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    # Check permissions
    if not current_user.is_superuser and sequence.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Delete the sequence (items will be deleted automatically due to cascade)
    session.delete(sequence)
    session.commit()
    return Message(message="Sequence deleted successfully")


# SequenceItem routes
@router.get("/{sequence_id}/items/", response_model=List[SequenceItemRead])
def read_sequence_items(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    sequence_id: uuid.UUID,
):
    """
    Retrieve items for a sequence.
    """
    # Check if sequence exists and user has permissions
    sequence = session.get(Sequence, sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    if not current_user.is_superuser and sequence.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get items ordered by position
    query = select(SequenceItem).where(SequenceItem.sequence_id == sequence_id).order_by(SequenceItem.position)
    items = session.exec(query).all()
    return items


@router.post("/{sequence_id}/items/", response_model=SequenceItemRead)
def create_sequence_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    sequence_id: uuid.UUID,
    item_in: SequenceItemCreate,
):
    """
    Add an item to a sequence.
    """
    # Check if sequence exists and user has permissions
    sequence = session.get(Sequence, sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    if not current_user.is_superuser and sequence.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if pictogram exists
    pictogram = session.get(Pictogram, item_in.pictogram_id)
    if not pictogram:
        raise HTTPException(status_code=404, detail="Pictogram not found")
    
    # Create the item
    item = SequenceItem.model_validate(item_in.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{sequence_id}/items/{item_id}", response_model=SequenceItemRead)
def update_sequence_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    sequence_id: uuid.UUID,
    item_id: uuid.UUID,
    item_in: SequenceItemUpdate,
):
    """
    Update a sequence item.
    """
    # Check if sequence exists and user has permissions
    sequence = session.get(Sequence, sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    if not current_user.is_superuser and sequence.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if item exists and belongs to the sequence
    item = session.get(SequenceItem, item_id)
    if not item or item.sequence_id != sequence_id:
        raise HTTPException(status_code=404, detail="Sequence item not found")
    
    # Check if new pictogram exists if provided
    if item_in.pictogram_id is not None:
        pictogram = session.get(Pictogram, item_in.pictogram_id)
        if not pictogram:
            raise HTTPException(status_code=404, detail="Pictogram not found")
    
    # Update item attributes
    update_data = item_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{sequence_id}/items/{item_id}", response_model=Message)
def delete_sequence_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    sequence_id: uuid.UUID,
    item_id: uuid.UUID,
):
    """
    Delete a sequence item.
    """
    # Check if sequence exists and user has permissions
    sequence = session.get(Sequence, sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    if not current_user.is_superuser and sequence.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if item exists and belongs to the sequence
    item = session.get(SequenceItem, item_id)
    if not item or item.sequence_id != sequence_id:
        raise HTTPException(status_code=404, detail="Sequence item not found")
    
    # Delete the item
    session.delete(item)
    session.commit()
    return Message(message="Sequence item deleted successfully")


@router.post("/{sequence_id}/reorder", response_model=Message)
def reorder_sequence_items(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    sequence_id: uuid.UUID,
    item_order: List[Dict[str, Any]],  # List of {id: uuid, position: int}
):
    """
    Reorder items in a sequence.
    """
    # Check if sequence exists and user has permissions
    sequence = session.get(Sequence, sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    if not current_user.is_superuser and sequence.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update positions
    for order_data in item_order:
        item_id = order_data.get("id")
        position = order_data.get("position")
        
        if not item_id or position is None:
            continue
        
        # Check if item exists and belongs to the sequence
        item = session.get(SequenceItem, item_id)
        if not item or item.sequence_id != sequence_id:
            continue
        
        # Update position
        item.position = position
        session.add(item)
    
    session.commit()
    return Message(message="Sequence items reordered successfully")