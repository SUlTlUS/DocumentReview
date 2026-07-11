from app.engines.reviewer import validate_dimension_result, validate_review_result


ALLOWED = ["合规风险", "条款缺失", "表述模糊", "权益不对等", "数据合规"]


def item(category: str, title: str, description: str = "风险描述") -> dict[str, str]:
    return {
        "category": category,
        "severity": "medium",
        "title": title,
        "description": description,
        "source_text": "合同原文",
        "suggestion": "修改建议",
    }


def test_dimension_validation_uses_trusted_dimension_name():
    result = validate_dimension_result(
        {"items": [item("合同公平性风险", "甲方享有单方解除权")]},
        "权益不对等",
    )
    assert result.items[0].category == "权益不对等"


def test_report_validation_normalizes_model_category_aliases():
    result = validate_review_result(
        {
            "summary": "审核完成",
            "items": [
                item("知识产权风险", "知识产权归属条款缺失"),
                item("隐私保护问题", "个人信息处理目的不明确"),
                item("资质许可问题", "乙方缺少必要经营资质", "可能违反行业法规"),
            ],
        },
        ALLOWED,
    )
    assert [entry.category for entry in result.items] == ["条款缺失", "数据合规", "条款缺失"]


def test_report_validation_keeps_unknown_finding_with_safe_fallback():
    result = validate_review_result(
        {"summary": "审核完成", "items": [item("其他业务风险", "价格调整机制异常")]},
        ALLOWED,
    )
    assert result.items[0].category == "合规风险"
