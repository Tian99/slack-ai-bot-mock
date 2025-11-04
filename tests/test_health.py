"""
Basic health and readiness endpoint test.
Ensures that the service is running and returns {ok: True}.
"""

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "ok" in body and body["ok"] is True