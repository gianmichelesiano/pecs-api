from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import get_db, get_current_active_superuser, SessionDep, CurrentUser
from app.models.nome import Nome, NomeCreate, NomeUpdate
from app.models.user import User
from app.models.pictogram import Pictogram

router = APIRouter(prefix="/nomi", tags=["nomi"])


@router.get("/", response_model=List[Nome])
def read_nomi(
    *,
    db: SessionDep,
    skip: int = 0,
    limit: int = 100,
    lang: Optional[str] = None,
    pictogram_id: Optional[int] = None,
):
    """
    Retrieve nomi (names) with optional filtering.
    """
    query = select(Nome)
    
    # Apply filters if provided
    if lang:
        query = query.where(Nome.lang == lang)
    if pictogram_id:
        query = query.where(Nome.pictogram_id == pictogram_id)
    
    nomi = db.exec(query.offset(skip).limit(limit)).all()
    return nomi


@router.post("/", response_model=Nome)
def create_nome(
    *,
    db: SessionDep,
    nome_in: NomeCreate,
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Create new nome (name) with the specified pictogram_id.
    No validation is performed to check if the pictogram exists.
    """
    # Create the nome directly
    nome = Nome.model_validate(nome_in.model_dump())
    db.add(nome)
    db.commit()
    db.refresh(nome)
    return nome


@router.get("/{nome_id}", response_model=Nome)
def read_nome(
    *,
    db: SessionDep,
    nome_id: int,
):
    """
    Get nome by ID.
    """
    nome = db.get(Nome, nome_id)
    if not nome:
        raise HTTPException(status_code=404, detail="Nome not found")
    return nome


@router.put("/{nome_id}", response_model=Nome)
def update_nome(
    *,
    db: SessionDep,
    nome_id: int,
    nome_in: NomeUpdate,
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Update a nome.
    """
    nome = db.get(Nome, nome_id)
    if not nome:
        raise HTTPException(status_code=404, detail="Nome not found")
    
    # Update nome attributes
    nome_data = nome_in.model_dump(exclude_unset=True)
    for key, value in nome_data.items():
        setattr(nome, key, value)
    
    db.add(nome)
    db.commit()
    db.refresh(nome)
    return nome


@router.delete("/{nome_id}", response_model=Nome)
def delete_nome(
    *,
    db: SessionDep,
    nome_id: int,
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Delete a nome.
    """
    nome = db.get(Nome, nome_id)
    if not nome:
        raise HTTPException(status_code=404, detail="Nome not found")
    
    db.delete(nome)
    db.commit()
    return nome


@router.get("/pictogram/{pictogram_id}", response_model=List[Nome])
def read_nomi_by_pictogram(
    *,
    db: SessionDep,
    pictogram_id: int,
    lang: Optional[str] = None,
):
    """
    Get all nomi for a specific pictogram_id, optionally filtered by language.
    """
    query = select(Nome).where(Nome.pictogram_id == pictogram_id)
    
    if lang:
        query = query.where(Nome.lang == lang)
    
    nomi = db.exec(query).all()
    return nomi


@router.get("/search/", response_model=List[Nome])
def search_nomi(
    *,
    db: SessionDep,
    q: str = Query(..., description="Search query"),
    lang: Optional[str] = None,
):
    """
    Search nomi by name.
    """
    query = select(Nome).where(Nome.name.contains(q))
    
    if lang:
        query = query.where(Nome.lang == lang)
    
    nomi = db.exec(query).all()
    return nomi
