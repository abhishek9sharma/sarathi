import os
import requests


def retrieve_api_key():
    """Retrieves the OpenAI API key from environment variables.

    This function attempts to retrieve the API key from two possible environment variables:
    SARATHI_OPENAI_API_KEY and OPENAI_API_KEY. If neither variable is set, it raises
    a ValueError.

    Returns:
        The OpenAI API key as a string.

    Raises:
        ValueError: If neither environment variable is found.
    """
    try:
        return os.environ["SARATHI_OPENAI_API_KEY"]
    except Exception as e:
        try:
            return os.environ["OPENAI_API_KEY"]
        except Exception as e:
            raise ValueError(
                "Exception occured: neither SARATHI_OPENAI_API_KEY nor OPENAI_API_KEY is found"
            )


def call_llm_model(prompt_info, user_msg, resp_type=None):
    """
    Generate a response from the OpenAI language model based on the given prompt and user message.

    Args:
        prompt_info (dict): A dictionary containing information about the prompt, including the model and system message.
        user_msg (str): The user message to be used as input for the language model.
        resp_type (str, optional): The type of response expected. Defaults to None.

    Returns:
    """
    url = "https://api.openai.com/v1/chat/completions"
    model = prompt_info["model"]
    system_msg = prompt_info["system_msg"]
    headers = {
        "Authorization": "Bearer " + retrieve_api_key(),
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
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
