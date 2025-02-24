#hubspot.py

import json
import secrets
from typing import List, Optional
from fastapi import Request, HTTPException # type: ignore
from fastapi.responses import HTMLResponse # type: ignore
import httpx # type: ignore
import asyncio
from urllib.parse import urlencode, unquote
from dateutil import parser # type: ignore
import logging
from dotenv import load_dotenv # type: ignore
import os
load_dotenv()

from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HubSpot API Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPES = 'crm.objects.contacts.read crm.objects.companies.read crm.objects.deals.read content oauth'

# HubSpot API endpoints
AUTH_URL = 'https://app.hubspot.com/oauth/authorize'
TOKEN_URL = 'https://api.hubapi.com/oauth/v1/token'
BASE_API_URL = 'https://api.hubapi.com'

def get_authorization_url(state: str) -> str:
    """Generate HubSpot authorization URL with required parameters"""
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'state': state
    }
    return f"{AUTH_URL}?{urlencode(params)}"

async def authorize_hubspot(user_id: str, org_id: str) -> str:
    """
    Initialize OAuth flow for HubSpot integration
    Returns authorization URL for frontend redirect
    """
    try:
        state_data = {
            'state': secrets.token_urlsafe(32),
            'user_id': user_id,
            'org_id': org_id
        }
        encoded_state = json.dumps(state_data)

        result = await add_key_value_redis(
            f'hubspot_state:{org_id}:{user_id}', 
            encoded_state, 
            expire=600
        )
        
        return get_authorization_url(encoded_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authorization initialization failed: {str(e)}")


async def oauth2callback_hubspot(request: Request) -> HTMLResponse:
    """
    Handle OAuth callback from HubSpot
    Exchanges authorization code for access token
    """
    try:
        if request.query_params.get('error'):
            raise HTTPException(
                status_code=400, 
                detail=request.query_params.get('error_description', 'Authorization failed')
            )

        code = request.query_params.get('code')
        encoded_state = request.query_params.get('state')
        
        if not code or not encoded_state:
            raise HTTPException(status_code=400, detail='Missing required parameters')

        decoded_state = unquote(encoded_state).replace('+', ' ')
        
        try:
            state_data = json.loads(decoded_state)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f'Invalid state format: {str(e)}')

        original_state = state_data.get('state')
        user_id = state_data.get('user_id')
        org_id = state_data.get('org_id')

        if not all([original_state, user_id, org_id]):
            raise HTTPException(status_code=400, detail='Missing required state parameters')

        saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
        if not saved_state:
            raise HTTPException(status_code=400, detail='State not found or expired')
            
        try:
            saved_state_data = json.loads(saved_state)
            if original_state != saved_state_data.get('state'):
                raise HTTPException(status_code=400, detail='State mismatch')
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail='Invalid saved state format')

        async with httpx.AsyncClient() as client:
            token_response, _ = await asyncio.gather(
                client.post(
                    TOKEN_URL,
                    data={
                        'grant_type': 'authorization_code',
                        'client_id': CLIENT_ID,
                        'client_secret': CLIENT_SECRET,
                        'redirect_uri': REDIRECT_URI,
                        'code': code
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                ),
                delete_key_redis(f'hubspot_state:{org_id}:{user_id}')
            )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400, 
                detail=f'Failed to obtain access token: {token_response.text}'
            )

        await add_key_value_redis(
            f'hubspot_credentials:{org_id}:{user_id}',
            json.dumps(token_response.json()),
            expire=600
        )

        return HTMLResponse(content="<html><script>window.close();</script></html>")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}")

async def get_hubspot_credentials(user_id: str, org_id: str) -> dict:
    """
    Retrieve stored HubSpot credentials from Redis
    """
    try:
        credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
        if not credentials:
            raise HTTPException(status_code=400, detail='No credentials found')
        
        credentials_dict = json.loads(credentials)
        await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
        
        return credentials_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve credentials: {str(e)}")


async def create_integration_item(item: dict, item_type: str) -> Optional[IntegrationItem]:
    try:
        properties = item.get('properties', {})
        creation_time = parser.isoparse(properties.get('createdate')) if properties.get('createdate') else None
        modified_time = parser.isoparse(properties.get('lastmodifieddate')) if properties.get('lastmodifieddate') else None

        name = None
        if item_type == 'company':
            name = properties.get('name')
        elif item_type == 'contact':
            name = f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip()
        elif item_type == 'deal':
            name = properties.get('dealname')

        if not name:
            name = f"{item_type}_{item.get('id', 'unknown')}"

        return IntegrationItem(
            id=str(item.get('id')),
            type=item_type,
            name=name,
            creation_time=creation_time,
            last_modified_time=modified_time,
            url=f"https://app.hubspot.com/{item_type}s/{item.get('id')}",
            visibility=True
        )
    except Exception as e:
        logger.error(f"Error creating integration item: {str(e)}")
        return None


async def get_items_hubspot(credentials: str) -> List[IntegrationItem]:
    """
    Retrieve and transform HubSpot items into IntegrationItems
    Fetches companies, contacts, and deals
    """
    try:
        credentials_dict = json.loads(credentials)
        access_token = credentials_dict.get('access_token')

        if not access_token:
            raise HTTPException(status_code=400, detail='Invalid credentials')

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        integration_items = []

        endpoints = [
            ('company', f'{BASE_API_URL}/crm/v3/objects/companies'),
            ('contact', f'{BASE_API_URL}/crm/v3/objects/contacts'),
            ('deal', f'{BASE_API_URL}/crm/v3/objects/deals')
        ]

        for item_type, endpoint in endpoints:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    headers=headers,
                    params={
                        'limit': 100,
                        'properties': 'createdate,lastmodifieddate,name,firstname,lastname,dealname'
                    }
                )

                if response.status_code == 200:
                    items = response.json().get('results', [])
                    for item in items:
                        integration_item = await create_integration_item(item, item_type)
                        if integration_item:
                            integration_items.append(integration_item)
                else:
                    logging.error(f"Failed to fetch {item_type}s: {response.status_code} - {response.text}")

        logger.info("list of integration items: %s", [item.__dict__ for item in integration_items])
        return integration_items

    except Exception as e:
        logging.error(f"Error in get_items_hubspot: {str(e)}")
        return []
