"""
Tests for the /admin/reload endpoint.
Ensures that document cache can be reloaded manually.
"""

def test_admin_reload(client):
    """Validates admin-triggered cache reload."""
    response = client.post("/admin/reload")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "reloaded_docs" in data