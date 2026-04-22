from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.db import AsyncSessionLocal
from app.models import UserSettings

router = APIRouter(prefix="/settings", tags=["Settings"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/{user_id}")
async def get_settings(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    return settings


@router.put("/{user_id}")
async def update_settings(
    user_id: str, payload: dict, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserSettings(user_id=user_id)

    for key, value in payload.items():
        setattr(settings, key, value)

    db.add(settings)
    await db.commit()
    await db.refresh(settings)

    return settings
