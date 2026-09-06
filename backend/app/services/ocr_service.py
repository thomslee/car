# -*- coding: utf-8 -*-
"""OCR 服务：图片识别（视觉模型）与文本结构化抽取（DeepSeek 等文本模型）"""
import json

from ..models import AiProvider
from . import llm_service

# 保养单字段抽取提示词
_EXTRACT_SYSTEM = (
    "你是汽车保养单据信息抽取助手。从用户提供的保养单文本中抽取结构化信息，"
    "只输出 JSON，不要输出其他内容。"
)
_EXTRACT_USER = (
    "请从以下保养单文本中抽取字段，输出 JSON：\n"
    '{{"occurred_at":"日期(YYYY-MM-DD，找不到填null)","mileage":里程数字(找不到填null),'
    '"shop_name":"门店名称","record_type":"保养或维修","category":"类别",'
    '"total_cost":总费用/实付金额数字(找不到填null),'
    '"original_total_cost":原价合计数字(找不到填null),'
    '"discount_amount":折扣金额数字(正数，找不到填null),'
    '"discounts":[{{"name":"折扣名称如基础保养券/忠诚守候券/续保抵扣","amount":折扣金额数字(正数)}}],'
    '"paid_amount":已支付金额数字(找不到填null),'
    '"confirmed_at":"客户确认时间(YYYY-MM-DD HH:MM，找不到填null)",'
    '"skipped_note":"本次未做项目文字说明(没有则填空字符串)",'
    '"items":[{{"item_type":"材料或工时","item_name":"项目名称",'
    '"quantity":数量(工时类填工时数如0.4/0.6/0.8),"unit_price":单价数字,'
    '"part_cost":材料费小计(工时类填0),"labor_cost":工时费小计(材料类填0),'
    '"is_original":是否原厂件(true/false，仅材料类)}}]}}\n'
    "项目名尽量规范（如：机油及机油滤清器、空调滤芯、火花塞、更换制动衬片）。"
    "材料和工时分条列出，不要合并。"
    "无法确定的字段填 null，不要编造。\n\n保养单文本：\n{text}"
)


def extract_from_text(text: str, provider: AiProvider | None) -> dict:
    """文本 → 结构化草稿；无模型时返回空草稿"""
    if provider is None or not provider.api_key:
        return {"mode": "no_model", "draft": _empty_draft()}
    try:
        raw = llm_service.call_chat(
            provider, _EXTRACT_SYSTEM, _EXTRACT_USER.format(text=text), temperature=0.1
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return {"mode": "parsed", "draft": data}
    except Exception as e:
        return {"mode": "failed", "message": f"解析失败：{e}", "draft": _empty_draft()}


def recognize_image(image_bytes: bytes, provider: AiProvider | None) -> dict:
    """图片 → 文本；provider 不支持视觉时返回 manual 模式"""
    if provider is None or not provider.api_key:
        return {"mode": "no_model", "message": "未配置可用的模型"}
    if "vision" not in (provider.capabilities or ""):
        return {
            "mode": "no_vision",
            "message": "当前模型（" + provider.name + "）不支持图片识别，可粘贴单据文字或手工录入",
        }
    try:
        text = llm_service.call_vision(
            provider,
            "你是汽车保养单据 OCR 助手，请完整、准确地转写单据上的所有文字。",
            "请逐行转写这张汽车保养/维修单据上的文字，保持数字准确。",
            image_bytes,
        )
        return {"mode": "text", "text": text}
    except Exception as e:
        return {"mode": "failed", "message": f"识别失败：{e}"}


def _empty_draft() -> dict:
    return {
        "occurred_at": None,
        "mileage": None,
        "shop_name": "",
        "record_type": "保养",
        "category": "",
        "total_cost": None,
        "original_total_cost": None,
        "discount_amount": None,
        "discounts": [],
        "paid_amount": None,
        "confirmed_at": None,
        "skipped_note": "",
        "items": [],
    }
