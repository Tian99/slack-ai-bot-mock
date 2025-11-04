"""
Tests for the /feedback endpoint.
Ensures that helpful/unhelpful feedback is recorded properly.
"""

def test_feedback_positive(client):
    """Sends positive feedback and checks success response."""
    payload = {"trace_id": "abc123", "helpful": True}
    response = client.post("/feedback", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["trace_id"] == "abc123"

def test_feedback_negative(client):
    """Sends negative feedback and checks success response."""
    payload = {"trace_id": "def456", "helpful": False}
    response = client.post("/feedback", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True