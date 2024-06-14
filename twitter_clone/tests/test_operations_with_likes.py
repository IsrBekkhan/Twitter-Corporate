import pytest

from models.like import Like
from models.tweet import Tweet


@pytest.mark.usefixtures("client", "db_session")
class TestAddLikeRoute:

    def test_error_when_requested_without_api_key(self, client):
        tweet_id = 1
        response = client.post(f"/api/tweets/{tweet_id}/likes")
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    def test_error_when_requested_with_too_length_api_key(self, client):
        tweet_id = 1
        api_key = "A" * 33
        response = client.post(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert (
            "String should have at most 32 characters"
            in response.json()["error_message"]
        )
        assert api_key in response.json()["error_message"]

    def test_error_when_requested_with_not_integer_tweet_id(self, client):
        tweet_id = "ABC"
        api_key = "test"
        response = client.post(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Input should be a valid integer" in response.json()["error_message"]
        assert tweet_id in response.json()["error_message"]

    def test_error_when_requested_with_not_exist_api_key(self, client):
        tweet_id = 1
        api_key = "test_id_17"
        response = client.post(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            f"Пользователя с id {api_key} не существует"
            == response.json()["error_message"]
        )

    def test_error_when_requested_with_not_exist_tweet_id(self, client):
        tweet_id = 100
        api_key = "test"
        response = client.post(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            f"Твита с id {tweet_id} не существует" == response.json()["error_message"]
        )

    async def test_successfully_response_when_requested_with_normal_values(
        self, client, db_session
    ):
        async_session = db_session()
        api_key = "test"
        tweet_id = await Tweet.add_tweet(
            async_session, author_id=api_key, content="It's just text for text..."
        )
        likes_count_before = await Like.get_likes_count(async_session)

        response = client.post(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 201
        assert response.json()["result"] is True
        assert likes_count_before == await Like.get_likes_count(async_session) - 1

        await Tweet.delete_tweet(async_session, author_id=api_key, tweet_id=tweet_id)

    async def test_error_when_posted_exist_like(self, client, db_session):
        async_session = db_session()
        api_key = "test"
        tweet_id = await Tweet.add_tweet(
            async_session, author_id=api_key, content="It's just text for text..."
        )

        client.post(f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key})
        likes_count_before = await Like.get_likes_count(async_session)
        response = client.post(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 409
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            f"Запись о добавлении лайка твиту с id {tweet_id} пользователем с id {api_key} уже существует"
            == response.json()["error_message"]
        )
        assert likes_count_before == await Like.get_likes_count(async_session)

        await Tweet.delete_tweet(async_session, author_id=api_key, tweet_id=tweet_id)


@pytest.mark.usefixtures("client", "db_session")
class TestDeleteLikeRoute:

    def test_error_when_requested_without_api_key(self, client):
        tweet_id = 1
        response = client.delete(f"/api/tweets/{tweet_id}/likes")
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    def test_error_when_requested_with_too_length_api_key(self, client):
        tweet_id = 1
        api_key = "A" * 33
        response = client.delete(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert (
            "String should have at most 32 characters"
            in response.json()["error_message"]
        )
        assert api_key in response.json()["error_message"]

    def test_error_when_requested_with_not_integer_tweet_id(self, client):
        tweet_id = "ABC"
        api_key = "test"
        response = client.delete(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Input should be a valid integer" in response.json()["error_message"]
        assert tweet_id in response.json()["error_message"]

    def test_error_when_requested_with_not_exist_api_key(self, client):
        tweet_id = 1
        api_key = "test_id_18"
        response = client.delete(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            f"Запись лайка твита с id {tweet_id} от пользователя с id {api_key} не существует"
            == response.json()["error_message"]
        )

    def test_error_when_requested_with_not_exist_tweet_id(self, client):
        tweet_id = 150
        api_key = "test"
        response = client.delete(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            f"Запись лайка твита с id {tweet_id} от пользователя с id {api_key} не существует"
            == response.json()["error_message"]
        )

    async def test_successfully_response_when_values_is_normal(
        self, client, db_session
    ):
        async_session = db_session()
        api_key = "test"
        tweet_id = await Tweet.add_tweet(
            async_session, author_id=api_key, content="It's just for test..."
        )

        await Like.add_like(async_session, user_id=api_key, tweet_id=tweet_id)
        likes_count_before = await Like.get_likes_count(async_session)

        response = client.delete(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )
        assert response.status_code == 200
        assert response.json()["result"] is True
        assert likes_count_before == await Like.get_likes_count(async_session) + 1

        await Tweet.delete_tweet(async_session, tweet_id=tweet_id, author_id=api_key)

    async def test_error_when_like_is_not_exist(self, client, db_session):
        async_session = db_session()
        api_key = "test"
        tweet_id = await Tweet.add_tweet(
            async_session, author_id=api_key, content="It's just for test..."
        )

        await Like.add_like(async_session, user_id=api_key, tweet_id=tweet_id)

        client.delete(f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key})
        likes_count_before = await Like.get_likes_count(async_session)
        response = client.delete(
            f"/api/tweets/{tweet_id}/likes", headers={"api-key": api_key}
        )

        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            f"Запись лайка твита с id {tweet_id} от пользователя с id {api_key} не существует"
            == response.json()["error_message"]
        )
        assert likes_count_before == await Like.get_likes_count(async_session)

        await Tweet.delete_tweet(async_session, tweet_id=tweet_id, author_id=api_key)
