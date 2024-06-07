def test_error_when_adding_to_length_user_id(client):
    response = client.post(url="/api/users", json={"id": "3242k3l42", "name": "Testname2323"})
    a = response.json()
    assert response.status_code == 201


def test_true_response(client):
    response = client.get(url="/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]