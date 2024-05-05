import os

import requests


def call_llm_model(prompt_info, user_msg):
    try:
        url = "https://api.openai.com/v1/chat/completions"
        # url = "https://api.openai.com/v1/engines/davinci-codex/completions"
        model = prompt_info["model"]
        system_msg = prompt_info["system_msg"]
        headers = {
            "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
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
        # print(response)
        return response.json()
    except Exception as e:
        if str(e) == "'OPENAI_API_KEY'":
            return {"Error": "Exception occured " + str(e) + " not found"}

        return {"Error": "Exception occured " + str(e) + " occured"}
