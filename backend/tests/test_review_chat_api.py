def upload_contract(api_client, name="contract.txt", text=None):
    body = text or "违约责任仅约束乙方。验收标准应在合理期限内完成。"
    response = api_client.post(
        "/api/documents/upload",
        files={"file": (name, body, "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["document"]["id"]


def test_review_and_repeat_review_preserve_contract(api_client):
    document_id = upload_contract(api_client)

    first = api_client.post(f"/api/documents/{document_id}/review")
    assert first.status_code == 200
    payload = first.json()
    assert payload["status"] == "completed"
    assert payload["pipeline_version"] == "v1.0"
    assert payload["risk_count"] == 1
    assert {item["category"] for item in payload["items"]} == {
        "权益不对等",
        "表述模糊",
        "条款缺失",
    }

    second = api_client.post(f"/api/documents/{document_id}/review")
    assert second.status_code == 200
    assert second.json()["id"] != payload["id"]
    latest = api_client.get(f"/api/documents/{document_id}/review")
    assert latest.json()["id"] == second.json()["id"]


def test_chat_reuses_session_and_returns_quoted_context(api_client):
    document_id = upload_contract(api_client)
    session_id = None
    for index in range(5):
        response = api_client.post(
            f"/api/documents/{document_id}/chat",
            json={"question": f"第 {index + 1} 个问题：违约责任是什么？", "session_id": session_id},
        )
        assert response.status_code == 200
        payload = response.json()
        session_id = payload["session_id"]
        assert "根据文档原文" in payload["answer"]

    history = api_client.get(
        f"/api/documents/{document_id}/chat/history",
        params={"session_id": session_id},
    )
    assert history.status_code == 200
    messages = history.json()["messages"]
    assert len(messages) == 10
    assert [message["role"] for message in messages[:2]] == ["user", "assistant"]


def test_review_rejects_parse_failed_document(api_client):
    response = api_client.post(
        "/api/documents/upload",
        files={"file": ("broken.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 201
    document = response.json()["document"]
    assert document["status"] == "parse_failed"

    review = api_client.post(f"/api/documents/{document['id']}/review")
    assert review.status_code == 409

