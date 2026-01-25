"""
Agent Engine Module - Orchestrates LLM interactions with tool support.

This module is responsible for:
- Managing conversation history
- Coordinating between LLM client and tool execution
- Handling streaming and non-streaming modes
- Processing tool calls and responses
"""

from typing import Any, Callable, Dict, Generator, List, Optional, Union

from sarathi.llm.llm_client import LLMClient
from sarathi.llm.response_parser import ParsedChunk, ResponseParser, ToolCallAggregator
from sarathi.llm.tools import registry


class AgentEngine:
    """
    Engine for running LLM-powered agents with tool support.

    Supports both streaming and non-streaming modes, with special
    handling for reasoning models.
    """

    def __init__(
        self,
        agent_name: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[str]] = None,
        tool_confirmation_callback: Optional[Callable[[str, str], bool]] = None,
    ):
        """
        Initialize the agent engine.

        Args:
            agent_name: Name of the agent configuration to use.
            system_prompt: Optional system prompt override.
            tools: List of tool names to enable.
            tool_confirmation_callback: Callback for tool execution confirmation.
        """
        from sarathi.config.config_manager import config

        self.agent_name = agent_name
        self.client = LLMClient(agent_name)
        self.parser = ResponseParser(is_reasoning_model=self.client.is_reasoning_model)

        # Load system prompt from config if not provided
        if system_prompt is None:
            system_prompt = config.get(f"prompts.{agent_name}")

        self.system_prompt = system_prompt
        self.tools = tools or []
        self.tool_confirmation_callback = tool_confirmation_callback

        # Initialize message history
        self.messages: List[Dict] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def run(self, user_input: str) -> str:
        """
        Blocking version of run.

        Args:
            user_input: User's input message.

        Returns:
            Complete response as a string.
        """
        result = ""
        for chunk in self.run_stream(user_input):
            if isinstance(chunk, str):
                result += chunk
        return result

    def run_stream(
        self, user_input: str
    ) -> Generator[Union[str, Dict[str, Any]], None, None]:
        """
        Generator version of run that yields content tokens and events.

        Args:
            user_input: User's input message.

        Yields:
            String tokens for content, or dict events for tool calls.
        """
        self.messages.append({"role": "user", "content": user_input})

        # Determine streaming mode
        use_streaming = self.client.is_streaming
        is_reasoning = self.client.is_reasoning_model

        # Reasoning models may default to non-streaming
        if is_reasoning and "stream" not in self.client.agent_conf:
            use_streaming = False

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            if use_streaming:
                yield from self._run_streaming_iteration()
            else:
                yield from self._run_sync_iteration()

            # Check if we should continue (tool calls were processed)
            # The iteration methods return True if we should continue
            if not self._should_continue_iteration():
                return

        yield "⚠️ Safety Limit reached (10 tool iterations)."

    def _run_streaming_iteration(
        self,
    ) -> Generator[Union[str, Dict[str, Any]], None, None]:
        """
        Run a single streaming iteration.

        Yields:
            Content tokens and tool call events.
        """
        tool_aggregator = ToolCallAggregator()
        full_content = ""
        full_reasoning = ""

        # Get tool definitions if tools are enabled
        tools = registry.get_tool_definitions() if self.tools else None

        for chunk in self.client.call_streaming(self.messages, tools):
            parsed = self.parser.parse_streaming_chunk(chunk)

            # Yield content
            if parsed.content:
                full_content += parsed.content
                yield parsed.content

            # Accumulate reasoning content (optionally yield it too)
            if parsed.reasoning_content:
                full_reasoning += parsed.reasoning_content
                # Optionally yield reasoning with a special marker
                # yield {"type": "reasoning", "content": parsed.reasoning_content}

            # Aggregate tool calls
            if parsed.tool_calls:
                tool_aggregator.add_chunk(parsed.tool_calls)

        # Process tool calls if any
        if tool_aggregator.has_calls():
            yield from self._process_tool_calls(
                tool_aggregator.get_complete_calls(), full_content
            )
            self._mark_continue_iteration()
        else:
            if full_content:
                self.messages.append({"role": "assistant", "content": full_content})
            self._mark_stop_iteration()

    def _run_sync_iteration(
        self,
    ) -> Generator[Union[str, Dict[str, Any]], None, None]:
        """
        Run a single non-streaming iteration.

        Yields:
            Content as a single chunk, and tool call events.
        """
        tools = registry.get_tool_definitions() if self.tools else None

        response = self.client.call_sync(self.messages, tools)
        parsed = self.parser.parse_sync_response(response)

        # Yield content
        if parsed.content:
            yield parsed.content

        # Process tool calls if any
        if parsed.tool_calls:
            yield from self._process_tool_calls(parsed.tool_calls, parsed.content)
            self._mark_continue_iteration()
        else:
            if parsed.content:
                self.messages.append({"role": "assistant", "content": parsed.content})
            self._mark_stop_iteration()

    def _process_tool_calls(
        self, tool_calls: List[Dict], content: Optional[str]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process tool calls and execute them.

        Args:
            tool_calls: List of tool call dictionaries.
            content: Any content from the assistant message.

        Yields:
            Tool call events.
        """
        # Record assistant message with tool calls
        assistant_msg = {
            "role": "assistant",
            "content": content or None,
            "tool_calls": tool_calls,
        }
        self.messages.append(assistant_msg)

        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            func_args = tool_call["function"]["arguments"]

            # Yield structured event
            yield {"type": "tool_call", "name": func_name, "args": func_args}

            # Check confirmation callback
            if self.tool_confirmation_callback:
                if not self.tool_confirmation_callback(func_name, func_args):
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.get("id"),
                            "name": func_name,
                            "content": "Tool execution was denied by the user.",
                        }
                    )
                    continue

            # Execute tool
            result = registry.call_tool(func_name, func_args)
            self.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "name": func_name,
                    "content": str(result),
                }
            )

    def _mark_continue_iteration(self) -> None:
        """Mark that the main loop should continue."""
        self._should_continue = True

    def _mark_stop_iteration(self) -> None:
        """Mark that the main loop should stop."""
        self._should_continue = False

    def _should_continue_iteration(self) -> bool:
        """Check if the main loop should continue."""
        return getattr(self, "_should_continue", False)
