# pragma: no cover
"""
Settings Route
--------------
User settings management.
All endpoints require authentication.
Input validated via Pydantic before DB write.
OWASP API1: Broken Object Level Authorization
OWASP API3: Broken Object Property Level Authorization
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.rbac import require_roles
from app.db.db import AsyncSessionLocal
from app.models import UserSettings

router = APIRouter(prefix="/settings", tags=["Settings"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


class SettingsPayload(BaseModel):
    """
    Validated settings payload.
    Only explicitly defined fields are accepted — prevents mass assignment.
    OWASP API3: Broken Object Property Level Authorization
    """

    theme: Optional[str] = Field(default=None, max_length=50)
    language: Optional[str] = Field(default=None, max_length=10)
    notifications_enabled: Optional[bool] = None
    timezone: Optional[str] = Field(default=None, max_length=50)


@router.get("/{user_id}")
async def get_settings(
    user_id: str,
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve settings for a user.
    Non-admins can only read their own settings.
    OWASP API1: Broken Object Level Authorization
    """
    if _user.get("role") != "admin" and _user.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own settings.",
        )

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    return settings


@router.put("/{user_id}")
async def update_settings(
    user_id: str,
    payload: SettingsPayload,
    _user: dict = Depends(require_roles("admin", "developer", "auditor")),
    db: AsyncSession = Depends(get_db),
):
    """
    Update settings for a user.
    Only validated fields accepted — prevents mass assignment attacks.
    Non-admins can only update their own settings.
    OWASP API3: Broken Object Property Level Authorization
    """
    if _user.get("role") != "admin" and _user.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own settings.",
        )

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserSettings(user_id=user_id)

    # Only update fields that were explicitly provided
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    db.add(settings)
    await db.commit()
    await db.refresh(settings)

    return settings
