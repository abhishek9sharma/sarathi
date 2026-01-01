import json
import time

from sarathi.llm.call_llm import call_llm_model
from sarathi.llm.tools import registry


class AgentEngine:
    def __init__(
        self,
        agent_name,
        system_prompt=None,
        tools=None,
        tool_confirmation_callback=None,
    ):
        from sarathi.config.config_manager import config

        self.agent_name = agent_name

        # If no explicit system_prompt provided, try loading from config
        if system_prompt is None:
            system_prompt = config.get(f"prompts.{agent_name}")

        self.system_prompt = system_prompt
        self.tools = tools or []
        self.tool_confirmation_callback = tool_confirmation_callback
        self.messages = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def run(self, user_input):
        """Blocking version of run."""
        res = ""
        for chunk in self.run_stream(user_input):
            if isinstance(chunk, str):
                res += chunk
        return res

    def run_stream(self, user_input):
        """Generator version of run that yields content tokens."""
        self.messages.append({"role": "user", "content": user_input})

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Implementation of streaming call
            full_content = ""
            tool_calls_chunks = {}  # index -> tool_call object

            for chunk in self._call_llm_stream():
                delta = chunk.get("choices", [{}])[0].get("delta", {})

                # Handle content
                content = delta.get("content")
                if content:
                    full_content += content
                    yield content

                # Handle tool calls
                tool_calls_delta = delta.get("tool_calls")
                if tool_calls_delta:
                    for tc in tool_calls_delta:
                        idx = tc.get("index", 0)
                        if idx not in tool_calls_chunks:
                            tool_calls_chunks[idx] = {
                                "id": tc.get("id"),
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }

                        f = tc.get("function", {})
                        if tc.get("id"):
                            tool_calls_chunks[idx]["id"] = tc.get("id")
                        if f.get("name"):
                            tool_calls_chunks[idx]["function"]["name"] += f.get("name")
                        if f.get("arguments"):
                            tool_calls_chunks[idx]["function"]["arguments"] += f.get(
                                "arguments"
                            )

            # After stream ends, check for tool calls
            if tool_calls_chunks:
                tool_calls = list(tool_calls_chunks.values())
                # Constructassistant message for history
                assistant_msg = {
                    "role": "assistant",
                    "content": full_content or None,
                    "tool_calls": tool_calls,
                }
                self.messages.append(assistant_msg)

                for tool_call in tool_calls:
                    func_name = tool_call["function"]["name"]
                    func_args = tool_call["function"]["arguments"]

                    yield f"\n[dim]Calling tool: {func_name}...[/dim]\n"

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

                    result = registry.call_tool(func_name, func_args)
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.get("id"),
                            "name": func_name,
                            "content": str(result),
                        }
                    )
                # Continue loop
                continue
            else:
                # No tool calls, finish
                if full_content:
                    self.messages.append({"role": "assistant", "content": full_content})
                return

        yield "⚠️ Safety Limit reached (10 tool iterations)."

    def _call_llm_stream(self):
        import httpx

        from sarathi.config.config_manager import config
        from sarathi.llm.call_llm import get_agent_config
        from sarathi.utils.usage import usage_tracker

        agent_conf = get_agent_config(self.agent_name)
        provider_name = agent_conf.get("provider", "openai")
        provider_conf = config.get_provider_config(provider_name)
        base_url = provider_conf.get("base_url")
        url = f"{base_url.rstrip('/')}/chat/completions"
        api_key = provider_conf.get("api_key")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        body = {
            "model": agent_conf.get("model", "gpt-4o-mini"),
            "messages": self.messages,
            "tools": registry.get_tool_definitions() if self.tools else None,
            "temperature": agent_conf.get("temperature", 0.7),
            "stream": True,  # Enable streaming
        }

        if not body["tools"]:
            del body["tools"]

        if config.get("core.debug"):
            from sarathi.utils.formatters import format_yellow

            print(f"\n{format_yellow('--- DEBUG: LLM STREAM REQUEST BODY ---')}")
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
                                    f"⚠️  Rate limited (429). Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})"
                                )
                                time.sleep(retry_delay)
                                retry_delay *= 2
                                continue

                        res.raise_for_status()

                        # Accumulate usage for streaming
                        total_prompt_tokens = 0
                        total_completion_tokens = 0

                        for line in res.iter_lines():
                            if not line.strip().startswith("data: "):
                                continue

                            json_data = line.strip()[len("data: ") :]
                            if json_data == "[DONE]":
                                continue
                            try:
                                chunk = json.loads(json_data)

                                # Accumulate usage from each chunk if available (some providers send it at the end)
                                usage = chunk.get("usage")
                                if usage:
                                    total_prompt_tokens = usage.get("prompt_tokens", 0)
                                    total_completion_tokens = usage.get(
                                        "completion_tokens", 0
                                    )

                                yield chunk
                            except json.JSONDecodeError:
                                continue

                        end_time = time.time()
                        # Record total usage after stream ends
                        usage_tracker.record_call(
                            end_time - start_time,
                            {
                                "prompt_tokens": total_prompt_tokens,
                                "completion_tokens": total_completion_tokens,
                                "total_tokens": total_prompt_tokens
                                + total_completion_tokens,
                            },
                        )
                        return  # Stream finished successfully
            except httpx.HTTPError as e:
                if attempt < max_retries:
                    print(
                        f"⚠️  LLM stream call failed: {e}. Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise

    def _call_llm(self):
        # We need a version of call_llm_model that accepts full message history and tools
        # Let's adapt call_llm_model or import it and use its logic
        import httpx

        from sarathi.config.config_manager import config
        from sarathi.llm.call_llm import get_agent_config
        from sarathi.utils.usage import usage_tracker

        agent_conf = get_agent_config(self.agent_name)
        provider_name = agent_conf.get("provider", "openai")
        provider_conf = config.get_provider_config(provider_name)
        base_url = provider_conf.get("base_url")
        url = f"{base_url.rstrip('/')}/chat/completions"
        api_key = provider_conf.get("api_key")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        body = {
            "model": agent_conf.get("model", "gpt-4o-mini"),
            "messages": self.messages,
            "tools": registry.get_tool_definitions() if self.tools else None,
            "temperature": agent_conf.get("temperature", 0.7),
        }

        if not body["tools"]:
            del body["tools"]

        if config.get("core.debug"):
            from sarathi.utils.formatters import format_yellow

            print(f"\n{format_yellow('--- DEBUG: LLM REQUEST BODY ---')}")
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
                                f"⚠️  Rate limited (429). Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})"
                            )
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue

                    res.raise_for_status()
                    end_time = time.time()

                    data = res.json()

                    # Record usage
                    usage = data.get("usage")
                    usage_tracker.record_call(end_time - start_time, usage)

                    return data
            except httpx.HTTPError as e:
                if attempt < max_retries:
                    print(
                        f"⚠️  LLM call failed: {e}. Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise
