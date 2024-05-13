# sarathi
A CLI coding assistant


## Installation
You can install the package using below command. Make sure you have Python and pip installed on your system.
    
        - pip install sarathi
 
## Setting OpenAI API Key
To use certain features of this package, you need to set up your OpenAI API key. If you don't have one, you can sign up for an account on the [OpenAI website](https://openai.com/product). Once you have your API key, you can set it in your environment variables. Here's how you can do it:

### For Linux/macOS:

    - export OPENAI_API_KEY=YOUR_API_KEY


## Usage

#### Generating Git Commit Messages
Sarathi provides a convenient command `sarathi git autocommit` to generate commit messages for Git commits. 
- Stage the files you want to commit
- Run `sarathi git autocommit`. This command will automatically analyze your staged changes, generate a commit message via OPEN AI, show the generated message to you, and if you confirm, will commit your changes to the repository with the generated message.

#### Generating docstring messages
You can generate docstrings for your python code using commands such as below

- Run `sarathi docstrgen -f src/sarathi/code/codetasks.py`. This command analyzes the methods in the file provided in the argument, and generates docstrings for functions.
- Run `sarathi docstrgen -d src/sarathi/`. This command analyzes the methods in all files present in the directory provided in the argument,  and generates docstrings for function.


## Helpul references
    - https://dev.to/taikedz/ive-parked-my-side-projects-3o62
    - https://github.com/lightningorb/autocommit
    