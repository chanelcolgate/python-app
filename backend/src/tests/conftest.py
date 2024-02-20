import asyncio
import httpx
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager

from src.app import app

collect_ignore = ["path/to/test/excluded"]
collect_ignore_glob = ["*_ignore.py"]


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def client():
    async with LifespanManager(app):
        async with httpx.AsyncClient(app=app, base_url="http://app.io") as c:
            yield c
