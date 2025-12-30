import time
import requests

from sarathi.config.config_manager import config
from sarathi.utils.usage import usage_tracker


def get_agent_config(agent_name):
    """Retrieves the configuration for a specific agent."""
    if not agent_name:
        return {}

    # Map legacy prompt keys to new agent names if needed
    # (assuming prompt_info keys passed might be 'autocommit')
    if agent_name == "autocommit":
        agent_name = "commit_generator"

    return config.get_agent_config(agent_name)


def call_llm_model(prompt_info, user_msg, resp_type=None, agent_name=None):
    """
    Generate a response from the configured LLM.

    Args:
        prompt_info (dict): Legacy prompt dict containing system_msg and default model.
        user_msg (str): The user input.
        resp_type (str): 'text' to return just string, else json.
        agent_name (str): The name of the agent (e.g. 'commit_generator').
    """

    # 1. Determine Agent Config
    agent_conf = get_agent_config(agent_name)

    # 2. Determine Attributes (Config > Prompt Info Default)
    # Model
    model_name = agent_conf.get("model") or prompt_info.get("model") or "gpt-4o-mini"

    # Provider (e.g. openai, ollama)
    provider_name = agent_conf.get("provider", "openai")
    provider_conf = config.get_provider_config(provider_name)

    # System Prompt (Agent Config > Prompts Section > Prompt Info Legacy)
    system_msg = agent_conf.get("system_prompt")
    if not system_msg:
        system_msg = config.get(f"prompts.{agent_name}")
    if not system_msg:
        system_msg = prompt_info.get("system_msg", "")

    # 3. Construct URL and Headers
    base_url = provider_conf.get("base_url")
    if not base_url:
        raise ValueError(f"base_url not found in config for provider '{provider_name}'")

    # Handle OpenAI vs Ollama URL quirks
    # OpenAI usually expects /v1/chat/completions appended if base is just root
    # But usually config has full path or we standardizing on base_url being the root?
    # The config_manager default says: "https://api.openai.com/v1"
    # So we append "/chat/completions"
    url = f"{base_url.rstrip('/')}/chat/completions"

    api_key = provider_conf.get("api_key")

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    print(f"USING LLM : {provider_name} | Model: {model_name} | URL: {url}")

    # 4. Construct Body
    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        # TODO: Make these configurable too
        "max_tokens": 300,
        "n": 1,
        "temperature": agent_conf.get("temperature", 0.7),
    }

    response = None
    start_time = time.time()
    try:
        response = requests.post(
            url, headers=headers, json=body, timeout=config.get("core.timeout", 30)
        )
        response.raise_for_status()
        end_time = time.time()
        
        data = response.json()
        
        # Record usage
        usage = data.get("usage")
        usage_tracker.record_call(end_time - start_time, usage)

        if resp_type == "text":
            return data["choices"][0]["message"]["content"]
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM: {e}")
        if response is not None:
            # Try to print body if available, but it might not be text
            try:
                print(f"Response: {response.text}")
            except:
                pass
        return {"Error": f"LLM Call Failed: {e}"}
