import logging

from app.chains.review_chain import ReviewChain
from app.config import Settings
from app.engines.reviewer import ReviewEngine


CONTRACT = """采购服务合同
乙方应在十个工作日内交付，甲方在合理期限内验收。
违约责任仅约束乙方。
"""


def test_three_stage_chain_runs_five_independent_dimensions(caplog):
    engine = ReviewEngine(Settings(llm_provider="mock"))
    chain = ReviewChain(engine, max_concurrency=2)

    with caplog.at_level(logging.INFO):
        result = chain.invoke(CONTRACT)

    assert len(engine.dimensions) == 5
    assert [item.category for item in result.items] == ["权益不对等", "条款缺失", "表述模糊"]
    assert [item.severity for item in result.items] == ["high", "medium", "medium"]
    assert "三阶段审核" in result.summary
    assert "stage=structure" in caplog.text
    assert "stage=dimensions" in caplog.text
    assert "stage=report" in caplog.text


def test_data_compliance_dimension_activates_from_yaml_configuration():
    engine = ReviewEngine(Settings(llm_provider="mock"))
    result = ReviewChain(engine).invoke("供应商收集身份证等个人信息，但合同未约定保存期限。")

    assert any(item.category == "数据合规" for item in result.items)
