from app.main import app


def test_day3_preserves_day2_nine_endpoint_contract():
    schema = app.openapi()
    actual = {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method.lower() in {"get", "post", "delete", "put", "patch"}
    }
    assert actual == {
        ("GET", "/api/health"),
        ("GET", "/api/documents"),
        ("POST", "/api/documents/upload"),
        ("GET", "/api/documents/{document_id}"),
        ("DELETE", "/api/documents/{document_id}"),
        ("POST", "/api/documents/{document_id}/review"),
        ("GET", "/api/documents/{document_id}/review"),
        ("POST", "/api/documents/{document_id}/chat"),
        ("GET", "/api/documents/{document_id}/chat/history"),
    }
