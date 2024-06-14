from pathlib import Path

import pytest

from models.image import Image
from models.tweet import Tweet
from utility.create_data import create_data


@pytest.mark.usefixtures("client", "db_session")
class TestGetTweetsRoute:

    def test_error_when_requested_without_api_key(self, client):
        response = client.get("/api/tweets")
        assert response.status_code == 422
        assert response.json()["result"] is False

        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    def test_error_when_requested_with_too_length_api_key(self, client):
        api_key = "A" * 33
        response = client.get("/api/tweets", headers={"api-key": api_key})
        assert response.status_code == 422
        assert response.json()["result"] is False

        assert "RequestValidationError" in response.json()["error_type"]
        assert (
            "String should have at most 32 characters"
            in response.json()["error_message"]
        )
        assert api_key in response.json()["error_message"]

    def test_error_when_requested_with_not_exist_user(self, client):
        api_key = "test_id_14"
        response = client.get("/api/tweets", headers={"api-key": api_key})
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            f"Пользоватлея с id {api_key} не существует в БД"
            == response.json()["error_message"]
        )

    async def test_successfully_response_with_following_tweets(
        self, client, db_session
    ):
        async_session = db_session()
        api_key = "test"
        await Tweet.add_tweet(
            async_session, author_id=api_key, content="Some tweet for test app..."
        )
        await Tweet.add_tweet(
            async_session, author_id=api_key, content="Another tweet for test app.."
        )

        response = client.get("/api/tweets", headers={"api-key": api_key})
        assert response.status_code == 200
        assert response.json()["result"] is True
        assert len(response.json()["tweets"]) == 2


