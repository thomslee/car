# -*- coding: utf-8 -*-
"""OCR 服务：图片识别（视觉模型）与文本结构化抽取（DeepSeek 等文本模型）
支持多类型单据：保养单(maintenance) / 保险单(insurance) / 加油单(refuel)
"""
import json

from ..models import AiProvider
from . import llm_service

# ========== 保养单 ==========
_EXTRACT_MAINTENANCE_SYSTEM = (
    "你是汽车保养单据信息抽取助手。从用户提供的保养单文本中抽取结构化信息，"
    "只输出 JSON，不要输出其他内容。"
)
_EXTRACT_MAINTENANCE_USER = (
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


def _empty_maintenance_draft() -> dict:
    return {
        "occurred_at": None, "mileage": None, "shop_name": "", "record_type": "保养",
        "category": "", "total_cost": None, "original_total_cost": None,
        "discount_amount": None, "discounts": [], "paid_amount": None,
        "confirmed_at": None, "skipped_note": "", "items": [],
    }


# ========== 保险单 ==========
_EXTRACT_INSURANCE_SYSTEM = (
    "你是汽车保险单信息抽取助手。从用户提供的保险单文本中抽取结构化信息，"
    "只输出 JSON，不要输出其他内容。"
)
_EXTRACT_INSURANCE_USER = (
    "请从以下保险单文本中抽取字段，输出 JSON：\n"
    '{{"company":"保险公司全称","policy_no":"保单号",'
    '"policy_type":"交强险或商业险(根据保单内容判断)",'
    '"premium":保费金额数字(找不到填null),"vehicle_tax":车船税金额数字(仅交强险有，找不到填0),'
    '"service_phone":"客服服务电话如95518(找不到填空字符串)",'
    '"start_date":"保险起期(YYYY-MM-DD，找不到填null)",'
    '"end_date":"保险到期日(YYYY-MM-DD，找不到填null)",'
    '"vehicle_model":"车辆厂牌型号如沃尔沃VCC6474E52U多用途乘用车(找不到填空字符串)",'
    '"plate_no":"车牌号如京JU1515(找不到填空字符串)",'
    '"items":"险种明细文本，把每个险种名称保额保费用分号隔开(如：车损险保额20万保费1500元;三者险保额300万保费520元)",'
    '"note":"备注信息如被保险人姓名销售渠道等(没有填空字符串)"}}\n'
    "注意：保单号通常以PDZA开头是交强险，PDAA开头是商业险。"
    "无法确定的字段填 null 或空字符串，不要编造。\n\n保险单文本：\n{text}"
)


def _empty_insurance_draft() -> dict:
    return {
        "company": "", "policy_no": "", "policy_type": "商业险",
        "premium": None, "vehicle_tax": 0, "service_phone": "",
        "start_date": None, "end_date": None,
        "vehicle_model": "", "plate_no": "",
        "items": "", "note": "",
    }


# ========== 加油单 ==========
_EXTRACT_REFUEL_SYSTEM = (
    "你是汽车加油记录信息抽取助手。从用户提供的加油记录文本中抽取结构化信息，"
    "只输出 JSON，不要输出其他内容。"
)
_EXTRACT_REFUEL_USER = (
    "请从以下加油记录文本中抽取字段，输出 JSON：\n"
    '{{"refueled_at":"加油时间(YYYY-MM-DD HH:MM，找不到填null)",'
    '"station_name":"加油站名称(找不到填空字符串)",'
    '"fuel_grade":"油标号，只能是92/95/98之一(找不到填95)",'
    '"liters":加油升数数字(找不到填null),'
    '"unit_price":单价元/升数字(找不到填null),'
    '"total_cost":应付金额数字(找不到填null),'
    '"paid_amount":实付金额/优惠后金额数字(找不到填null),'
    '"mileage":当前里程公里数(找不到填null)}}\n'
    "注意：实付金额是优惠后实际支付的金额，应付金额是原价。如果只提到一个金额，应付和实付都填这个金额。"
    "油标只能是92、95、98中的一个。"
    "无法确定的字段填 null，不要编造。\n\n加油记录文本：\n{text}"
)


def _empty_refuel_draft() -> dict:
    return {
        "refueled_at": None, "station_name": "", "fuel_grade": "95",
        "liters": None, "unit_price": None, "total_cost": None,
        "paid_amount": None, "mileage": None,
    }


# ========== 类型映射 ==========
_TYPE_CONFIG = {
    "maintenance": {
        "system": _EXTRACT_MAINTENANCE_SYSTEM,
        "user": _EXTRACT_MAINTENANCE_USER,
        "empty": _empty_maintenance_draft,
        "vision_instruction": "你是汽车保养单据 OCR 助手，请完整、准确地转写单据上的所有文字。",
        "vision_prompt": "请逐行转写这张汽车保养/维修单据上的文字，保持数字准确。",
    },
    "insurance": {
        "system": _EXTRACT_INSURANCE_SYSTEM,
        "user": _EXTRACT_INSURANCE_USER,
        "empty": _empty_insurance_draft,
        "vision_instruction": "你是汽车保险单 OCR 助手，请完整、准确地转写保单上的所有文字。",
        "vision_prompt": "请逐行转写这张汽车保险单上的所有文字，包括保险公司、保单号、保费、险种、日期、车辆信息等，保持数字准确。",
    },
    "refuel": {
        "system": _EXTRACT_REFUEL_SYSTEM,
        "user": _EXTRACT_REFUEL_USER,
        "empty": _empty_refuel_draft,
        "vision_instruction": "你是加油记录 OCR 助手，请完整、准确地转写加油小票上的所有文字。",
        "vision_prompt": "请逐行转写这张加油小票/记录上的文字，包括加油站、油号、升数、单价、金额、时间等，保持数字准确。",
    },
}


def extract_from_text(text: str, provider: AiProvider | None, doc_type: str = "maintenance") -> dict:
    """文本 → 结构化草稿；无模型时返回空草稿"""
    cfg = _TYPE_CONFIG.get(doc_type, _TYPE_CONFIG["maintenance"])
    if provider is None or not provider.api_key:
        return {"mode": "no_model", "draft": cfg["empty"]()}
    try:
        raw = llm_service.call_chat(
            provider, cfg["system"], cfg["user"].format(text=text), temperature=0.1
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return {"mode": "parsed", "draft": data}
    except Exception as e:
        return {"mode": "failed", "message": f"解析失败：{e}", "draft": cfg["empty"]()}


def recognize_image(image_bytes: bytes, provider: AiProvider | None, doc_type: str = "maintenance") -> dict:
    """图片 → 文本；provider 不支持视觉时返回 manual 模式"""
    cfg = _TYPE_CONFIG.get(doc_type, _TYPE_CONFIG["maintenance"])
    if provider is None or not provider.api_key:
        return {"mode": "no_model", "message": "未配置可用的模型"}
    if "vision" not in (provider.capabilities or ""):
        return {
            "mode": "no_vision",
            "message": "当前模型（" + provider.name + "）不支持图片识别，可粘贴单据文字或手工录入",
        }
    try:
        text = llm_service.call_vision(
            provider, cfg["vision_instruction"], cfg["vision_prompt"], image_bytes,
        )
        return {"mode": "text", "text": text}
    except Exception as e:
        return {"mode": "failed", "message": f"识别失败：{e}"}
