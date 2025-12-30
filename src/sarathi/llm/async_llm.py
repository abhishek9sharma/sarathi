"""
Async LLM utilities for parallel processing.

This module provides the foundation for concurrent LLM calls across the framework,
using aiohttp for non-blocking HTTP requests with connection pooling.
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional, Any
from sarathi.config.config_manager import config


class AsyncLLMClient:
    """
    Async client for LLM API calls with connection pooling.
    
    Designed to be reused across multiple requests for efficiency.
    Supports OpenAI-compatible APIs.
    """
    
    def __init__(self, agent_name: str = "default"):
        """
        Initialize the async LLM client.
        
        Args:
            agent_name: Name of the agent configuration to use from config.
        """
        self.agent_name = agent_name
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session with connection pooling."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=config.get("core.timeout", 30))
            connector = aiohttp.TCPConnector(limit=10)  # Connection pool
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
        return self._session
    
    async def close(self):
        """Close the client session. Call when done with the client."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def _get_request_params(self) -> tuple:
        """
        Get URL, headers, and model from config.
        
        Returns:
            Tuple of (url, headers, model_name)
        """
        agent_conf = config.get_agent_config(self.agent_name) or {}
        provider_name = agent_conf.get("provider", "openai")
        provider_conf = config.get_provider_config(provider_name)
        
        base_url = provider_conf.get("base_url", "https://api.openai.com/v1")
        url = f"{base_url.rstrip('/')}/chat/completions"
        
        headers = {"Content-Type": "application/json"}
        api_key = provider_conf.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        model = agent_conf.get("model", "gpt-4o-mini")
        
        return url, headers, model
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 150,
        temperature: float = 0.5,
    ) -> str:
        """
        Make a single async completion call.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-1).
            
        Returns:
            The content of the assistant's response.
            
        Raises:
            aiohttp.ClientError: If the request fails.
        """
        url, headers, model = self._get_request_params()
        
        body = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        session = await self._get_session()
        async with session.post(url, headers=headers, json=body) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
    
    async def complete_batch(
        self,
        message_batches: List[List[Dict[str, str]]],
        max_concurrent: int = 4,
        **kwargs
    ) -> List[Any]:
        """
        Process multiple completions with concurrency limit.
        
        Args:
            message_batches: List of message lists, each representing one completion.
            max_concurrent: Maximum number of concurrent requests.
            **kwargs: Additional arguments passed to complete().
            
        Returns:
            List of results (strings) or exceptions for each batch.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_complete(messages: List[Dict]) -> str:
            async with semaphore:
                return await self.complete(messages, **kwargs)
        
        tasks = [bounded_complete(msgs) for msgs in message_batches]
        return await asyncio.gather(*tasks, return_exceptions=True)


# --- Convenience Functions ---

async def call_llm_async(
    messages: List[Dict[str, str]],
    agent_name: str = "commit_generator",
    **kwargs
) -> str:
    """
    Simple async LLM call for one-off usage.
    
    For multiple calls, prefer creating an AsyncLLMClient instance directly.
    
    Args:
        messages: List of message dicts.
        agent_name: Agent configuration to use.
        **kwargs: Additional arguments for complete().
        
    Returns:
        The assistant's response content.
    """
    client = AsyncLLMClient(agent_name)
    try:
        return await client.complete(messages, **kwargs)
    finally:
        await client.close()
