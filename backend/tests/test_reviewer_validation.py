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


def test_dimension_validation_normalizes_alias_fields_and_chinese_severity():
    result = validate_dimension_result(
        {
            "risks": [
                {
                    "risk_level": "高风险",
                    "risk_title": "单方解除权",
                    "analysis": "甲方可以无条件解除合同。",
                    "quote": "甲方有权随时解除本合同",
                    "recommendation": "增加对等解除权和通知期限。",
                }
            ]
        },
        "权益不对等",
    )
    assert result.items[0].category == "权益不对等"
    assert result.items[0].severity == "high"
    assert result.items[0].title == "单方解除权"
    assert result.items[0].description == "甲方可以无条件解除合同。"
    assert result.items[0].source_text == "甲方有权随时解除本合同"
    assert result.items[0].suggestion == "增加对等解除权和通知期限。"


def test_dimension_validation_marks_missing_evidence_for_manual_review():
    result = validate_dimension_result(
        {"issues": [{"title": "付款期限不明确", "level": "moderate"}]},
        "表述模糊",
    )
    assert result.items[0].severity == "medium"
    assert "需人工复核" in result.items[0].description
    assert "需人工复核" in result.items[0].source_text
    assert result.items[0].suggestion


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


def test_report_validation_accepts_missing_summary_and_alias_container():
    result = validate_review_result(
        {"findings": [{"name": "未约定保密义务", "risk_level": "low"}]},
        ALLOWED,
    )
    assert result.summary == "审核完成，共识别 1 项风险。"
    assert result.items[0].category == "合规风险"
    assert result.items[0].severity == "low"
