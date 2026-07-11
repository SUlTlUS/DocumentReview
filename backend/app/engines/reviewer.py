from __future__ import annotations

import json
import hashlib
import logging
from typing import Any, Literal

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnableLambda
from pydantic import BaseModel, Field, ValidationError

from app.config import Settings
from app.errors import LLMError
from app.prompts.loader import PromptBundle, load_prompt
from app.utils.json_parser import extract_json


logger = logging.getLogger(__name__)


class ReviewItemPayload(BaseModel):
    category: str
    severity: Literal["high", "medium", "low"]
    title: str
    description: str
    suggestion: str
    source_text: str


class ReviewResultPayload(BaseModel):
    summary: str
    items: list[ReviewItemPayload] = Field(default_factory=list)


class DimensionResultPayload(BaseModel):
    items: list[ReviewItemPayload] = Field(default_factory=list)


def validate_dimension_result(payload: dict[str, Any], category: str) -> DimensionResultPayload:
    try:
        result = DimensionResultPayload.model_validate(payload)
    except ValidationError as exc:
        raise LLMError("维度审核结果字段不完整", str(exc)) from exc
    return DimensionResultPayload(
        items=[item.model_copy(update={"category": category}) for item in result.items]
    )


def _canonical_category(item: ReviewItemPayload, categories: list[str]) -> str:
    if item.category in categories:
        return item.category
    evidence = f"{item.category} {item.title} {item.description}".lower()
    rules = (
        ("数据合规", ("数据", "个人信息", "隐私", "跨境")),
        ("条款缺失", ("缺失", "缺少", "遗漏", "不完整", "未约定", "未明确约定")),
        ("表述模糊", ("模糊", "歧义", "不明确", "不清晰", "未量化", "表述")),
        ("权益不对等", ("不对等", "失衡", "单方", "不公平", "过度免责")),
        ("合规风险", ("合规", "违法", "法律", "法规", "资质", "许可", "税务")),
    )
    for target, keywords in rules:
        if target in categories and any(keyword in evidence for keyword in keywords):
            return target
    return "合规风险" if "合规风险" in categories else categories[0]


def validate_review_result(
    payload: dict[str, Any],
    categories: set[str] | list[str] | tuple[str, ...] | None = None,
) -> ReviewResultPayload:
    try:
        result = ReviewResultPayload.model_validate(payload)
    except ValidationError as exc:
        raise LLMError("审核结果字段不完整", str(exc)) from exc
    if not categories:
        return result
    allowed = list(categories)
    normalized: list[ReviewItemPayload] = []
    for item in result.items:
        category = _canonical_category(item, allowed)
        if category != item.category:
            digest = hashlib.sha256(item.category.encode("utf-8")).hexdigest()[:10]
            logger.warning("review_category_normalized source_sha256=%s target=%s", digest, category)
        normalized.append(item.model_copy(update={"category": category}))
    return ReviewResultPayload(summary=result.summary, items=normalized)


class ReviewEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.review_bundle = load_prompt("review")
        self.structure_bundle = load_prompt("structure")
        self.report_bundle = load_prompt("report")
        self.dimensions = self.review_bundle.dimensions
        self.prompt_version = self.review_bundle.version
        self.is_mock = settings.llm_provider.lower() == "mock"
        self._model = None if self.is_mock else self._create_model()

    def _create_model(self):
        if self.settings.llm_provider.lower() != "deepseek":
            raise LLMError("未知 LLM Provider", self.settings.llm_provider)
        if not self.settings.deepseek_api_key:
            raise LLMError("未配置 DeepSeek API Key")
        from langchain_deepseek import ChatDeepSeek

        return ChatDeepSeek(
            model=self.settings.deepseek_model,
            api_key=self.settings.deepseek_api_key,
            base_url=self.settings.deepseek_base_url,
            temperature=0,
            timeout=60,
            max_retries=2,
        )

    def structure_runnable(self) -> Runnable:
        if self.is_mock:
            return RunnableLambda(self._mock_structure).with_config(run_name="mock_structure_analysis")
        return (
            self.structure_bundle.prompt
            | self._model
            | StrOutputParser()
        ).with_config(run_name="structure_analysis")

    def dimension_runnable(self, dimension: dict[str, str]) -> Runnable:
        name = dimension["name"]
        if self.is_mock:
            return RunnableLambda(
                lambda inputs, current=dimension: self._mock_dimension(inputs, current)
            ).with_config(run_name=f"mock_dimension_{dimension['key']}")
        prompt = self.review_bundle.prompt.partial(
            dimension_name=name,
            dimension_description=dimension["description"],
        )
        return (
            prompt
            | self._model
            | StrOutputParser()
            | RunnableLambda(extract_json)
            | RunnableLambda(lambda payload: validate_dimension_result(payload, name))
        ).with_config(run_name=f"dimension_{dimension['key']}")

    def report_runnable(self) -> Runnable:
        if self.is_mock:
            return RunnableLambda(self._mock_report).with_config(run_name="mock_report_aggregation")
        categories = [item["name"] for item in self.dimensions]
        return (
            self.report_bundle.prompt
            | self._model
            | StrOutputParser()
            | RunnableLambda(extract_json)
            | RunnableLambda(lambda payload: validate_review_result(payload, categories))
        ).with_config(run_name="report_aggregation")

    @staticmethod
    def _mock_structure(inputs: dict[str, Any]) -> str:
        text = str(inputs["document_text"])
        headings = [line.strip() for line in text.splitlines() if line.strip()[:2] in {"一、", "二、", "三、", "四、", "五、"}]
        return f"合同正文约 {len(text)} 字；识别到 {len(headings)} 个主要章节：{'、'.join(headings[:5]) or '未识别章节标题'}。"

    @staticmethod
    def _item(
        category: str,
        severity: Literal["high", "medium", "low"],
        title: str,
        description: str,
        suggestion: str,
        source_text: str,
    ) -> ReviewItemPayload:
        return ReviewItemPayload(
            category=category,
            severity=severity,
            title=title,
            description=description,
            suggestion=suggestion,
            source_text=source_text,
        )

    def _mock_dimension(
        self,
        inputs: dict[str, Any],
        dimension: dict[str, str],
    ) -> DimensionResultPayload:
        text = str(inputs["document_text"])
        category = dimension["name"]
        items: list[ReviewItemPayload] = []
        if dimension["key"] == "incompleteness" and "保密" not in text:
            items.append(self._item(category, "medium", "缺少保密条款", "未约定商业秘密的范围、使用限制和期限。", "补充保密信息定义、例外、期限和违约责任。", "文档未包含保密条款"))
        if dimension["key"] == "ambiguity" and ("合理期限" in text or "适当" in text):
            source = "合理期限" if "合理期限" in text else "适当"
            items.append(self._item(category, "medium", "履行期限缺乏量化标准", "模糊时间或程度用语会增加履约争议。", "改为明确工作日数量、触发条件和确认方式。", source))
        if dimension["key"] == "imbalance" and ("仅约束乙方" in text or "单方" in text):
            source = "违约责任仅约束乙方" if "仅约束乙方" in text else "单方"
            items.append(self._item(category, "high", "双方责任约定不对等", "主要违约责任集中于一方，权利义务明显失衡。", "补充双方对等责任、责任上限和救济方式。", source))
        if dimension["key"] == "data_compliance" and any(word in text for word in ("个人信息", "用户数据", "身份证")) and "处理目的" not in text:
            items.append(self._item(category, "high", "个人信息处理规则不完整", "合同涉及个人信息但未明确处理目的和范围。", "补充处理目的、最小必要范围、保存期限和主体权利。", "文档涉及个人信息但未说明处理目的"))
        return DimensionResultPayload(items=items)

    @staticmethod
    def _mock_report(inputs: dict[str, Any]) -> ReviewResultPayload:
        raw_results = inputs["dimension_results"]
        candidates: list[ReviewItemPayload] = []
        for value in raw_results.values():
            result = value if isinstance(value, DimensionResultPayload) else DimensionResultPayload.model_validate(value)
            candidates.extend(result.items)
        severity_rank = {"high": 0, "medium": 1, "low": 2}
        unique: dict[tuple[str, str], ReviewItemPayload] = {}
        for item in candidates:
            key = (item.source_text, item.title)
            previous = unique.get(key)
            if previous is None or severity_rank[item.severity] < severity_rank[previous.severity]:
                unique[key] = item
        items = sorted(unique.values(), key=lambda item: severity_rank[item.severity])
        return ReviewResultPayload(
            summary=f"v2.0 Mock 三阶段审核完成，共识别 {len(items)} 项风险；请由法务人员复核。",
            items=items,
        )


class ChatEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.bundle: PromptBundle = load_prompt("chat")
        self.prompt_version = self.bundle.version
        self.is_mock = settings.llm_provider.lower() == "mock"
        if self.is_mock:
            self.chain = RunnableLambda(self._mock_chat).with_config(run_name="mock_document_chat")
        else:
            review_engine = ReviewEngine(settings)
            self.chain = (
                self.bundle.prompt | review_engine._model | StrOutputParser()
            ).with_config(run_name="document_chat")

    @staticmethod
    def _mock_chat(inputs: dict[str, Any]) -> str:
        context = str(inputs.get("context", "")).strip()
        question = str(inputs.get("question", "")).strip()
        if not context:
            return "文档中未涉及此内容。"
        keywords = [word for word in ("违约", "保密", "验收", "付款", "交付", "争议") if word in question]
        position = context.find(keywords[0]) if keywords else 0
        position = max(0, position)
        quote = context[max(0, position - 36): position + 144]
        return f"根据文档原文：“{quote}”\n\n针对“{question}”，建议结合上述条款进行判断。"

    def invoke(self, context: str, history: str, question: str) -> str:
        return str(self.chain.invoke({"context": context, "history": history, "question": question}))
