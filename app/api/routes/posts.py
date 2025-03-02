import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Post, PostCreate, PostPublic, PostsPublic, PostUpdate, Message

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/", response_model=PostsPublic)
def read_posts(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve posts.
    """
    # If user is superuser, can see all posts
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Post)
        count = session.exec(count_statement).one()
        statement = select(Post).offset(skip).limit(limit)
        posts = session.exec(statement).all()
    else:
        # Otherwise, can only see own posts
        count_statement = (
            select(func.count())
            .select_from(Post)
            .where(Post.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Post)
            .where(Post.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        posts = session.exec(statement).all()

    return PostsPublic(data=posts, count=count)


@router.get("/hello-world", response_model=Message)
def hello_world(session: SessionDep) -> Message:
    """
    Simple hello world endpoint for testing.
    This endpoint does not require authentication but uses a database session.
    """
    return Message(message="Hello World11!")


@router.get("/{id}", response_model=PostPublic)
def read_post(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get post by ID.
    """
    post = session.get(Post, id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not current_user.is_superuser and (post.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return post


@router.post("/", response_model=PostPublic)
def create_post(
    *, session: SessionDep, current_user: CurrentUser, post_in: PostCreate
) -> Any:
    """
    Create new post.
    """
    post = Post.model_validate(post_in, update={"owner_id": current_user.id})
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


@router.put("/{id}", response_model=PostPublic)
def update_post(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    post_in: PostUpdate,
) -> Any:
    """
    Update a post.
    """
    post = session.get(Post, id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not current_user.is_superuser and (post.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = post_in.model_dump(exclude_unset=True)
    post.sqlmodel_update(update_dict)
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


@router.delete("/{id}")
def delete_post(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a post.
    """
    post = session.get(Post, id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not current_user.is_superuser and (post.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(post)
    session.commit()
    return Message(message="Post deleted successfully")
