"""Dataverse Web API client for D365 integration."""
import time
from typing import Any, Dict, List, Optional

import httpx
from msal import ConfidentialClientApplication

from ..config import get_settings


class DataverseError(Exception):
    """Dataverse API error."""
    pass


class DataverseClient:
    """Async client for Dataverse Web API operations."""

    def __init__(self):
        self.settings = get_settings()
        self._access_token: Optional[str] = None
        self._token_expires: float = 0

    async def _get_access_token(self) -> str:
        """Acquire or refresh OAuth access token."""
        if self._access_token and time.time() < self._token_expires - 60:
            return self._access_token

        if not self.settings.dataverse_client_id:
            raise DataverseError("Dataverse credentials not configured")

        app = ConfidentialClientApplication(
            client_id=self.settings.dataverse_client_id,
            client_credential=self.settings.dataverse_client_secret,
            authority=f"https://login.microsoftonline.com/{self.settings.dataverse_tenant_id}",
        )

        scope = [f"{self.settings.dataverse_url}/.default"]
        result = app.acquire_token_for_client(scopes=scope)

        if "access_token" not in result:
            raise DataverseError(
                f"Failed to acquire token: {result.get('error_description', 'Unknown error')}"
            )

        self._access_token = result["access_token"]
        self._token_expires = time.time() + result.get("expires_in", 3600)

        return self._access_token

    def _build_url(self, entity_set: str, record_id: Optional[str] = None) -> str:
        """Build Web API URL."""
        base_url = f"{self.settings.dataverse_url}/api/data/v9.2/{entity_set}"
        if record_id:
            return f"{base_url}({record_id})"
        return base_url

    async def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> httpx.Response:
        """Execute HTTP request with authentication."""
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Prefer": "return=representation",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
            )

        if response.status_code >= 400:
            raise DataverseError(
                f"Dataverse API error: {response.status_code} - {response.text}"
            )

        return response

    async def create(self, entity_set: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        url = self._build_url(entity_set)
        response = await self._make_request("POST", url, data=data)
        return response.json()

    async def retrieve(
        self,
        entity_set: str,
        record_id: str,
        select: Optional[List[str]] = None,
        expand: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Retrieve a single record by ID."""
        url = self._build_url(entity_set, record_id)
        params = {}

        if select:
            params["$select"] = ",".join(select)
        if expand:
            params["$expand"] = ",".join(expand)

        response = await self._make_request("GET", url, params=params)
        return response.json()

    async def query(
        self,
        entity_set: str,
        select: Optional[List[str]] = None,
        filter_query: Optional[str] = None,
        order_by: Optional[str] = None,
        top: Optional[int] = None,
        expand: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Query records with OData options."""
        url = self._build_url(entity_set)
        params = {}

        if select:
            params["$select"] = ",".join(select)
        if filter_query:
            params["$filter"] = filter_query
        if order_by:
            params["$orderby"] = order_by
        if top:
            params["$top"] = str(top)
        if expand:
            params["$expand"] = ",".join(expand)

        response = await self._make_request("GET", url, params=params)
        return response.json().get("value", [])

    async def update(
        self,
        entity_set: str,
        record_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an existing record."""
        url = self._build_url(entity_set, record_id)
        response = await self._make_request("PATCH", url, data=data)
        return response.json()

    async def upsert(
        self,
        entity_set: str,
        alternate_key: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Upsert record using alternate key."""
        url = f"{self._build_url(entity_set)}({alternate_key})"
        response = await self._make_request("PATCH", url, data=data)
        return response.json()

    async def delete(self, entity_set: str, record_id: str) -> None:
        """Delete a record."""
        url = self._build_url(entity_set, record_id)
        await self._make_request("DELETE", url)


# Singleton instance
_client: Optional[DataverseClient] = None


def get_dataverse_client() -> DataverseClient:
    """Get or create Dataverse client singleton."""
    global _client
    if _client is None:
        _client = DataverseClient()
    return _client
