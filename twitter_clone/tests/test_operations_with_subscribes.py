import pytest

from models.user import User


@pytest.mark.usefixtures("client", "db_session")
class TestFollowUserRoute:

    def test_error_when_requested_without_api_key(self, client):
        response = client.post("/api/users/test/follow")
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    def test_error_when_requested_with_too_length_api_key(self, client):
        user_id = "test"
        api_key = "A" * 33
        response = client.post(f"/api/users/{user_id}/follow", headers={"api-key": api_key})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "String should have at most 32 characters" in response.json()["error_message"]
        assert api_key in response.json()["error_message"]

    def test_error_when_requested_with_too_length_user_id(self, client):
        user_id = "A" * 33
        api_key = "test"
        response = client.post(f"/api/users/{user_id}/follow", headers={"api-key": api_key})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "String should have at most 32 characters" in response.json()["error_message"]
        assert user_id in response.json()["error_message"]

    def test_error_when_requested_with_not_exist_api_key(self, client):
        user_id = "test"
        api_key = "test_1"
        response = client.post(f"/api/users/{user_id}/follow", headers={"api-key": api_key})
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert f"Пользователя с id {api_key} не существует" == response.json()["error_message"]

    def test_error_when_requested_with_not_exist_user_id(self, client):
        user_id = "test_1"
        api_key = "test"
        response = client.post(f"/api/users/{user_id}/follow", headers={"api-key": api_key})
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert f"Пользователя с id {user_id} не существует" == response.json()["error_message"]

    def test_error_when_requested_with_same_user_id_as_api_key(self, client):
        user_id = "test"
        api_key = "test"
        response = client.post(f"/api/users/{user_id}/follow", headers={"api-key": api_key})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert "Пользователь не может подписаться сам на себя" == response.json()["error_message"]

    async def test_successfully_subscribe_add(self, client, db_session):
        api_key = "test"
        async_session = db_session()
        user = await User.add_user(async_session, user_id="test_id_10", name="Testname_10")
        user_id = user.id
        prev_subscribes_count = await User.get_subscribes_count(async_session)

        response = client.post(f"/api/users/{user_id}/follow", headers={"api-key": api_key})
        assert response.status_code == 201
        assert response.json()["result"] is True
        assert await User.get_subscribes_count(async_session) == prev_subscribes_count + 1

    async def test_error_when_adding_exist_record(self, client, db_session):
        api_key = "test"
        async_session = db_session()
        user = await User.add_user(async_session, user_id="test_id_11", name="Testname_11")
        user_id = user.id

        response_temp = client.post(url=f"/api/users/{user_id}/follow", headers={"api-key": api_key})
        response = client.post(url=f"/api/users/{user_id}/follow", headers={"api-key": api_key})

        assert response.status_code == 409
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (f"Запись о подписке пользователя с id {api_key} на пользователя с {user_id} уже существует в БД" ==
                response.json()["error_message"])


@pytest.mark.usefixtures("client", "db_session")
class TestUnfollowUserRoute:

    def test_error_when_requested_without_api_key(self, client):
        response = client.delete("/api/users/test/follow")
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    def test_error_when_requested_with_too_length_api_key(self, client):
        user_id = "test"
        api_key = "A" * 33
        response = client.post(f"/api/users/{user_id}/follow", headers={"api-key": api_key})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "String should have at most 32 characters" in response.json()["error_message"]
        assert api_key in response.json()["error_message"]

    def test_error_when_requested_with_too_length_user_id(self, client):
        user_id = "A" * 33
        api_key = "test"
        response = client.delete(f"/api/users/{user_id}/follow", headers={"api-key": api_key})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "String should have at most 32 characters" in response.json()["error_message"]
        assert user_id in response.json()["error_message"]

    async def test_successfully_subscribe_delete(self, client, db_session):
        async_session = db_session()
        new_user_id = "test_id_12"
        api_key = "test"

        new_user = await User.add_user(async_session, user_id=new_user_id, name="Testname_12")
        res = await User.follow(async_session, follower_user_id="test", following_user_id=new_user_id)
        prev_subscribes_count = await User.get_subscribes_count(async_session)

        response = client.delete(f"/api/users/{new_user.id}/follow", headers={"api-key": api_key})
        assert response.status_code == 200
        assert response.json()["result"] is True
        assert await User.get_subscribes_count(async_session) == prev_subscribes_count - 1

    async def test_error_when_deleting_not_exist_record(self, client, db_session):
        async_session = db_session()
        new_user_id = "test_id_13"
        api_key = "test"

        new_user = await User.add_user(async_session, user_id=new_user_id, name="Testname_13")
        res = await User.follow(async_session, follower_user_id="test", following_user_id=new_user_id)

        response_temp = client.delete(f"/api/users/{new_user.id}/follow", headers={"api-key": api_key})
        prev_subscribes_count = await User.get_subscribes_count(async_session)
        response = client.delete(f"/api/users/{new_user.id}/follow", headers={"api-key": api_key})

        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert await User.get_subscribes_count(async_session) == prev_subscribes_count
        assert (f"Запись об отписке пользователя с id {api_key} от пользователя с {new_user.id} не существует в БД" ==
                response.json()["error_message"])
