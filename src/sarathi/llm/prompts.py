prompt_dict = {
    "autocommit": {
        "system_msg": """
                         Your task is to generate a commit message based on the diff provided. Please follow below guidelines while generating the commit message
                          - Think like a software developer
                          - Provide a high level description of changes
                          - Wrap lines at 72 characters
                          - In case of multiple lines add the character - in front of each line
                          - Provide High Level Description
                          - Use a maximum of 50 words
                          - Use standard English
                          - Try to be concise. Do not write multiple lines if not required
                          - If you think the diff fixes a comminbug, security issue or CVE which you know about, mention that in your response
                          - Do not repeat instructions in commit message
                        """,
        "model": "gpt-4o-mini",
    },
    "qahelper": {
        "system_msg": """
                         Your task is to answer the below question to the best of your knowledge. Please follow below guidelines
                          - Think like a principal software engineer who is assiting a junior developer
                          - Do not give any nasty comments or answers.
                          - If you do not know the answer do not make it up, just say 'sorry I do not know answer to that question'
                      """,
        "model": "gpt-4o-mini",
    },
    "update_docstrings": {
        "system_msg": """
                         Your task is to generate Google style docstrings format for the python code provided below. Please follow below guidelines while generating the docstring
                        -  docstrings should be generated in Google style docstrings format. An example is mentioned below
                                \"\"\"Reads the content of a file.

                                    Args:
                                        file_path: The path to the file to be read.

                                    Returns:
                                        The content of the file as a string.
                                \"\"\"
                        -  in your response only the docstrings should be send back, make sure not to send any code back in response
                        -  if you cannot determine the type of parameter or arguments, do not make up the type values in docstrings
                        -  do not mention any single quotes or double quotes in the response
                        -  if you do not know the answer do not make it up, just say sorry I do not know that
                    """,
        "model": "gpt-4o-mini",
    },
}
