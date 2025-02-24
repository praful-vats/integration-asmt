import pytest
from unittest.mock import AsyncMock, patch
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
from integrations.notion import authorize_notion, oauth2callback_notion, get_notion_credentials

USER_ID = 'test_user'
ORG_ID = 'test_org'


@pytest.mark.asyncio
async def test_authorize_notion():
    with patch('redis_client.add_key_value_redis', new_callable=AsyncMock) as mock_add_key:
        auth_url = await authorize_notion(USER_ID, ORG_ID)
        assert 'https://api.notion.com/v1/oauth/authorize' in auth_url
        mock_add_key.assert_called()

@pytest.mark.asyncio
async def test_oauth2callback_notion():
    request = AsyncMock()
    request.query_params = {'code': 'test_code', 'state': '{"state":"test_state"}'}
    with patch('redis_client.get_value_redis', new_callable=AsyncMock) as mock_get_key, \
         patch('redis_client.delete_key_redis', new_callable=AsyncMock) as mock_delete_key, \
         patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:

        mock_get_key.return_value = '{"state":"test_state"}'
        mock_post.return_value.json.return_value = {'access_token': 'test_token'}

        response = await oauth2callback_notion(request)

        assert '<script>window.close();</script>' in response.body.decode()
        mock_delete_key.assert_called()

@pytest.mark.asyncio
async def test_get_notion_credentials():
    with patch('redis_client.get_value_redis', new_callable=AsyncMock) as mock_get_key, \
         patch('redis_client.delete_key_redis', new_callable=AsyncMock) as mock_delete_key:

        mock_get_key.return_value = '{"access_token":"test_token"}'

        credentials = await get_notion_credentials(USER_ID, ORG_ID)

        assert credentials['access_token'] == 'test_token'
        mock_delete_key.assert_called()
