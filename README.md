# sarathi
A CLI coding assistant


## Installation
You can install the package from the GitHub repository using pip. Make sure you have Python and pip installed on your system.
    
        - pip install sarathi
        - pip install https://github.com/abhishek9sharma/sarathi.git

## Setting OpenAI API Key
To use certain features of this package, you need to set up your OpenAI API key. If you don't have one, you can sign up for an account on the [OpenAI website](https://openai.com/product). Once you have your API key, you can set it in your environment variables. Here's how you can do it:

### For Linux/macOS:

    - export OPENAI_API_KEY=YOUR_API_KEY


## Usage

#### Generating Git Commit Messages
Sarathi provides a convenient command `sarathi git autocommit` to generate commit messages for Git commits. 
- Stage the files you want to commit
- Run `sarathi git autocommit`. This command will automatically analyze your staged changes (using git add .), generate a commit message, and if you confirm will commit your changes to the repository with the generate message

#### Generating docstring messages
You can generate docstrings for your python code using the below commands.

- Run `sarathi docstrgen -f /scratchpad/ghmount/sarathi/src/sarathi/utils/formatters.py`. This command analyze the methods in the file passed and generates docstrings for functions if they do not exist.
- Run `sarathi docstrgen -d /scratchpad/ghmount/sarathi/src/sarathi/`. This command analyzes the methods in all files presend in the directory specified and generates docstrings for functions if they do not exist.


## Helpul references
    - https://dev.to/taikedz/ive-parked-my-side-projects-3o62
    - https://github.com/lightningorb/autocommit
    