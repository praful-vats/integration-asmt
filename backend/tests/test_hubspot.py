import pytest #type: ignore
from unittest.mock import patch, AsyncMock
from redis_client import redis

BASE_URL = "/integrations/hubspot"

# 1. Test OAuth Authorization (GET Auth URL)
@pytest.mark.asyncio
async def test_authorize_hubspot(async_client, mock_redis):
    response = await async_client.post(f"{BASE_URL}/authorize", data={
        "user_id": "TestUser",
        "org_id": "TestOrg"
    })
    assert response.status_code == 200
    assert response.json().startswith("https://app.hubspot.com/oauth/authorize")


# 2. Test OAuth Callback Handling
@pytest.mark.asyncio
@patch("hubspot.exchange_code_for_token", new_callable=AsyncMock)
async def test_oauth2callback_hubspot(mock_exchange_token, async_client, mock_redis):
    mock_exchange_token.return_value = {"access_token": "mock_token"}
    
    response = await async_client.get(f"{BASE_URL}/oauth2callback", params={
        "code": "mock_code",
        "state": "TestUser_TestOrg"
    })
    assert response.status_code == 200
    assert await redis.get("TestUser_TestOrg") == b'{"access_token":"mock_token"}'


# 3. Test Credential Retrieval
@pytest.mark.asyncio
async def test_get_hubspot_credentials(async_client, mock_redis):
    await redis.set("TestUser_TestOrg", '{"access_token":"mock_token"}')
    
    response = await async_client.post(f"{BASE_URL}/credentials", data={
        "user_id": "TestUser",
        "org_id": "TestOrg"
    })
    assert response.status_code == 200
    assert response.json() == {"access_token": "mock_token"}


# 4. Test Item Fetching from HubSpot API
@pytest.mark.asyncio
@patch("hubspot.get_hubspot_data", new_callable=AsyncMock)
async def test_get_items_hubspot(mock_get_data, async_client, mock_redis):
    await redis.set("TestUser_TestOrg", '{"access_token":"mock_token"}')
    mock_get_data.return_value = [
        {"id": "1", "name": "Item1"},
        {"id": "2", "name": "Item2"}
    ]
    
    response = await async_client.post(f"{BASE_URL}/load", data={
        "credentials": '{"access_token":"mock_token"}'
    })
    assert response.status_code == 200
    assert response.json() == [
        {"id": "1", "name": "Item1"},
        {"id": "2", "name": "Item2"}
    ]


# 5. Test Unauthorized Credential Retrieval
@pytest.mark.asyncio
async def test_get_hubspot_credentials_not_found(async_client, mock_redis):
    response = await async_client.post(f"{BASE_URL}/credentials", data={
        "user_id": "UnknownUser",
        "org_id": "UnknownOrg"
    })
    assert response.status_code == 404
    assert response.json() == {"detail": "No credentials found for this user/org"}
