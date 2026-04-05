"""Reminder endpoints: manage user race notifications."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Reminder, User
from dependencies import get_current_user
from models.reminder_schemas import ReminderCreate, ReminderResponse, ReminderUpdate

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("/", response_model=list[ReminderResponse])
async def list_reminders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Reminder]:
    """List all reminders for the current user."""
    result = await db.execute(
        select(Reminder)
        .where(Reminder.user_id == user.id)
        .order_by(Reminder.race_year, Reminder.race_round)
    )
    return list(result.scalars().all())


@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    body: ReminderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Reminder:
    """Create a new race reminder."""
    reminder = Reminder(
        user_id=user.id,
        race_round=body.race_round,
        race_year=body.race_year,
        notify_before_hours=body.notify_before_hours,
        method=body.method,
    )
    db.add(reminder)
    await db.flush()
    return reminder


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: int,
    body: ReminderUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Reminder:
    """Update an existing reminder."""
    result = await db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user.id)
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    if body.notify_before_hours is not None:
        reminder.notify_before_hours = body.notify_before_hours
    if body.enabled is not None:
        reminder.enabled = body.enabled

    db.add(reminder)
    await db.flush()
    return reminder


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a reminder."""
    result = await db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user.id)
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    await db.execute(delete(Reminder).where(Reminder.id == reminder_id))
    await db.flush()
