# sarathi
A CLI coding assistant. It is targeted towards mundane tasks such as writing commit messages, generating docstrings etc.

## Installation
You can install the package using below command. Make sure you have Python and pip installed on your system.

        - pip install sarathi

## Quickstart

[![sarathi]](https://github.com/user-attachments/assets/f1581b80-ec10-4c1c-b4b7-60e90eaa3f37)

## Configuration

Sarathi uses a dual configuration system: **YAML files** for settings and **Environment Variables** for secrets (like API Keys).

### 1. Initialize Configuration
To create your global configuration file:

```bash
sarathi config init
```
This creates settings in `~/.sarathi/config.yaml`. This is the single source of truth for your preferences across all projects.

If you want to initialize a config at a specific path:
```bash
sarathi config init --path ./my-config.yaml
```

### 2. Using a Custom Configuration
By default, Sarathi always looks at `~/.sarathi/config.yaml`. If you want to use a specific configuration file for a particular project or session, use the global `--config` (or `-c`) flag:

```bash
sarathi --config ./project-config.yaml git autocommit
```

### 3. Configuration Hierarchy
Sarathi resolves configuration in the following order (lower items override higher ones):
1. **Defaults**: Built-in settings.
2. **Global Config**: `~/.sarathi/config.yaml` (or the file specified via `--config`).
3. **Environment Variables**: For secrets and quick overrides (e.g., `OPENAI_API_KEY`).

### 4. Update Configuration from CLI
You can update configuration values directly from the terminal. This will persist settings to your active configuration file (local `sarathi.yaml` or global `~/.sarathi/config.yaml`).

```bash
sarathi config set core.verify_ssl False
sarathi config set core.timeout 60
```

To update a value without saving it to the config file (current session only):
```bash
sarathi config set core.timeout 10 --no-save
```

### 5. Air-Gapped / Private Environments
If you are running Sarathi in an environment with private LLM endpoints (like a local Ollama or corporate proxy) that uses self-signed certificates, you can disable SSL verification:

```bash
sarathi config set core.verify_ssl False
```

### 6. Set API Keys (Environment Variable Only)
For security, API keys **cannot** be stored in the config file. You must export them in your shell:

**For OpenAI:**
```bash
export OPENAI_API_KEY="sk-..."
```

**For Ollama (Local):**
```bash
# No API key needed usually, just set the endpoint in config or env
export OPENAI_ENDPOINT_URL="http://localhost:11434/v1/chat/completions"
# Or configure the provider in sarathi.yaml/global config
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

- Run `sarathi chat -q "How do I reverse a list in Python?"`

#### Interactive Chat Mode
Start a persistent, interactive session where the assistant can help you edit code, run tests, and answer complex queries.

- Run `sarathi chat`

Inside the chat, you can use **Slash Commands**:
- `/exit`: Quit the session
- `/clear`: Reset conversation context
- `/model <name>`: Switch the LLM model for the current session
- `/reindex`: Refresh the project file index for `@filename` completions

#### Model Switching
Quickly change or view the LLM model used by Sarathi:

- View current models: `sarathi model`
- Change globally for all agents: `sarathi model gpt-4o`
- Change for a specific agent: `sarathi model claude-3-5-sonnet --agent code_editor`
- Temporary change (no save): `sarathi model llama3 --no-save`

#### SBOM (Software Bill of Materials) Tools
Audit your project's dependencies, licenses, and full dependency trees with a **beautiful Rich terminal UI**:

- **Library Mapping**: `sarathi sbom imports` (See which file imports which external library)
- **Dependency Graph**: `sarathi sbom depgraph` (Full visual tree of installed dependencies)
- **Integrity Check**: `sarathi sbom check` (Detect unused bloat or undeclared dependencies)
- **Specific Package**: `sarathi sbom depgraph -p requests`
- **JSON Export**: `sarathi sbom imports --json`

> **Tip**: Inside `sarathi chat`, you can ask "Who depends on aiohttp?" or "Check for unused dependencies" and the assistant will use these tools to audit your project.


## Recent Changes
- **Interactive Chat Mode**: Added a powerful `sarathi chat` mode with tool support, project indexing, and slash commands.
- **SBOM Tools**: New `sarathi sbom` suite for auditing imports, licenses, and full dependency graphs.
- **Dynamic Configuration**: New `sarathi config set` command to update settings from CLI.
- **Model Switching**: Added `sarathi model` command and `/model` chat command to switch LLMs on the fly.
- **Unified Interface**: Merged `ask` into `chat` for a simpler command structure.
- **Air-Gapped Support**: Added `core.verify_ssl` toggle to support environments with private/self-signed certificates.
- **Persistence**: Configuration updates are now preserved with proper YAML formatting.

## Helpful references
    - https://dev.to/taikedz/ive-parked-my-side-projects-3o62
    - https://github.com/lightningorb/autocommit
