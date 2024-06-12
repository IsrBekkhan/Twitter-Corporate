import pytest
from sqlalchemy import func, select

from models.user import User


@pytest.mark.usefixtures("client", "db_session")
class TestAddUserRoute:
    def test_error_when_adding_too_length_user_id(self, client):
        user_id = "A" * 33
        response = client.post(url="/api/users", json={"id": user_id, "name": "Testname1"})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "String should have at most 32 characters" in response.json()["error_message"]
        assert user_id in response.json()["error_message"]

    def test_error_when_adding_too_short_user_id(self, client):
        user_id = ""
        response = client.post(url="/api/users", json={"id": user_id, "name": "Testname2"})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "String should have at least 1 character" in response.json()["error_message"]
        assert user_id in response.json()["error_message"]

    def test_error_when_adding_too_length_user_name(self, client):
        user_name = "A" * 21
        response = client.post(url="/api/users", json={"id": "test_id_1", "name": user_name})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "String should have at most 20 characters" in response.json()["error_message"]
        assert user_name in response.json()["error_message"]

    def test_error_when_adding_too_short_user_name(self, client):
        user_name = "A"
        response = client.post(url="/api/users", json={"id": "", "name": user_name})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "String should have at least 2 characters" in response.json()["error_message"]
        assert user_name in response.json()["error_message"]

    def test_error_when_adding_user_with_integer_id(self, client):
        user_id = 1234
        response = client.post(url="/api/users", json={"id": "", "name": user_id})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Input should be a valid string" in response.json()["error_message"]
        assert str(user_id) in response.json()["error_message"]

    def test_error_when_adding_user_with_integer_name(self, client):
        user_name = 123
        response = client.post(url="/api/users", json={"id": "", "name": user_name})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Input should be a valid string" in response.json()["error_message"]
        assert str(user_name) in response.json()["error_message"]

    def test_error_when_adding_user_without_name(self, client):
        response = client.post(url="/api/users", json={"id": "test_id_3"})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    def test_error_when_adding_user_without_id(self, client):
        response = client.post(url="/api/users", json={"name": "Testname3"})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    async def test_successfully_adding_new_user(self, client, db_session):
        user_id = "test_id_4"
        user_name = "Testname4"

        async_session = db_session()
        async with async_session.begin():
            result = await async_session.execute(
                select(func.count(User.id))
            )
            prev_users_count = result.scalars().one()

        response = client.post(url="/api/users", json={"id": user_id, "name": user_name})
        assert response.status_code == 201
        assert response.json()["result"] is True
        assert response.json()["user"]["id"] == user_id
        assert response.json()["user"]["name"] == user_name
        async_session = db_session()
        async with async_session.begin():
            result = await async_session.execute(
                select(func.count(User.id))
            )
        assert prev_users_count + 1 == result.scalars().one()

    async def test_error_when_adding_exist_user_name(self, client, db_session):
        user_id_1 = "test_id_5"
        user_id_2 = "test_id_6"
        user_name = "Testname5"
        response_temp = client.post(url="/api/users", json={"id": user_id_1, "name": user_name})
        response = client.post(url="/api/users", json={"id": user_id_2, "name": user_name})
        assert response.status_code == 409
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert user_name in response.json()["error_message"]

    async def test_error_when_adding_exist_user_id(self, client, db_session):
        user_id_1 = "test_id_7"
        user_name_1 = "Testname6"
        user_name_2 = "Testname7"
        response_temp = client.post(url="/api/users", json={"id": user_id_1, "name": user_name_1})
        response = client.post(url="/api/users", json={"id": user_id_1, "name": user_name_2})
        assert response.status_code == 409
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert user_id_1 in response.json()["error_message"]


@pytest.mark.usefixtures("client")
class TestMyProfileInfoRoute:

    async def test_successfully_response_my_info(self, client):
        response = client.get(url="/api/users/me", headers={"api-key": "test"})
        assert response.status_code == 200
        user_id = response.json()["user"]["id"]
        assert response.json()["result"] is True
        assert user_id.split()[0] == "test"
        assert response.json()["user"]["name"] == "Testname"

    async def test_error_when_requested_not_exist_my_user_id(self, client):
        user_id = "test123"
        response = client.get(url="/api/users/me", headers={"api-key": user_id})
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert f"Пользователь с id {user_id} не существует" == response.json()["error_message"]

    async def test_error_when_requested_without_api_key(self, client):
        response = client.get(url="/api/users/me")
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    async def test_error_when_requested_too_length_my_user_id(self, client):
        user_id = "A" * 33
        response = client.get(url="/api/users/me", headers={"api-key": user_id})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "String should have at most 32 characters" in response.json()["error_message"]
        assert user_id in response.json()["error_message"]


@pytest.mark.usefixtures("client")
class TestUserProfileInfoRoute:

    async def test_successfully_response_user_info(self, client):
        user_id = "test"
        response = client.get(url=f"/api/users/{user_id}")
        assert response.status_code == 200
        user_id = response.json()["user"]["id"]
        assert response.json()["result"] is True
        assert user_id.split()[0] == "test"
        assert response.json()["user"]["name"] == "Testname"

    async def test_error_when_requested_not_exist_user_id(self, client):
        user_id = "test1234"
        response = client.get(url=f"/api/users/{user_id}")
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert f"Пользователь с id {user_id} не существует" == response.json()["error_message"]

    async def test_error_when_requested_too_length_user_id(self, client):
        user_id = "A" * 33
        response = client.get(url=f"/api/users/{user_id}")
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "String should have at most 32 characters" in response.json()["error_message"]
        assert user_id in response.json()["error_message"]







