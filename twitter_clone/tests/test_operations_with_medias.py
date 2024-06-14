from pathlib import Path

import pytest

from models.image import Image


@pytest.mark.usefixtures("client", "db_session")
class TestPostImageRoute:

    def test_error_when_requested_with_false_form_data_key(self, client):
        file = {"file_test": open(Path("tests", "media", "image.jpg"), mode="rb")}
        response = client.post("/api/medias", files=file)
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "RequestValidationError" in response.json()["error_type"]
        assert "Field required" in response.json()["error_message"]

    async def test_error_when_requested_without_file(self, client, db_session):
        async_session = db_session()
        file = {"file": open(Path("tests", "media", "image.jpg"), mode="rb")}
        images_before = await Image.get_all_image_ids(async_session)

        response = client.post("/api/medias", files=file)
        images_after = await Image.get_all_image_ids(async_session)
        assert response.status_code == 201
        assert response.json()["result"] is True
        assert isinstance(response.json()["media_id"], str)
        assert len(response.json()["media_id"]) == 32
        assert len(images_before) == len(images_after) - 1

        await Image.delete_image(async_session, response.json()["media_id"])

    def test_error_when_requested_without_image_file(self, client):
        file = {"file": "test_string"}
        response = client.post("/api/medias", files=file)
        assert response.status_code == 422
        assert response.json()["result"] is False
        assert "HTTPException" in response.json()["error_type"]
        assert (
            "В запросе отсутствует файл изображения" == response.json()["error_message"]
        )
