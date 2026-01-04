"""
LLM Client Module - Handles HTTP communication with LLM providers.

This module is responsible for:
- Making streaming and non-streaming API calls
- Handling retries and rate limiting
- Recording usage statistics
"""

import json
import time
from typing import Any, Dict, Generator, List, Optional

import httpx

from sarathi.config.config_manager import config
from sarathi.utils.usage import usage_tracker


class LLMClient:
    """Client for making LLM API calls with streaming and non-streaming support."""

    def __init__(self, agent_name: str = "chat"):
        """
        Initialize the LLM client.

        Args:
            agent_name: Name of the agent configuration to use.
        """
        self.agent_name = agent_name
        self._agent_conf: Optional[Dict] = None
        self._provider_conf: Optional[Dict] = None

    def _load_config(self) -> None:
        """Load agent and provider configuration."""
        from sarathi.llm.call_llm import get_agent_config

        self._agent_conf = get_agent_config(self.agent_name)
        provider_name = self._agent_conf.get("provider", "openai")
        self._provider_conf = config.get_provider_config(provider_name)

    @property
    def agent_conf(self) -> Dict:
        """Get agent configuration, loading if needed."""
        if self._agent_conf is None:
            self._load_config()
        return self._agent_conf

    @property
    def provider_conf(self) -> Dict:
        """Get provider configuration, loading if needed."""
        if self._provider_conf is None:
            self._load_config()
        return self._provider_conf

    @property
    def is_streaming(self) -> bool:
        """Check if streaming is enabled for this agent."""
        return self.agent_conf.get("stream", True)

    @property
    def is_reasoning_model(self) -> bool:
        """Check if this is a reasoning model."""
        return self.agent_conf.get("reasoning_model", False)

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self.agent_conf.get("model", "gpt-4o-mini")

    def _get_url(self) -> str:
        """Get the API endpoint URL."""
        base_url = self.provider_conf.get("base_url", "https://api.openai.com/v1")
        return f"{base_url.rstrip('/')}/chat/completions"

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers including authorization."""
        headers = {"Content-Type": "application/json"}
        api_key = self.provider_conf.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _build_request_body(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        stream: bool = True,
    ) -> Dict[str, Any]:
        """
        Build the request body for the API call.

        Args:
            messages: List of message dicts.
            tools: Optional list of tool definitions.
            stream: Whether to enable streaming.

        Returns:
            Request body dictionary.
        """
        body = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.agent_conf.get("temperature", 0.7),
            "stream": stream,
        }

        # Only include stream_options for models that support it
        # (OpenAI gpt-4o and later, not all providers/models support this)
        if stream and self._supports_stream_options():
            body["stream_options"] = {"include_usage": True}

        if tools:
            body["tools"] = tools

        # Reasoning model adjustments
        if self.is_reasoning_model:
            # Some reasoning models (o1, deepseek-r1) have restrictions
            # - May not support tools
            # - May require temperature=1
            # - May have different response format
            pass  # Override specific params if needed

        return body

    def _supports_stream_options(self) -> bool:
        """Check if the current model supports stream_options parameter."""
        model = self.model_name.lower()
        # Only gpt-4o and newer OpenAI models support stream_options
        supported_models = ["gpt-4o", "gpt-4-turbo", "o1", "o3"]
        return any(supported in model for supported in supported_models)

    def call_streaming(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
    ) -> Generator[Dict, None, None]:
        """
        Make a streaming API call.

        Args:
            messages: List of message dicts.
            tools: Optional list of tool definitions.

        Yields:
            Response chunks as dictionaries.
        """
        url = self._get_url()
        headers = self._get_headers()
        body = self._build_request_body(messages, tools, stream=True)

        if config.get("core.debug"):
            from sarathi.utils.formatters import format_yellow

            print(f"\n{format_yellow('--- DEBUG: LLM STREAM REQUEST ---')}")
            print(json.dumps(body, indent=2))
            print(f"{format_yellow('--- END DEBUG ---')}\n")

        start_time = time.time()
        max_retries = config.get("core.llm_retries", 3)
        retry_delay = 2

        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(
                    timeout=config.get("core.timeout", 30),
                    verify=config.get("core.verify_ssl", True),
                ) as client:
                    with client.stream(
                        "POST", url, headers=headers, json=body, timeout=None
                    ) as res:
                        if res.status_code == 429:
                            if attempt < max_retries:
                                print(
                                    f"⚠️  Rate limited. Retrying in {retry_delay}s... ({attempt + 1}/{max_retries})"
                                )
                                time.sleep(retry_delay)
                                retry_delay *= 2
                                continue

                        res.raise_for_status()

                        total_prompt_tokens = 0
                        total_completion_tokens = 0

                        for line in res.iter_lines():
                            if not line.strip().startswith("data: "):
                                continue

                            json_data = line.strip()[len("data: "):]
                            if json_data == "[DONE]":
                                continue

                            try:
                                chunk = json.loads(json_data)

                                # Track usage
                                usage = chunk.get("usage")
                                if usage:
                                    pt = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
                                    ct = usage.get("completion_tokens") or usage.get("output_tokens") or 0
                                    if pt > 0:
                                        total_prompt_tokens = pt
                                    if ct > 0:
                                        total_completion_tokens = ct

                                yield chunk
                            except json.JSONDecodeError:
                                continue

                        end_time = time.time()
                        usage_tracker.record_call(
                            end_time - start_time,
                            {
                                "prompt_tokens": total_prompt_tokens,
                                "completion_tokens": total_completion_tokens,
                                "total_tokens": total_prompt_tokens + total_completion_tokens,
                            },
                        )
                        return

            except httpx.HTTPError as e:
                if attempt < max_retries:
                    print(
                        f"⚠️  LLM call failed: {e}. Retrying in {retry_delay}s... ({attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise

    def call_sync(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Make a non-streaming (synchronous) API call.

        Args:
            messages: List of message dicts.
            tools: Optional list of tool definitions.

        Returns:
            Full response dictionary.
        """
        url = self._get_url()
        headers = self._get_headers()
        body = self._build_request_body(messages, tools, stream=False)

        if config.get("core.debug"):
            from sarathi.utils.formatters import format_yellow

            print(f"\n{format_yellow('--- DEBUG: LLM REQUEST ---')}")
            print(json.dumps(body, indent=2))
            print(f"{format_yellow('--- END DEBUG ---')}\n")

        start_time = time.time()
        max_retries = config.get("core.llm_retries", 3)
        retry_delay = 2

        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(
                    timeout=config.get("core.timeout", 30),
                    verify=config.get("core.verify_ssl", True),
                ) as client:
                    res = client.post(url, headers=headers, json=body)

                    if res.status_code == 429:
                        if attempt < max_retries:
                            print(
                                f"⚠️  Rate limited. Retrying in {retry_delay}s... ({attempt + 1}/{max_retries})"
                            )
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue

                    res.raise_for_status()
                    end_time = time.time()

                    data = res.json()

                    usage = data.get("usage")
                    usage_tracker.record_call(end_time - start_time, usage)

                    return data

            except httpx.HTTPError as e:
                if attempt < max_retries:
                    print(
                        f"⚠️  LLM call failed: {e}. Retrying in {retry_delay}s... ({attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise

        return {"error": "Max retries exceeded"}
