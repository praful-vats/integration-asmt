import pytest
from unittest.mock import AsyncMock, patch
from integrations.airtable import authorize_airtable, oauth2callback_airtable, get_airtable_credentials, get_items_airtable
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

USER_ID = 'test_user'
ORG_ID = 'test_org'

@pytest.mark.asyncio
async def test_authorize_airtable():
    with patch('redis_client.add_key_value_redis', new_callable=AsyncMock) as mock_add_key:
        auth_url = await authorize_airtable(USER_ID, ORG_ID)
        assert 'https://airtable.com/oauth2/v1/authorize' in auth_url
        mock_add_key.assert_called()

@pytest.mark.asyncio
async def test_oauth2callback_airtable():
    request = AsyncMock()
    request.query_params = {'code': 'test_code', 'state': 'encoded_state'}
    with patch('redis_client.get_value_redis', new_callable=AsyncMock) as mock_get_key, \
         patch('redis_client.delete_key_redis', new_callable=AsyncMock) as mock_delete_key, \
         patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:

        mock_get_key.side_effect = ['{"state":"test_state"}', 'code_verifier']
        mock_post.return_value.json.return_value = {'access_token': 'test_token'}

        response = await oauth2callback_airtable(request)

        assert '<script>window.close();</script>' in response.body.decode()
        mock_delete_key.assert_called()

@pytest.mark.asyncio
async def test_get_airtable_credentials():
    with patch('redis_client.get_value_redis', new_callable=AsyncMock) as mock_get_key, \
         patch('redis_client.delete_key_redis', new_callable=AsyncMock) as mock_delete_key:

        mock_get_key.return_value = '{"access_token":"test_token"}'

        credentials = await get_airtable_credentials(USER_ID, ORG_ID)

        assert credentials['access_token'] == 'test_token'
        mock_delete_key.assert_called()