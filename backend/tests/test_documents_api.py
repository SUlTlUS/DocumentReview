def test_health_reports_mock_provider(api_client):
    response = api_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "llm_provider": "mock", "version": "1.0.0"}


def test_upload_list_detail_and_delete_txt(api_client):
    response = api_client.post(
        "/api/documents/upload",
        files={"file": ("采购合同.txt", "违约责任仅约束乙方。验收标准为合理期限。", "text/plain")},
    )
    assert response.status_code == 201
    uploaded = response.json()
    document_id = uploaded["document"]["id"]
    assert uploaded["document"]["status"] == "ready"
    assert uploaded["chunk_count"] >= 1

    listed = api_client.get("/api/documents").json()
    assert listed["total"] == 1
    assert listed["items"][0]["filename"] == "采购合同.txt"

    detail = api_client.get(f"/api/documents/{document_id}")
    assert detail.status_code == 200
    assert detail.json()["content_summary"].startswith("违约责任")

    deleted = api_client.delete(f"/api/documents/{document_id}")
    assert deleted.status_code == 204
    assert api_client.get(f"/api/documents/{document_id}").status_code == 404


def test_upload_rejects_unsupported_and_empty_files(api_client):
    unsupported = api_client.post(
        "/api/documents/upload",
        files={"file": ("sheet.xlsx", b"data", "application/octet-stream")},
    )
    assert unsupported.status_code == 422

    empty = api_client.post(
        "/api/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert empty.status_code == 422

