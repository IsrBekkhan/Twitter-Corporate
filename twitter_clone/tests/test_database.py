from pathlib import Path

from models.image import Image
from models.like import Like
from models.tweet import Tweet
from models.user import User


async def test_cascade_delete_tweet_after_delete_user(db_session):
    async_session = db_session()
    user_id = "test_id_20"
    name = "Testname_20"

    user = await User.add_user(async_session, user_id=user_id, name=name)
    await Tweet.add_tweet(
        async_session, author_id=user.id, content="Some simple text for test..."
    )

    tweets_before = await Tweet.get_all_tweet_ids(async_session)
    await User.delete_user(async_session, user_id=user.id)
    tweets_after = await Tweet.get_all_tweet_ids(async_session)

    assert len(tweets_before) == len(tweets_after) + 1


async def test_cascade_delete_subscribe_after_delete_user(db_session):
    async_session = db_session()
    user_id_1 = "test_id_21"
    name_1 = "Testname_21"

    user_id_2 = "test_id_22"
    name_2 = "Testname_22"

    user_1 = await User.add_user(async_session, user_id=user_id_1, name=name_1)
    user_2 = await User.add_user(async_session, user_id=user_id_2, name=name_2)
    await User.follow(
        async_session, follower_user_id=user_1.id, following_user_id=user_2.id
    )

    subscribes_before = await User.get_subscribes_count(async_session)
    await User.delete_user(async_session, user_id=user_1.id)
    subscribes_after = await User.get_subscribes_count(async_session)

    assert subscribes_before == subscribes_after + 1


async def test_cascade_delete_like_after_delete_tweet(db_session):
    async_session = db_session()
    user_id = "test"

    tweet = await Tweet.add_tweet(
        async_session, author_id=user_id, content="Some simple text for test..."
    )
    await Like.add_like(async_session, user_id=user_id, tweet_id=tweet)

    likes_before = await Like.get_likes_count(async_session)
    await Tweet.delete_tweet(async_session, author_id=user_id, tweet_id=tweet)
    likes_after = await Like.get_likes_count(async_session)

    assert likes_before == likes_after + 1


async def test_cascade_delete_like_after_delete_user(db_session):
    async_session = db_session()
    user_id = "test_id_23"
    name = "Testname_23"

    user = await User.add_user(async_session, user_id=user_id, name=name)

    tweet = await Tweet.add_tweet(
        async_session, author_id=user.id, content="Some simple text for test..."
    )
    await Like.add_like(async_session, user_id=user.id, tweet_id=tweet)

    likes_before = await Like.get_likes_count(async_session)
    await Tweet.delete_tweet(async_session, author_id=user.id, tweet_id=tweet)
    likes_after = await Like.get_likes_count(async_session)

    assert likes_before == likes_after + 1


async def test_cascade_delete_image_after_delete_tweet(db_session):
    async_session = db_session()
    filename = "image.jpg"
    user_id = "test"

    with open(Path("tests", "media", filename), mode="rb") as image_file:
        image_id = await Image.add_image(
            async_session, image=image_file.read(), filename=filename
        )

    tweet_id = await Tweet.add_tweet(
        async_session,
        author_id=user_id,
        content="Some simple text for test...",
        tweet_media_ids=[image_id],
    )
    images_before = await Image.get_all_image_ids(async_session)
    await Tweet.delete_tweet(async_session, author_id=user_id, tweet_id=tweet_id)
    images_after = await Image.get_all_image_ids(async_session)

    assert len(images_before) == len(images_after) + 1
