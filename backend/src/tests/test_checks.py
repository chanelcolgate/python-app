import logging
import os

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from fastapi import status

from src.app import app
from src.models.image_display import Checks


@pytest.mark.anyio
async def test_retrieve_all_checks(client: AsyncClient):
    response = await client.get("/api/check/", headers={"api-key": "ok"})
    logging.info(response.status_code)
    assert response.status_code == status.HTTP_200_OK, response.text


@pytest.mark.anyio
async def test_retrieve_check(client: AsyncClient):
    response = await client.get("/api/check/HPLO", headers={"api-key": "ok"})
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()

    # logging.info(data)
    # {'id': 'HPLO', 'name': 'Bộ hộp', 'matrix': {'hop_jn': 1, 'hop_vtg': 1, 'hop_ytv': 4}}

    assert data["id"] == "HPLO"


@pytest.mark.anyio
async def test_get_checks_404(client: AsyncClient):
    response = await client.get("/api/check/TEST", headers={"api-key": "ok"})
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


@pytest.mark.anyio
async def test_create_check(client: AsyncClient):
    response = await client.post(
        "/api/check/new",
        json={
            "id": "TEST",
            "matrix": {"hop_jn": 1, "hop_vtg": 1, "hop_ytv": 4},
            "name": "Bộ hộp",
        },
        headers={"api-key": "ok"},
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text


@pytest.mark.anyio
async def test_update_check(client: AsyncClient):
    response = await client.put(
        "/api/check/edit/TEST",
        json={
            "name": "Bộ test",
            "matrix": {
                "hop_jn": 1,
                "hop_vtg": 1,
                "hop_ytv": 5,
            },
        },
        headers={"api-key": "ok"},
    )


@pytest.mark.anyio
async def test_error_xlsx(client: AsyncClient):
    PATH = os.path.abspath(os.path.dirname(__file__))
    files = {"file": open(PATH + "/bo_trung_bay_test.csv", "rb")}
    response = await client.post(
        "/api/check/uploadfile", files=files, headers={"api-key": "ok"}
    )
    assert (
        response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    ), response.text


@pytest.mark.anyio
async def test_upload_file(client: AsyncClient):
    PATH = os.path.abspath(os.path.dirname(__file__))
    files = {"file": open(PATH + "/bo_trung_bay_test.xlsx", "rb")}
    response = await client.post(
        "/api/check/uploadfile", files=files, headers={"api-key": "ok"}
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()[0]

    assert "id" in data
    assert data["id"] == "TEST"
    check_id = data["id"]

    check_obj = await Checks.get(id=check_id)
    assert check_obj.id == check_id
    await client.delete(f"/api/check/{check_id}", headers={"api-key": "ok"})
