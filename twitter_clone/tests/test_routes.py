def test_error_when_adding_to_length_user_id(client):
    response = client.post(url="/api/users", json={"id": "324242", "name": "Testname222"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_true_response(client):
    response = client.get(url="/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]