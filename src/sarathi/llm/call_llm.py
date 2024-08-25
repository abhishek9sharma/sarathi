import os

import requests


def get_env_var(var_names, default=None, error_msg=None):
    """Generic function to retrieve environment variables."""

    for name in var_names:
        if name in os.environ:
            return os.environ[name]
    if default is not None:
        return default
    raise ValueError(error_msg or f"Environment variable(s) not found: {var_names}")


def retrieve_api_key():
    """
    Retrieve the OpenAI API key from environment variables.

    Returns:
        str: The OpenAI API key.

    Raises:
        ValueError: If neither SARATHI_OPENAI_API_KEY nor OPENAI_API_KEY is found.
    """

    return get_env_var(
        ["SARATHI_OPENAI_API_KEY", "OPENAI_API_KEY"],
        error_msg="Neither SARATHI_OPENAI_API_KEY nor OPENAI_API_KEY is found",
    )


def retrieve_llm_url():
    """
    Retrieve the OpenAI API endpoint URL from environment variables.

    Returns:
        str: The OpenAI API endpoint URL. Defaults to 'https://api.openai.com/v1/chat/completions'
             if OPENAI_ENDPOINT_URL is not set.
    """

    return get_env_var(
        ["OPENAI_ENDPOINT_URL"], default="https://api.openai.com/v1/chat/completions"
    )


def retrieve_model_name(prompt_info):
    """
    Retrieve the OpenAI model name from environment variables.
        prompt_info (dict): A dictionary containing information about the prompt, including the model and system message.

    Returns:
        str: The OpenAI model name. Defaults to 'gpt-4o-mini' if OPENAI_MODEL_NAME is not set.
        dict: updated prompt_info
    """
    model_name = get_env_var(
        ["OPENAI_MODEL_NAME"],
        default=(prompt_info["model"] if prompt_info["model"] else "gpt-4o-mini"),
    )
    if prompt_info["model"] != model_name:
        prompt_info["model"] = model_name
    return model_name


def call_llm_model(prompt_info, user_msg, resp_type=None):
    """
    Generate a response from the OpenAI language model based on the given prompt and user message.

    Args:
        prompt_info (dict): A dictionary containing information about the prompt, including the model and system message.
        user_msg (str): The user message to be used as input for the language model.
        resp_type (str, optional): The type of response expected. Defaults to None.

    Returns:
    """

    url = retrieve_llm_url()
    model_name = retrieve_model_name(prompt_info)
    print(f"USING LLM : {url} and model :{model_name}")
    system_msg = prompt_info["system_msg"]
    headers = {
        "Authorization": "Bearer " + retrieve_api_key(),
        "Content-Type": "application/json",
    }
    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 100,
        "n": 1,
        "stop": None,
        "temperature": 0.7,
    }
    response = requests.post(url, headers=headers, json=body)
    if resp_type == "text":
        text_resp = response.json()["choices"][0]["message"]["content"]
        return text_resp
    return response.json()
