from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any

from app.errors import LLMError


logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        matches = re.findall(r"\{[\s\S]*\}", text)
        if not matches:
            _log_failure(text)
            raise LLMError("模型没有返回合法 JSON")
        try:
            value = json.loads(matches[-1])
        except json.JSONDecodeError as exc:
            _log_failure(text)
            raise LLMError("模型 JSON 解析失败", f"line={exc.lineno} column={exc.colno}") from exc
    if not isinstance(value, dict):
        raise LLMError("模型 JSON 顶层必须是对象")
    return value


def _log_failure(text: str) -> None:
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12]
    logger.warning("llm_json_parse_failed response_chars=%d response_sha256=%s", len(text), digest)
