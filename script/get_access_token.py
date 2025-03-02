#!/usr/bin/env python3
"""
Script to generate an access token for a user.
"""
import sys
from datetime import timedelta, datetime, timezone

from sqlmodel import Session

from app import crud
from app.core.db import engine
from app.core.security import create_access_token
from app.core.config import settings

def get_access_token(email: str, password: str) -> tuple[str, datetime]:
    """
    Authenticate a user and generate an access token.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        Tuple containing:
        - Access token as a string
        - Expiration datetime
    
    Raises:
        ValueError: If authentication fails
    """
    with Session(engine) as session:
        # Authenticate the user
        user = crud.authenticate(session=session, email=email, password=password)
        
        if not user:
            raise ValueError("Authentication failed: Incorrect email or password")
        
        if not user.is_active:
            raise ValueError("Authentication failed: User is inactive")
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expiration_time = datetime.now(timezone.utc) + access_token_expires
        access_token = create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        return access_token, expiration_time

def main():
    """Main function to run the script."""
    # Use the credentials from settings if not provided as arguments
    email = settings.FIRST_SUPERUSER
    password = settings.FIRST_SUPERUSER_PASSWORD
    
    try:
        token, expiration_time = get_access_token(email, password)
        
        # Calculate validity period in days, hours, minutes
        validity_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        days = validity_minutes // (24 * 60)
        remaining_minutes = validity_minutes % (24 * 60)
        hours = remaining_minutes // 60
        minutes = remaining_minutes % 60
        
        print("\nAccess Token:")
        print(token)
        print("\nToken Validity:")
        print(f"- Valid for: {days} days, {hours} hours, {minutes} minutes")
        print(f"- Expires at: {expiration_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("\nUse this token in the Authorization header as:")
        print(f"Bearer {token}")
        print("\nOr use it in Swagger UI by clicking 'Authorize' and entering:")
        print(f"Bearer {token}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
