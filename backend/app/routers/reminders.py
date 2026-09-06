# -*- coding: utf-8 -*-
"""提醒中心"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Reminder, User
from ..schemas import ReminderHandleIn, ReminderIn, ReminderOut

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderOut])
def list_reminders(
    status_filter: str = Query("", alias="status"),
    vehicle_id: int = Query(0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Reminder).filter(Reminder.user_id == user.id)
    if status_filter:
        q = q.filter(Reminder.status == status_filter)
    if vehicle_id:
        q = q.filter(Reminder.vehicle_id == vehicle_id)
    return q.order_by(Reminder.target_date, Reminder.id).all()


@router.post("", response_model=ReminderOut)
def create_reminder(body: ReminderIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = Reminder(user_id=user.id, **body.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.post("/{reminder_id}/handle", response_model=ReminderOut)
def handle_reminder(reminder_id: int, body: ReminderHandleIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(Reminder, reminder_id)
    if r is None or r.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "提醒不存在")
    r.status = body.status
    db.commit()
    db.refresh(r)
    return r


@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(Reminder, reminder_id)
    if r is None or r.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "提醒不存在")
    db.delete(r)
    db.commit()
    return {"ok": True}
