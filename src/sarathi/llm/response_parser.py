"""
Response Parser Module - Handles parsing and cleaning LLM responses.

This module is responsible for:
- Extracting content from streaming/non-streaming responses
- Handling reasoning model specific content (reasoning_content)
- Filtering out system prompt artifacts from reasoning models
- Aggregating tool calls from streaming chunks
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional, Union


@dataclass
class ParsedChunk:
    """Represents a parsed chunk from an LLM response."""

    content: str = ""
    reasoning_content: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    is_complete: bool = False


@dataclass
class ToolCall:
    """Represents a tool call extracted from an LLM response."""

    id: str
    name: str
    arguments: str

    def to_dict(self) -> Dict:
        """Convert to dictionary format for message history."""
        return {
            "id": self.id,
            "type": "function",
            "function": {"name": self.name, "arguments": self.arguments},
        }


class ResponseParser:
    """Parser for LLM responses with support for reasoning models."""

    # Common patterns for system prompt artifacts in reasoning content
    SYSTEM_PROMPT_PATTERNS = [
        r"^<\|system\|>.*?<\|/system\|>\s*",  # SGLang style
        r"^<system>.*?</system>\s*",  # Generic XML style
        r"^\[SYSTEM\].*?\[/SYSTEM\]\s*",  # Bracket style
        r"^System:.*?\n\n",  # Plain text style
    ]

    def __init__(self, is_reasoning_model: bool = False):
        """
        Initialize the parser.

        Args:
            is_reasoning_model: Whether parsing for a reasoning model.
        """
        self.is_reasoning_model = is_reasoning_model
        self._compiled_patterns = [
            re.compile(p, re.DOTALL | re.IGNORECASE)
            for p in self.SYSTEM_PROMPT_PATTERNS
        ]

    def clean_reasoning_content(self, content: str) -> str:
        """
        Remove system prompt artifacts from reasoning content.

        Some providers (e.g., SGLang) may include system prompts at the
        beginning of reasoning_content. This method strips them out.

        Args:
            content: Raw reasoning content.

        Returns:
            Cleaned reasoning content.
        """
        if not content:
            return content

        cleaned = content
        for pattern in self._compiled_patterns:
            cleaned = pattern.sub("", cleaned)

        return cleaned.strip()

    def parse_streaming_chunk(self, chunk: Dict) -> ParsedChunk:
        """
        Parse a single streaming chunk.

        Args:
            chunk: Raw chunk from streaming API.

        Returns:
            ParsedChunk with extracted data.
        """
        result = ParsedChunk()

        choices = chunk.get("choices")
        if not choices:
            return result

        delta = choices[0].get("delta", {})
        finish_reason = choices[0].get("finish_reason")

        # Extract content
        content = delta.get("content")
        if content:
            result.content = content

        # Extract reasoning content (for reasoning models)
        if self.is_reasoning_model:
            reasoning = delta.get("reasoning_content")
            if reasoning:
                result.reasoning_content = self.clean_reasoning_content(reasoning)

        # Extract tool calls
        tool_calls_delta = delta.get("tool_calls")
        if tool_calls_delta:
            result.tool_calls = tool_calls_delta

        result.is_complete = finish_reason is not None

        return result

    def parse_sync_response(self, response: Dict) -> ParsedChunk:
        """
        Parse a non-streaming (synchronous) response.

        Args:
            response: Full response from API.

        Returns:
            ParsedChunk with extracted data.
        """
        result = ParsedChunk()

        choices = response.get("choices")
        if not choices:
            return result

        message = choices[0].get("message", {})

        # Extract content
        content = message.get("content")
        if content:
            result.content = content

        # Extract reasoning content
        if self.is_reasoning_model:
            reasoning = message.get("reasoning_content")
            if reasoning:
                result.reasoning_content = self.clean_reasoning_content(reasoning)

        # Extract tool calls
        tool_calls = message.get("tool_calls")
        if tool_calls:
            result.tool_calls = tool_calls

        result.is_complete = True

        return result


class ToolCallAggregator:
    """Aggregates tool call chunks from streaming responses."""

    def __init__(self):
        """Initialize the aggregator."""
        self._chunks: Dict[int, Dict] = {}

    def add_chunk(self, tool_calls: List[Dict]) -> None:
        """
        Add tool call chunks to the aggregator.

        Args:
            tool_calls: List of tool call deltas from a streaming chunk.
        """
        for tc in tool_calls:
            idx = tc.get("index", 0)

            if idx not in self._chunks:
                self._chunks[idx] = {
                    "id": tc.get("id"),
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                }

            if tc.get("id"):
                self._chunks[idx]["id"] = tc.get("id")

            func = tc.get("function", {})
            if func.get("name"):
                self._chunks[idx]["function"]["name"] += func.get("name")
            if func.get("arguments"):
                self._chunks[idx]["function"]["arguments"] += func.get("arguments")

    def get_complete_calls(self) -> List[Dict]:
        """
        Get the list of complete tool calls.

        Returns:
            List of complete tool call dictionaries.
        """
        return list(self._chunks.values())

    def has_calls(self) -> bool:
        """Check if any tool calls have been aggregated."""
        return len(self._chunks) > 0

    def clear(self) -> None:
        """Clear all aggregated chunks."""
        self._chunks = {}
