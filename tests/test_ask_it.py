"""
Tests for the /ask-it endpoint.
Covers both normal queries and reload commands.
"""

def test_ask_it_basic(client):
    """Verify normal question flow returns a Slack message structure."""
    payload = {"user": "U123", "channel": "C1", "text": "reset okta mfa"}
    response = client.post("/ask-it", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "trace_id" in data
    assert "slack_message" in data
    msg = data["slack_message"]
    assert "blocks" in msg and isinstance(msg["blocks"], list)

def test_ask_it_reload(client):
    """Verify reload command correctly reloads the document cache."""
    payload = {"user": "U123", "channel": "C1", "text": "reload"}
    response = client.post("/ask-it", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["ok"] is True
    assert "reloaded_docs" in data