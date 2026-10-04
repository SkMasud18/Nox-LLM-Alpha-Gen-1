"""
Official Nox Intelligence Python SDK Client
Author: Sk Masud Rahaman (@SkMasud18) - Falcon Intelligence
Seamless interface for streaming completions from Nox Sovereign Cloud or Local Endpoints.
"""

import httpx
import json
from typing import AsyncGenerator, Dict, Any, List

class NoxClient:
    def __init__(self, base_url: str = "https://noxassistant.com", api_token: str = None):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        thinking_budget: int = 8192
    ) -> AsyncGenerator[str, None]:
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        payload = {
            "messages": messages,
            "thinking_budget": thinking_budget,
            "stream": True
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat/stream",
                json=payload,
                headers=headers
            ) as response:
                async for chunk in response.aiter_text():
                    if chunk:
                        yield chunk
