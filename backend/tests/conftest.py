import pytest #type: ignore
from httpx import AsyncClient #type: ignore
from main import app 
from redis_client import redis

@pytest.fixture(scope="module")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function")
async def mock_redis():
    await redis.flushdb()
    yield redis
    await redis.flushdb()
