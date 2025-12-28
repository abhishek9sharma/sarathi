# sarathi
A CLI coding assistant. It is targeted towards mundane tasks such as writing commit messages, generating docstrings etc.

## Installation
You can install the package using below command. Make sure you have Python and pip installed on your system.

        - pip install sarathi

## Quickstart

[![sarathi](https://img.youtube.com/vi/iBH_A6aZ4Qk/0.jpg)](https://youtu.be/iBH_A6aZ4Qk?si=_vJspgD5X33acR2i)

## Configuration

Sarathi uses a dual configuration system: **YAML files** for settings and **Environment Variables** for secrets (like API Keys).

### 1. Initialize Configuration
To create a local configuration file (`sarathi.yaml`) for your project:

```bash
sarathi config init
```

You can edit this file to change models, timeouts, or system prompts.

### 2. Set API Keys (Environment Variable Only)
For security, API keys **cannot** be stored in the config file. You must export them in your shell:

**For OpenAI:**
```bash
export OPENAI_API_KEY="sk-..."
```

**For Ollama (Local):**
```bash
# No API key needed usually, just set the endpoint in config or env
export OPENAI_ENDPOINT_URL="http://localhost:11434/v1/chat/completions"
# Or configure the provider in sarathi.yaml
```

**Legacy Environment Variables:**
The following variables are also supported for backward compatibility:
- `OPENAI_ENDPOINT_URL`
- `OPENAI_MODEL_NAME`


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

#### Ask Questions
You can ask general coding questions to the assistant:

- Run `sarathi ask -q "How do I reverse a list in Python?"`


## Helpul references
    - https://dev.to/taikedz/ive-parked-my-side-projects-3o62
    - https://github.com/lightningorb/autocommit
