# -*- coding: utf-8 -*-
"""OCR 录入：图片识别 / 文本结构化抽取"""
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR
from ..database import get_db
from ..deps import get_current_user
from ..models import AiProvider, OcrTask, User
from ..schemas import LoginIn  # noqa: F401  (保持导入一致性，无实际用途)
from ..services import llm_service, ocr_service

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


def _vision_provider(db: Session):
    """拍照识别优先选已启用的视觉模型；没有则回退默认模型"""
    p = (
        db.query(AiProvider)
        .filter(AiProvider.is_enabled.is_(True), AiProvider.capabilities.contains("vision"))
        .first()
    )
    return p or llm_service.get_default_provider(db)


@router.post("/upload")
def ocr_upload(
    file: UploadFile = File(...),
    vehicle_id: int = Form(0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传单据图片：支持视觉的模型直接识别；否则返回 manual 模式（图片已留存）"""
    ext = Path(file.filename or "file.jpg").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "仅支持图片文件")
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / fname
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    image_bytes = dest.read_bytes()

    provider = _vision_provider(db)
    result = ocr_service.recognize_image(image_bytes, provider)
    task = OcrTask(
        user_id=user.id,
        vehicle_id=vehicle_id or None,
        image_path=f"/uploads/{fname}",
        raw_text=result.get("text", ""),
        status="完成" if result["mode"] == "text" else "待处理",
        provider=provider.name if provider else "",
    )
    db.add(task)
    db.commit()

    if result["mode"] == "text":
        parsed = ocr_service.extract_from_text(
            result["text"], llm_service.get_default_provider(db)
        )
        task.parsed_json = str(parsed)
        db.commit()
        return {
            "mode": "parsed",
            "image_path": task.image_path,
            "task_id": task.id,
            "text": result["text"],
            "draft": parsed.get("draft"),
            "message": "识别完成，请核对表单后保存",
        }
    return {
        "mode": result["mode"],
        "image_path": task.image_path,
        "task_id": task.id,
        "message": result.get("message", "已留存图片，可粘贴单据文字或手工录入"),
    }


@router.post("/parse-text")
def ocr_parse_text(
    text: str = Form(...),
    vehicle_id: int = Form(0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """粘贴单据文本 → 默认模型结构化抽取 → 表单草稿"""
    provider = llm_service.get_default_provider(db)
    result = ocr_service.extract_from_text(text, provider)
    task = OcrTask(
        user_id=user.id,
        vehicle_id=vehicle_id or None,
        raw_text=text,
        parsed_json=str(result),
        status="完成",
        provider=provider.name if provider else "无模型",
    )
    db.add(task)
    db.commit()
    return {
        "mode": result["mode"],
        "draft": result.get("draft"),
        "message": result.get("message", "解析完成，请核对后保存"),
    }
