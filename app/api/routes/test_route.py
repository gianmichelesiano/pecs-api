from fastapi import APIRouter
from app.models import Message

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/hello", response_model=Message)
def hello_world() -> Message:
    """
    Simple test endpoint that returns a hello world message.
    """
    return Message(message="Hello World!")
