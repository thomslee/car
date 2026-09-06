# -*- coding: utf-8 -*-
"""附件图片上传/列表/删除"""
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR
from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import Attachment, User

router = APIRouter(prefix="/api/attachments", tags=["attachments"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".pdf"}


@router.post("/upload")
def upload_attachment(
    file: UploadFile = File(...),
    vehicle_id: int = Form(...),
    biz_type: str = Form("照片"),
    biz_id: int = Form(0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_vehicle_or_404(db, vehicle_id, user)
    ext = Path(file.filename or "file.jpg").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "仅支持图片或 PDF 文件")
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / fname
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    a = Attachment(
        vehicle_id=vehicle_id,
        biz_type=biz_type,
        biz_id=biz_id,
        file_path=f"/uploads/{fname}",
        original_name=file.filename or fname,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"ok": True, "id": a.id, "url": a.file_path, "original_name": a.original_name}


@router.get("")
def list_attachments(
    vehicle_id: int = Query(...),
    biz_type: str = Query(""),
    biz_id: int = Query(0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_vehicle_or_404(db, vehicle_id, user)
    q = db.query(Attachment).filter(Attachment.vehicle_id == vehicle_id)
    if biz_type:
        q = q.filter(Attachment.biz_type == biz_type)
    if biz_id:
        q = q.filter(Attachment.biz_id == biz_id)
    rows = q.order_by(Attachment.id.desc()).all()
    return [
        {
            "id": a.id,
            "biz_type": a.biz_type,
            "biz_id": a.biz_id,
            "url": a.file_path,
            "original_name": a.original_name,
            "created_at": str(a.created_at)[:10] if a.created_at else None,
        }
        for a in rows
    ]


@router.delete("/{attachment_id}")
def delete_attachment(attachment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(Attachment, attachment_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "附件不存在")
    get_vehicle_or_404(db, a.vehicle_id, user)
    try:
        (UPLOAD_DIR / Path(a.file_path).name).unlink(missing_ok=True)
    except Exception:
        pass
    db.delete(a)
    db.commit()
    return {"ok": True}
