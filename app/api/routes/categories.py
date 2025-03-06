import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from sqlmodel import select, func

from app.api.deps import SessionDep, CurrentUser
from app.models import Category, CategoryCreate, CategoryUpdate, CategoryRead, Message

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=List[CategoryRead])
def read_categories(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    is_custom: Optional[bool] = None,
    is_visible: Optional[bool] = None,
):
    """
    Retrieve categories with optional filtering.
    """
    query = select(Category)
    
    # Apply filters if provided
    if is_custom is not None:
        query = query.where(Category.is_custom == is_custom)
    
    if is_visible is not None:
        query = query.where(Category.is_visible == is_visible)
    
    # Filter by user for custom categories
    if not current_user.is_superuser and is_custom:
        query = query.where(Category.created_by == current_user.id)
    
    # Order by display_order (handle None values)
    query = query.order_by(Category.display_order.nulls_last())
    
    categories = session.exec(query.offset(skip).limit(limit)).all()
    return categories


@router.post("/", response_model=CategoryRead)
def create_category(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    category_in: CategoryCreate,
):
    """
    Create new category.
    """
    # Set created_by if not provided
    if category_in.created_by is None:
        category_in.created_by = current_user.id
    
    # Only superusers can create non-custom categories
    if not category_in.is_custom and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only superusers can create non-custom categories"
        )
    
    # Create the category
    category_data = category_in.model_dump()
    
    # If display_order is not provided, assign a default value
    if category_data.get('display_order') is None:
        # Get the maximum display_order value
        max_order_result = session.exec(
            select(func.max(Category.display_order))
        ).one_or_none()
        
        # Set display_order to max + 1, or 1 if no categories exist
        max_order = max_order_result if max_order_result is not None else 0
        category_data['display_order'] = max_order + 1
    
    category = Category.model_validate(category_data)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryRead)
def read_category(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    category_id: uuid.UUID,
):
    """
    Get category by ID.
    """
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check permissions for custom categories
    if category.is_custom and not current_user.is_superuser and category.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return category


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    category_id: uuid.UUID,
    category_in: CategoryUpdate,
):
    """
    Update a category.
    """
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check permissions
    if not current_user.is_superuser and (category.is_custom and category.created_by != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update category attributes
    update_data = category_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    
    category.updated_at = func.now()
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/{category_id}", response_model=Message)
def delete_category(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    category_id: uuid.UUID,
):
    """
    Delete a category.
    """
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check permissions
    if not current_user.is_superuser and (category.is_custom and category.created_by != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Delete the category (relationships will be deleted automatically due to cascade)
    session.delete(category)
    session.commit()
    return Message(message="Category deleted successfully")