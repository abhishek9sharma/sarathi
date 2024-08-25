# sarathi
A CLI coding assistant. It is targeted towards mundane tasks such as writing commit messages, generating docstrings etc.


## Installation
You can install the package using below command. Make sure you have Python and pip installed on your system.

        - pip install sarathi


## Quickstart

[![sarathi](https://img.youtube.com/vi/iBH_A6aZ4Qk/0.jpg)](https://youtu.be/iBH_A6aZ4Qk?si=_vJspgD5X33acR2i)




## Setting some Environment Variables

-  To use this package, you need to set up some environment variables. The steps are mentioned below. 

    - The default setting of the package is to use [OpenAI](https://openai.com/) services which requires an API key. To get the key, you need to sign up for an account on the [OpenAI website](https://openai.com/product). Once you have your API key, you can set it in your environment variables as mentioned below
       
            export OPENAI_API_KEY=keyvalue

    - In case you do not want to use [OpenAI](https://openai.com/) services, this package should work with any endpoint which accepts requests in OpenAI schema format. For example you can use it local LLM model endpoints like [Ollama](https://ollama.com/) by setting below environment variables
            
            export OPENAI_API_KEY=ollama
            export OPENAI_ENDPOINT_URL=http://localhost:11434/v1/chat/completions
            export OPENAI_MODEL_NAME=codellama:7b


 

 


## Usage

#### Generating Git Commit Messages
Sarathi provides a convenient commands to generate commit messages for git commits locally. Below are the steps you want to follow
- Stage the files you want to commit
- Run `sarathi git autocommit`.
    - this command will automatically analyze your staged changes
    - generate a commit message via OPEN AI, show the generated message to you,
    - if you confirm, will commit your changes to the repository with the generated message.

- Run `sarathi git gencommit`.
    - this command will automatically analyze your staged changes,
    - generate a commit message via OPEN AI, and commit the changes automatically.
    - It will then run `git commit --amend` for you to edit the generated commit message.

#### Generating docstring messages
You can generate docstrings for your python code using commands such as below

- Run `sarathi docstrgen -f src/sarathi/code/codetasks.py`. This command analyzes the methods in the file provided in the argument, and generates docstrings for functions.
- Run `sarathi docstrgen -d src/sarathi/`. This command analyzes the methods in all files present in the directory provided in the argument,  and generates docstrings for function.


## Helpul references
    - https://dev.to/taikedz/ive-parked-my-side-projects-3o62
    - https://github.com/lightningorb/autocommit
