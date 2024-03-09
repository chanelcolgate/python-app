import logging
import os
import base64

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from fastapi import status

from src.app import app
from src.models.image_display import Images


@pytest.mark.anyio
async def test_showroom_grading_1(client: AsyncClient):
    response = await client.post(
        "/image-display/showroom-grading",
        json={
            "image": "http://10.20.1.90/image/002df0a7-25c2-47d0-b3e8-e513c3c0d9de.jpeg",
            "location": {"latitude": 16.0590299, "longitude": 108.2075305},
            "program_id": "HPLO_01",
        },
    )
    # logging.info(response.json()["result"])
    assert response.status_code == status.HTTP_200_OK, response.text

    data = response.json()
    assert data["result"] == "pass"

    await client.delete(f"/image-display/HPLO")


@pytest.mark.anyio
async def test_showroom_grading_2(client: AsyncClient):
    PATH = os.path.abspath(os.path.dirname(__file__))
    image_path = PATH + "/image_test.jpg"
    image_file = open(image_path, "rb")
    base64_bytes = base64.b64encode(image_file.read()).decode("utf-8")
    # logging.info(base64_bytes[:10])
    # /9j/4AAQSk
    response = await client.post(
        "/image-display/showroom-grading",
        json={
            "image": base64_bytes,
            "location": {"latitude": 16.0590299, "longitude": 108.2075305},
            "program_id": "HPLO_01",
        },
    )
    assert response.status_code == status.HTTP_200_OK, response.text

    data = response.json()
    assert data["result"] == "pass"

    await client.delete(f"/image-display/HPLO")


@pytest.mark.anyio
async def test_showroom_grading_3(client: AsyncClient):
    response = await client.post(
        "/image-display/showroom-grading",
        json={
            "image": "http://10.20.1.90/image/002df0a7-25c2-47d0-b3e8-e513c3c0d9de.jpeg",
            "location": {"latitude": 16.0590299, "longitude": 108.2075305},
            "program_id": "HPLO_01",
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.text

    response = await client.post(
        "/image-display/showroom-grading",
        json={
            "image": "http://10.20.1.90/image/002df0a7-25c2-47d0-b3e8-e513c3c0d9de.jpeg",
            "location": {"latitude": 16.0590299, "longitude": 108.2075305},
            "program_id": "HPLO_01",
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.text

    data = response.json()
    assert data["result"] == "Duplicated"

    await client.delete("/image-display/HPLO")


@pytest.mark.anyio
async def test_showroom_grading_4(client: AsyncClient):
    response = await client.post(
        "/image-display/showroom-grading",
        json={
            "image": "http://10.20.1.90/image/002df0a7-25c2-47d0-b3e8-e513c3c0d9de.jpeg",
            "location": {"latitude": 16.0590299, "longitude": 108.2075305},
            "program_id": "HPLO_02",
        },
    )

    assert response.status_code == status.HTTP_200_OK, response.text

    # logging.info(response.json())
    # {'result': 'fail', 'reason': "Don't have hop_jn, Not enough hop_vtg", 'program_id': 'HPLO_02', 'image_url': '5aa181e6ca8f607be9b240904f9f245f0ed37e7b.jpg'}

    data = response.json()
    assert data["result"] == "fail"

    await client.delete("/image-display/HPLO")
