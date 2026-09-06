# -*- coding: utf-8 -*-
"""大模型调用（OpenAI 兼容协议，支持多品牌配置）"""
import base64

import httpx
from sqlalchemy.orm import Session

from ..config import AI_TIMEOUT_SECONDS
from ..models import AiProvider


def get_default_provider(db: Session) -> AiProvider | None:
    """优先取已启用的默认模型，其次第一个已启用模型"""
    p = (
        db.query(AiProvider)
        .filter(AiProvider.is_enabled.is_(True), AiProvider.is_default.is_(True))
        .first()
    )
    if p:
        return p
    return db.query(AiProvider).filter(AiProvider.is_enabled.is_(True)).first()


def _headers(provider: AiProvider) -> dict:
    return {
        "Authorization": f"Bearer {provider.api_key}",
        "Content-Type": "application/json",
    }


def _endpoint(provider: AiProvider) -> str:
    return provider.base_url.rstrip("/") + "/chat/completions"


def call_chat(provider: AiProvider, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    """文本对话"""
    payload = {
        "model": provider.model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "stream": False,
    }
    with httpx.Client(timeout=AI_TIMEOUT_SECONDS) as client:
        resp = client.post(_endpoint(provider), headers=_headers(provider), json=payload)
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]


def call_vision(provider: AiProvider, system_prompt: str, user_prompt: str, image_bytes: bytes) -> str:
    """图片识别（provider 需支持 vision）"""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": provider.model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            },
        ],
        "temperature": 0.1,
        "stream": False,
    }
    with httpx.Client(timeout=AI_TIMEOUT_SECONDS) as client:
        resp = client.post(_endpoint(provider), headers=_headers(provider), json=payload)
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]
