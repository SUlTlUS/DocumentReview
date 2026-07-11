import json
from typing import Protocol

from fastapi import Depends
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from app.config import Settings, get_settings
from app.errors import LLMError
from app.services.rag import RetrievalResult


ALLOWED_SEVERITIES = {"high", "medium", "low"}
V1_CATEGORIES = {"合规风险", "条款缺失", "表述模糊", "权益不对等"}


class ReviewItemPayload(BaseModel):
    category: str
    severity: str
    title: str
    description: str
    suggestion: str
    source_text: str


class ReviewResultPayload(BaseModel):
    summary: str
    items: list[ReviewItemPayload] = Field(default_factory=list)


class ReviewerProvider(Protocol):
    def review_document(self, text: str, chunks: list[str]) -> ReviewResultPayload: ...

    def chat(
        self,
        contexts: list[RetrievalResult],
        question: str,
        history: list[tuple[str, str]],
    ) -> str: ...


def extract_json(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start < 0 or end <= start:
            raise LLMError("模型没有返回合法 JSON", content[:500])
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMError("模型 JSON 解析失败", str(exc)) from exc


def validate_review_result(payload: dict) -> ReviewResultPayload:
    try:
        result = ReviewResultPayload.model_validate(payload)
    except ValidationError as exc:
        raise LLMError("审核结果字段不完整", str(exc)) from exc
    for item in result.items:
        if item.category not in V1_CATEGORIES:
            raise LLMError("审核结果包含未知分类", item.category)
        if item.severity not in ALLOWED_SEVERITIES:
            raise LLMError("审核结果包含未知风险等级", item.severity)
    return result


class MockReviewerProvider:
    def review_document(self, text: str, chunks: list[str]) -> ReviewResultPayload:
        items: list[ReviewItemPayload] = []
        if "仅约束乙方" in text or "单方" in text:
            source = "违约责任仅约束乙方" if "仅约束乙方" in text else "单方"
            items.append(
                ReviewItemPayload(
                    category="权益不对等",
                    severity="high",
                    title="双方责任约定不对等",
                    description="合同将主要违约责任集中于一方，可能造成显著权利义务失衡。",
                    suggestion="补充双方对等的违约责任、责任上限和救济方式。",
                    source_text=source,
                )
            )
        if "合理期限" in text or "适当" in text:
            source = "合理期限" if "合理期限" in text else "适当"
            items.append(
                ReviewItemPayload(
                    category="表述模糊",
                    severity="medium",
                    title="履行期限缺乏量化标准",
                    description="模糊时间或程度用语会增加履约争议。",
                    suggestion="改为明确的工作日数量、触发条件和确认方式。",
                    source_text=source,
                )
            )
        if "保密" not in text:
            items.append(
                ReviewItemPayload(
                    category="条款缺失",
                    severity="medium",
                    title="缺少保密条款",
                    description="合同未约定商业秘密的范围、使用限制和保密期限。",
                    suggestion="补充保密信息定义、例外、期限及违约责任。",
                    source_text="文档未包含保密条款",
                )
            )
        summary = f"Mock 审核完成，共识别 {len(items)} 项风险；请由法务人员复核后使用。"
        return ReviewResultPayload(summary=summary, items=items)

    def chat(
        self,
        contexts: list[RetrievalResult],
        question: str,
        history: list[tuple[str, str]],
    ) -> str:
        if not contexts:
            return "文档中未涉及此内容。"
        content = contexts[0].content
        keywords = [keyword for keyword in ("违约", "保密", "验收", "付款", "交付", "争议") if keyword in question]
        position = content.find(keywords[0]) if keywords else 0
        if position < 0:
            position = 0
        start = max(0, position - 36)
        quote = content[start : start + 180]
        return f"根据文档原文：“{quote}”\n\n针对“{question}”，建议结合上述条款进行判断。"


class DeepSeekReviewerProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.deepseek_api_key:
            raise LLMError("未配置 DeepSeek API Key")
        self.client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=60,
            max_retries=2,
        )
        self.model = settings.deepseek_model
        self.max_chars = settings.max_review_chars

    def review_document(self, text: str, chunks: list[str]) -> ReviewResultPayload:
        prompt = f"""你是一位资深法务合同审核专家。请从合规风险、条款缺失、表述模糊、权益不对等四个维度审核合同。
返回 JSON，格式为 {{"summary":"...","items":[{{"category":"...","severity":"high|medium|low","title":"...","description":"...","suggestion":"...","source_text":"..."}}]}}。
每个风险必须引用合同原文，不要输出 Markdown。合同内容：\n{text[: self.max_chars]}"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        return validate_review_result(extract_json(content))

    def chat(
        self,
        contexts: list[RetrievalResult],
        question: str,
        history: list[tuple[str, str]],
    ) -> str:
        context = "\n\n".join(item.content for item in contexts)
        history_text = "\n".join(f"{role}: {content}" for role, content in history)
        prompt = f"""仅根据文档片段回答并引用原文；如果没有依据，回答“文档中未涉及此内容”。
文档片段：\n{context}\n最近对话：\n{history_text}\n用户问题：{question}"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or "文档中未涉及此内容。"


def get_reviewer_provider(
    settings: Settings = Depends(get_settings),
) -> ReviewerProvider:
    if settings.llm_provider.lower() == "mock":
        return MockReviewerProvider()
    if settings.llm_provider.lower() == "deepseek":
        return DeepSeekReviewerProvider(settings)
    raise LLMError("未知 LLM Provider", settings.llm_provider)
