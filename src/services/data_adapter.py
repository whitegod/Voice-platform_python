"""
Data Adapter
Handles external API integration and communication
"""

import logging
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import time

logger = logging.getLogger(__name__)


class DataAdapter:
    """
    Adapter for calling external backend APIs.
    Handles authentication, retries, and error handling.
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        default_headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize data adapter.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            default_headers: Default HTTP headers
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_headers = default_headers or {
            "Content-Type": "application/json",
            "User-Agent": "VaaS-Platform/1.0"
        }
        
        logger.info("DataAdapter initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def call_api(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to external API.

        Args:
            endpoint: API endpoint URL
            method: HTTP method
            data: Request body
            headers: HTTP headers
            params: Query parameters
            auth_token: Authentication token

        Returns:
            API response data
        """
        start_time = time.time()
        
        try:
            # Merge headers
            request_headers = {**self.default_headers}
            if headers:
                request_headers.update(headers)
            
            # Add authentication
            if auth_token:
                request_headers["Authorization"] = f"Bearer {auth_token}"

            logger.info(f"Calling API: {method} {endpoint}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=endpoint,
                    json=data,
                    headers=request_headers,
                    params=params
                )

                response_time = time.time() - start_time
                
                # Handle response
                response.raise_for_status()
                
                result = {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json() if response.content else {},
                    "response_time": response_time
                }

                logger.info(f"API call successful ({response_time:.2f}s): "
                          f"{response.status_code}")
                
                return result

        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            logger.error(f"API HTTP error: {e.response.status_code} - {e}")
            
            return {
                "success": False,
                "status_code": e.response.status_code,
                "error": str(e),
                "error_type": "http_error",
                "response_time": response_time
            }

        except httpx.TimeoutException as e:
            response_time = time.time() - start_time
            logger.error(f"API timeout: {e}")
            
            return {
                "success": False,
                "status_code": 408,
                "error": "Request timeout",
                "error_type": "timeout",
                "response_time": response_time
            }

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"API call failed: {e}")
            
            return {
                "success": False,
                "status_code": 500,
                "error": str(e),
                "error_type": "unknown",
                "response_time": response_time
            }

    async def call_with_config(
        self,
        intent_config: Any,
        entities: Dict[str, Any],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Call API using intent configuration.

        Args:
            intent_config: Intent configuration object
            entities: Extracted entities
            context: Additional context

        Returns:
            API response
        """
        try:
            # Build request data from entities and context
            request_data = {
                **entities,
                **(context or {})
            }

            # Get auth token if required
            auth_token = None
            if intent_config.requires_auth and context:
                auth_token = context.get("auth_token")

            # Make API call
            response = await self.call_api(
                endpoint=intent_config.api_endpoint,
                method=intent_config.api_method,
                data=request_data,
                headers=intent_config.api_headers,
                auth_token=auth_token
            )

            return response

        except Exception as e:
            logger.error(f"Failed to call API with config: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "adapter_error"
            }

    async def batch_call(
        self,
        requests: list
    ) -> list:
        """
        Make multiple API calls concurrently.

        Args:
            requests: List of request configurations

        Returns:
            List of responses
        """
        try:
            import asyncio
            
            tasks = [
                self.call_api(**req) for req in requests
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            return [
                resp if not isinstance(resp, Exception) 
                else {"success": False, "error": str(resp)}
                for resp in responses
            ]

        except Exception as e:
            logger.error(f"Batch call failed: {e}")
            return []

    def format_response(
        self,
        api_response: Dict[str, Any],
        template: Optional[str] = None
    ) -> str:
        """
        Format API response using template.

        Args:
            api_response: API response data
            template: Response template string

        Returns:
            Formatted response text
        """
        try:
            if not template:
                # Default formatting
                if api_response.get("success"):
                    return "Request completed successfully."
                else:
                    return f"Request failed: {api_response.get('error', 'Unknown error')}"

            # Simple template substitution
            data = api_response.get("data", {})
            formatted = template
            
            for key, value in data.items():
                placeholder = "{" + key + "}"
                formatted = formatted.replace(placeholder, str(value))

            return formatted

        except Exception as e:
            logger.error(f"Failed to format response: {e}")
            return "Unable to format response."

