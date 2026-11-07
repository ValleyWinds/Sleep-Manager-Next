"""构造与解析主程序 Planner Hook 使用的 Context Item"""

from datetime import datetime
from typing import Any, Dict, List

import uuid

SYSTEM_MESSAGE_ITEM_TYPE = "SystemMessageItem"
FUNCTION_CALL_ITEM_TYPE = "FunctionCallItem"
FUNCTION_CALL_OUTPUT_ITEM_TYPE = "FunctionCallOutputItem"


def build_system_message_item(text: str) -> Dict[str, Any]:
    """构造一条可被主程序反序列化的系统消息 Item

    主程序会用 `deserialize_context_item_snapshot` 严格校验结构：`meta` 必须含
    `item_id` / `logical_turn_id` / `timestamp`，`parts` 必须是内容片段列表。
    任一字段缺失或类型不符都会导致整份 items 被丢弃，因此这里只构造最小合法结构。
    """

    return {
        "item_type": SYSTEM_MESSAGE_ITEM_TYPE,
        "meta": {
            "item_id": uuid.uuid4().hex,
            "logical_turn_id": None,
            "timestamp": datetime.now().isoformat(),
        },
        "parts": [{"type": "text", "text": text}],
    }


def extract_item_tool_names(raw_items: Any) -> List[str]:
    """从序列化的 Context Item 列表中提取工具名"""

    if not isinstance(raw_items, list):
        return []

    tool_names: List[str] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue

        item_type = str(raw_item.get("item_type") or "").strip()
        if item_type == FUNCTION_CALL_ITEM_TYPE:
            raw_tool_call = raw_item.get("tool_call")
            candidate = raw_tool_call.get("func_name") if isinstance(raw_tool_call, dict) else None
        elif item_type == FUNCTION_CALL_OUTPUT_ITEM_TYPE:
            candidate = raw_item.get("tool_name")
        else:
            candidate = None

        if isinstance(candidate, str) and candidate.strip():
            tool_names.append(candidate.strip())
    return tool_names
