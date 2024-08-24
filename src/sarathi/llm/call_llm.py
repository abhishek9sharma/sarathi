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

def retrieve_llm_url():
    """Retrieves the LLM endpoint that is to be called

    This function attempts to retrieve the API key from the end point OPEN_API_ENDPOINT_URL if specified

    Returns:
        The OPEN_API_ENDPOINT_URL 

    Raises:
        ValueError: If neither environment variable is found.
    """
    try:
        return os.environ["OPENAI_ENDPOINT_URL"]
    except Exception as e:
        try:
            default_OPENAI_ENDPOINT_URL = "https://api.openai.com/v1/chat/completions"
            print(f"OPENAI_ENDPOINT_URL env var not found using default URL : {default_OPENAI_ENDPOINT_URL} ")
            return default_OPENAI_ENDPOINT_URL
        except Exception as e:
            raise ValueError(
                "Exception occured: OPEN_API_ENDPOINT_URL  not found"
            )

def retrieve_model_name():
    """Retrieves the LLM model name to be used

    This function attempts to retrieve the model name from the environment variable OPENAI_MODEL_NAME.
    If not found, it uses a default model name.

    Returns:
        The OpenAI model name as a string.
    """
    try:
        return os.environ["OPENAI_MODEL_NAME"]
    except KeyError:
        default_model_name = "gpt-3.5-turbo"
        print(f"OPENAI_MODEL_NAME env var not found, using default model: {default_model_name}")
        return default_model_name


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
    model = retrieve_model_name()
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
    print(response.text)
    if resp_type == "text":
        text_resp = response.json()["choices"][0]["message"]["content"]
        return text_resp
    return response.json()