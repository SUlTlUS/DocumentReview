from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from langchain_core.prompts import ChatPromptTemplate

from app.errors import AppError


PROMPT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class PromptBundle:
    version: str
    prompt: ChatPromptTemplate
    dimensions: tuple[dict[str, str], ...] = ()


def load_prompt(name: str) -> PromptBundle:
    path = (PROMPT_DIR / f"{name}.yaml").resolve()
    if path.parent != PROMPT_DIR or not path.is_file():
        raise AppError("Prompt 模板不存在", name)
    try:
        payload: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
        system = str(payload["system"])
        human = str(payload["human"])
        dimensions = tuple(payload.get("dimensions", ()))
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        raise AppError("Prompt 模板格式错误", name) from exc
    return PromptBundle(
        version=str(payload.get("version", "unknown")),
        prompt=ChatPromptTemplate.from_messages([("system", system), ("human", human)]),
        dimensions=dimensions,
    )
