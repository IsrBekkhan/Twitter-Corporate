def test_true_response(client):
    response = client.get(url="/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
