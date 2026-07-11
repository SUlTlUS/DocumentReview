import pytest

from app.errors import LLMError
from app.prompts.loader import load_prompt
from app.utils.json_parser import extract_json


def test_review_prompt_loads_five_dimensions_and_renders_json_shape():
    bundle = load_prompt("review")
    rendered = bundle.prompt.invoke(
        {
            "dimension_name": "数据合规",
            "dimension_description": "检查个人信息处理",
            "document_structure": "采购合同",
            "document_text": "合同正文",
        }
    ).to_string()

    assert bundle.version == "2.0"
    assert [item["key"] for item in bundle.dimensions] == [
        "compliance",
        "incompleteness",
        "ambiguity",
        "imbalance",
        "data_compliance",
    ]
    assert '"items": [' in rendered
    assert "数据合规" in rendered


def test_chat_prompt_exposes_only_expected_variables():
    bundle = load_prompt("chat")
    assert set(bundle.prompt.input_variables) == {"context", "history", "question"}


def test_extract_json_handles_plain_and_wrapped_payloads():
    assert extract_json('{"summary":"ok"}') == {"summary": "ok"}
    assert extract_json('说明文字\n```json\n{"summary":"ok"}\n```') == {"summary": "ok"}


def test_extract_json_rejects_invalid_or_non_object_payloads():
    with pytest.raises(LLMError):
        extract_json("not json")
    with pytest.raises(LLMError):
        extract_json("[]")
