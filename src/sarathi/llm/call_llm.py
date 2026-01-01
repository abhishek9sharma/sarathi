import json
import time

import httpx

from sarathi.config.config_manager import config
from sarathi.utils.formatters import clean_llm_response
from sarathi.utils.usage import usage_tracker


def get_agent_config(agent_name):
    """Retrieves the configuration for a specific agent."""
    if not agent_name:
        return {}

    # Map legacy prompt keys to new agent names if needed
    if agent_name == "autocommit":
        agent_name = "commit_generator"

    return config.get_agent_config(agent_name)


def parse_stream(response_iter):
    """Helper to parse OpenAI-style SSE stream chunks."""
    for line in response_iter:
        if not line or not line.startswith("data: "):
            continue
        if line == "data: [DONE]":
            break
        try:
            chunk = json.loads(line[6:])
            yield chunk
        except:
            continue


def call_llm_model(prompt_info, user_msg, resp_type=None, agent_name=None):
    """
    Generate a response from the configured LLM using httpx.
    """
    agent_conf = get_agent_config(agent_name)
    model_name = agent_conf.get("model") or prompt_info.get("model") or "gpt-4o-mini"
    provider_name = agent_conf.get("provider", "openai")
    provider_conf = config.get_provider_config(provider_name)

    system_msg = agent_conf.get("system_prompt")
    if not system_msg:
        system_msg = config.get(f"prompts.{agent_name}")
    if not system_msg:
        system_msg = prompt_info.get("system_msg", "")

    base_url = provider_conf.get("base_url")
    if not base_url:
        raise ValueError(f"base_url not found in config for provider '{provider_name}'")

    url = f"{base_url.rstrip('/')}/chat/completions"
    api_key = provider_conf.get("api_key")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 500,
        "n": 1,
        "temperature": agent_conf.get("temperature", 0.7),
    }

    max_retries = config.get("core.llm_retries", 3)
    retry_delay = 2

    for attempt in range(max_retries + 1):
        try:
            with httpx.Client(
                timeout=config.get("core.timeout", 30),
                verify=config.get("core.verify_ssl", True),
            ) as client:
                start_time = time.time()
                response = client.post(url, headers=headers, json=body)

                if response.status_code == 429:
                    if attempt < max_retries:
                        print(
                            f"⚠️  Rate limited (429). Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue

                response.raise_for_status()
                end_time = time.time()

                data = response.json()

                # Record usage
                usage = data.get("usage")
                usage_tracker.record_call(end_time - start_time, usage)

                if resp_type == "text":
                    choices = data.get("choices", [])
                    if not choices:
                        return "Error: No response from LLM provider."
                    content = (
                        choices[0]
                        .get("message", {})
                        .get("content", "Error: No content in LLM response.")
                    )
                    return clean_llm_response(content)
                return data

        except httpx.HTTPError as e:
            if attempt < max_retries:
                print(
                    f"⚠️  LLM call failed: {e}. Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2
                continue

            print(f"❌ Error calling LLM after {max_retries} retries: {e}")
            return {"Error": f"LLM Call Failed after retries: {e}"}