@pytest.mark.usefixtures("client", "db_session")
class TestAddTweetRoute:

    def test_error_when_requested_without_api_key(self, client):
        response = client.post("/api/tweets")
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    def test_error_when_requested_with_too_length_api_key(self, client):
        api_key = "A" * 33
        response = client.post("/api/tweets", headers={"api-key": api_key})
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert (
            "String should have at most 32 characters"
            in response.json()["error_message"]
        )
        assert api_key in response.json()["error_message"]

    def test_error_when_requested_without_tweet_data(self, client):
        response = client.post(
            "/api/tweets",
            headers={"api-key": "test"},
            json={"tweet_media_ids": []},
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    def test_error_when_requested_without_tweet_media_ids(self, client):
        response = client.post(
            "/api/tweets",
            headers={"api-key": "test"},
            json={"tweet_data": "It's test text 1..."},
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    def test_error_when_posted_too_big_tweet_data(self, client):
        tweet_data = "A" * 6554
        response = client.post(
            "/api/tweets",
            headers={"api-key": "test"},
            json={"tweet_data": tweet_data, "tweet_media_ids": []},
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert (
            "String should have at most 6553 characters"
            in response.json()["error_message"]
        )
        assert tweet_data in response.json()["error_message"]

    def test_error_when_tweet_data_is_not_string(self, client):
        tweet_data = 123
        response = client.post(
            "/api/tweets",
            headers={"api-key": "test"},
            json={"tweet_data": tweet_data, "tweet_media_ids": []},
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Input should be a valid string" in response.json()["error_message"]
        assert str(tweet_data) in response.json()["error_message"]

    def test_error_when_tweet_media_ids_is_not_list(self, client):
        tweet_data = ""
        tweet_media_ids = 123
        response = client.post(
            "/api/tweets",
            headers={"api-key": "test"},
            json={"tweet_data": tweet_data, "tweet_media_ids": tweet_media_ids},
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Input should be a valid list" in response.json()["error_message"]
        assert str(tweet_media_ids) in response.json()["error_message"]

    def test_error_when_tweet_media_ids_as_list_include_a_not_string_values(
        self, client
    ):
        tweet_data = ""
        tweet_media_ids = [123, 1234, 12345]
        response = client.post(
            "/api/tweets",
            headers={"api-key": "test"},
            json={"tweet_data": tweet_data, "tweet_media_ids": tweet_media_ids},
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Input should be a valid string" in response.json()["error_message"]

        for value in tweet_media_ids:
            assert str(value) in response.json()["error_message"]

    def test_error_when_tweet_media_ids_list_include_over_10_values(self, client):
        tweet_data = ""
        tweet_media_ids = ["path_{}".format(path_num) for path_num in range(1, 12)]
        response = client.post(
            "/api/tweets",
            headers={"api-key": "test"},
            json={"tweet_data": tweet_data, "tweet_media_ids": tweet_media_ids},
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert (
            "List should have at most 10 items after validation, not {}".format(
                len(tweet_media_ids)
            )
            in response.json()["error_message"]
        )
        assert str(tweet_media_ids) in response.json()["error_message"]

    async def test_successfully_response_if_tweet_media_ids_list_is_empty(
        self, client, db_session
    ):
        tweet_data = "It's just text for test..."
        tweet_media_ids = []

        async_session = db_session()
        tweets_count_before = await Tweet.get_all_tweet_ids(async_session)

        response = client.post(
            "/api/tweets",
            headers={"api-key": "test"},
            json={"tweet_data": tweet_data, "tweet_media_ids": tweet_media_ids},
        )

        assert response.status_code == 201
        assert response.json()["result"] is True
        assert isinstance(response.json()["tweet_id"], int)
        assert (
            len(tweets_count_before)
            == len(await Tweet.get_all_tweet_ids(async_session)) - 1
        )

    def test_error_when_posted_tweet_where_author_is_not_exist(self, client):
        api_key = "test_id_15"
        tweet_data = "It's just another text for test..."
        tweet_media_ids = []
        response = client.post(
            "/api/tweets",
            headers={"api-key": api_key},
            json={"tweet_data": tweet_data, "tweet_media_ids": tweet_media_ids},
        )
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            f"Пользователя с id {api_key} не существует"
            == response.json()["error_message"]
        )

    def test_error_when_posted_with_not_exist_ids_in_tweet_media_ids(self, client):
        api_key = "test"
        tweet_data = "It's just another text for test..."
        tweet_media_ids = ["path_{}".format(path_num) for path_num in range(1, 5)]
        response = client.post(
            "/api/tweets",
            headers={"api-key": api_key},
            json={"tweet_data": tweet_data, "tweet_media_ids": tweet_media_ids},
        )
        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            "Получен список id изображений, которых не существуeт в БД:"
            in response.json()["error_message"]
        )
        assert str(tweet_media_ids) in response.json()["error_message"]

    async def test_successfully_response_if_arguments_is_normal(
        self, client, db_session
    ):
        api_key = "test"
        tweet_data = "It's just another text with medias for test..."

        await create_data(db_session, images_count=5)
        async_session = db_session()
        tweet_media_ids = await Image.get_all_image_ids(async_session)
        all_tweets_before = await Tweet.get_all_tweet_ids(async_session)

        response = client.post(
            "/api/tweets",
            headers={"api-key": api_key},
            json={"tweet_data": tweet_data, "tweet_media_ids": tweet_media_ids},
        )
        all_tweets_after = await Tweet.get_all_tweet_ids(async_session)
        assert response.status_code == 201
        assert response.json()["result"] is True
        assert len(all_tweets_before) == len(all_tweets_after) - 1
        added_tweet: Tweet = await Tweet.get_tweet_by_id(
            async_session, response.json()["tweet_id"]
        )

        for path in added_tweet.attachments:
            assert Path("static", path).exists()

        for tweet_id in all_tweets_after:
            await Tweet.delete_tweet(
                async_session, author_id=api_key, tweet_id=tweet_id
            )


@pytest.mark.usefixtures("client", "db_session")
class TestDeleteTweetRoute:

    def test_error_when_requested_with_string_type_tweet_id(self, client):
        tweet_id = "ABC"
        api_key = "test"
        response = client.delete(
            f"/api/tweets/{tweet_id}", headers={"api-key": api_key}
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Input should be a valid integer" in response.json()["error_message"]
        assert tweet_id in response.json()["error_message"]

    def test_error_when_requested_without_api_key(self, client):
        tweet_id = 1
        response = client.delete(f"/api/tweets/{tweet_id}")
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    def test_error_when_requested_with_too_length_api_key(self, client):
        tweet_id = 1
        api_key = "A" * 33
        response = client.delete(
            f"/api/tweets/{tweet_id}", headers={"api-key": api_key}
        )
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert (
            "String should have at most 32 characters"
            in response.json()["error_message"]
        )
        assert api_key in response.json()["error_message"]

    async def test_error_when_requested_with_not_exist_api_key(
        self, client, db_session
    ):
        async_session = db_session()
        await create_data(db_session, tweets_count=3)
        tweet_ids = await Tweet.get_all_tweet_ids(async_session)

        tweet_id = tweet_ids[0]
        api_key = "test_id_16"
        response = client.delete(
            f"/api/tweets/{tweet_id}", headers={"api-key": api_key}
        )

        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            f"Пользователя с id {api_key} не существует"
            in response.json()["error_message"]
        )

    async def test_error_when_requested_with_not_exist_tweet_id(self, client):
        tweet_id = 100
        api_key = "test"
        response = client.delete(
            f"/api/tweets/{tweet_id}", headers={"api-key": api_key}
        )

        assert response.status_code == 404
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert f"Твит с id {tweet_id} не существует" in response.json()["error_message"]

    async def test_successfully_response_with_normal_values(self, client, db_session):
        async_session = db_session()
        api_key = "test"
        tweet_id = await Tweet.add_tweet(
            async_session, author_id=api_key, content="It's just text for text..."
        )
        all_tweets_before = await Tweet.get_all_tweet_ids(async_session)

        response = client.delete(
            f"/api/tweets/{tweet_id}", headers={"api-key": api_key}
        )
        all_tweets_after = await Tweet.get_all_tweet_ids(async_session)
        assert response.status_code == 200
        assert response.json()["result"] is True
        assert len(all_tweets_before) == len(all_tweets_after) + 1
