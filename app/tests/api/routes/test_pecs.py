import uuid
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import User, PECS, PECSTranslation


def test_create_pecs(
    client: TestClient, superuser_token_headers: Dict[str, str], db: Session
) -> None:
    data = {
        "image_url": "https://example.com/image.jpg",
        "is_custom": True,
        "translations": [
            {
                "language_code": "en",
                "name": "Test PECS"
            },
            {
                "language_code": "it",
                "name": "Test PECS IT"
            }
        ]
    }
    response = client.post(
        f"{settings.API_V1_STR}/pecs/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["image_url"] == data["image_url"]
    assert content["is_custom"] == data["is_custom"]
    assert len(content["translations"]) == 2
    assert "id" in content
    assert "created_at" in content


def test_read_pecs(
    client: TestClient, superuser_token_headers: Dict[str, str], db: Session
) -> None:
    # Create a test PECS
    pecs = PECS(
        image_url="https://example.com/test.jpg",
        is_custom=False
    )
    db.add(pecs)
    db.commit()
    db.refresh(pecs)
    
    # Add a translation
    translation = PECSTranslation(
        pecs_id=pecs.id,
        language_code="en",
        name="Test PECS"
    )
    db.add(translation)
    db.commit()
    
    response = client.get(
        f"{settings.API_V1_STR}/pecs/{pecs.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["image_url"] == pecs.image_url
    assert content["is_custom"] == pecs.is_custom
    assert len(content["translations"]) == 1
    assert content["translations"][0]["language_code"] == "en"
    assert content["translations"][0]["name"] == "Test PECS"


def test_update_pecs(
    client: TestClient, superuser_token_headers: Dict[str, str], db: Session
) -> None:
    # Create a test PECS
    pecs = PECS(
        image_url="https://example.com/old.jpg",
        is_custom=False
    )
    db.add(pecs)
    db.commit()
    db.refresh(pecs)
    
    data = {
        "image_url": "https://example.com/new.jpg",
        "is_custom": True,
        "translations": [
            {
                "language_code": "en",
                "name": "Updated PECS"
            }
        ]
    }
    
    response = client.put(
        f"{settings.API_V1_STR}/pecs/{pecs.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["image_url"] == data["image_url"]
    assert content["is_custom"] == data["is_custom"]
    assert len(content["translations"]) == 1
    assert content["translations"][0]["language_code"] == "en"
    assert content["translations"][0]["name"] == "Updated PECS"


def test_delete_pecs(
    client: TestClient, superuser_token_headers: Dict[str, str], db: Session
) -> None:
    # Create a test PECS
    pecs = PECS(
        image_url="https://example.com/delete.jpg",
        is_custom=False
    )
    db.add(pecs)
    db.commit()
    db.refresh(pecs)
    
    response = client.delete(
        f"{settings.API_V1_STR}/pecs/{pecs.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    
    # Verify it's deleted
    response = client.get(
        f"{settings.API_V1_STR}/pecs/{pecs.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
